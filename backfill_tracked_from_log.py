#!/usr/bin/env python3
"""
Backfill the tracked_songs table (side-project songs such as "Toto - Africa") from radio.log.
Dry run by default; nothing is written without --commit.

Usage (run from the radiochecker directory, next to radio_songs.db and radio.log):
    python3 backfill_tracked_from_log.py                  # dry run, whole log
    python3 backfill_tracked_from_log.py --since 2026-08-19
    python3 backfill_tracked_from_log.py --commit         # insert into tracked_songs

Which songs to look for comes from the 'tracked_songs' setting in the database (the same
list the live detector uses); pass --entry "Toto - Africa" (repeatable) to override it.

Dates: lines written since the date prefix was added carry their own date. Older lines only
have [HH:MM], so they are dated by anchoring to detections already in the songs table
(see backfill_from_log.py). A line is only used if the anchors on both sides agree on its
date; the others are listed as uncertain and skipped.
"""

import argparse
import json
import os
import re
from datetime import datetime, time, timedelta

import db_connection as db
from backfill_from_log import day_offsets, find_anchors, load_db_rows, make_dater
from find_log_detections import parse_line

DEDUPE_WINDOW = timedelta(minutes=10)  # a song lasts ~5 min; a replay on one station within 10 is the same play


def title_case(text):
    """Same casing as main.py's normalize_song_title"""
    text = re.sub(r'^#\d+:\s*', '', text).strip()
    words = []
    for word in text.split():
        if "'" in word:
            parts = word.split("'")
            word = parts[0].capitalize() + "'" + "'".join(p.lower() for p in parts[1:])
        else:
            word = word.capitalize()
        words.append(word)
    return ' '.join(words)


def parse_entry(entry):
    """'Toto - Africa' -> ('toto', 'africa'); a plain 'Africa' -> (None, 'africa') matches any artist"""
    if ' - ' in entry:
        artist, title = entry.split(' - ', 1)
        return artist.strip().lower(), title.strip().lower()
    return None, entry.strip().lower()


def resolve(entries, artist, song):
    """(artist, song) in the right order if the pair matches an entry in either order, else None.
    Either order because some stations (JOE) used to report 'title - artist'."""
    for entry in entries:
        t_artist, t_title = parse_entry(entry)
        for a, s in ((artist, song), (song, artist)):
            if t_title and t_title in s.lower() and (t_artist is None or t_artist == a.lower()):
                return title_case(a), title_case(s)
    return None


def load_entries(c, db_type):
    db.execute_query(c, "SELECT value FROM settings WHERE key = ?", ('tracked_songs',), db_type)
    row = c.fetchone()
    return [e for e in json.loads(row[0]) if e] if row else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('logfile', nargs='?', default='radio.log')
    ap.add_argument('--since', help='first date to backfill, YYYY-MM-DD (default: whole log)')
    ap.add_argument('--entry', action='append', help="tracked song, e.g. 'Toto - Africa' (default: the tracked_songs setting)")
    ap.add_argument('--commit', action='store_true', help='actually insert (default is a dry run)')
    args = ap.parse_args()

    since = datetime.strptime(args.since, '%Y-%m-%d').date() if args.since else None
    end_date = datetime.fromtimestamp(os.path.getmtime(args.logfile)).date()

    conn, db_type, db_rows = load_db_rows()
    c = conn.cursor()
    entries = args.entry or load_entries(c, db_type)
    if not entries:
        print("No tracked songs configured (the 'tracked_songs' setting is empty). Pass --entry 'Artist - Title'.")
        return
    print(f"Looking for: {', '.join(entries)}")

    with open(args.logfile, encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]

    offsets = day_offsets(lines)
    if not any(o is not None for o in offsets):
        print("No timed lines in the log.")
        return
    parsed, explicit = {}, {}
    for i, line in enumerate(lines):
        p = parse_line(line)
        if p:
            parsed[i] = (p[1], p[2], p[3], p[4])  # hm, station, artist, song
            if p[0]:
                explicit[i] = datetime.strptime(p[0], '%Y-%m-%d').date()
    span = max(o for o in offsets if o is not None)

    anchors = find_anchors(parsed, offsets, db_rows, end_date - timedelta(days=span + 1), end_date + timedelta(days=1))
    print(f"{len(lines)} log lines spanning ~{span + 1} days; {len(explicit)} carry their own date, {len(anchors)} date anchors from the database")
    date_for = make_dater(anchors, offsets)
    for (ai, ad), (bi, bd) in zip(anchors, anchors[1:]):
        expected = ad + timedelta(days=offsets[bi] - offsets[ai])
        if expected != bd:
            print(f"  Date drift of {(bd - expected).days:+d} day(s) between log lines {ai + 1} ({ad}) and {bi + 1} ({bd})")

    candidates, uncertain, already_tracked_lines = [], [], 0
    for i, (hm, station, artist, song) in parsed.items():
        match = resolve(entries, artist, song)
        if not match:
            continue
        if '(tracked' in lines[i]:
            already_tracked_lines += 1  # written by the live detector, so already in the table
            continue
        if i in explicit:
            date, confident = explicit[i], True
        else:
            date, confident = date_for(i)
        if date is None or (since and date < since):
            continue
        if not confident:
            uncertain.append((i, station, match, hm))
            continue
        candidates.append((datetime.combine(date, time(int(hm[:2]), int(hm[3:]))), station, match[0], match[1]))

    try:
        db.execute_query(c, "SELECT station, artist, song, timestamp FROM tracked_songs", db_type=db_type)
        existing = [(st, a.lower(), s.lower(), datetime.fromisoformat(ts)) for st, a, s, ts in c.fetchall()]
    except Exception:
        existing = []  # table not created yet (the service creates it on restart)

    found, log_duplicates, db_duplicates = [], 0, 0
    last_seen = {}
    for ts, station, artist, song in sorted(candidates, key=lambda x: (x[1], x[2], x[3], x[0])):
        key = (station, artist.lower(), song.lower())
        if key in last_seen and ts - last_seen[key] <= DEDUPE_WINDOW:
            log_duplicates += 1  # same play logged twice, e.g. after a restart or a source flip
            last_seen[key] = ts
            continue
        last_seen[key] = ts
        if any(st == station and a == artist.lower() and s == song.lower() and abs(ts - t) <= DEDUPE_WINDOW
               for st, a, s, t in existing):
            db_duplicates += 1
            continue
        found.append((ts, station, artist, song))
    found.sort()

    for ts, station, artist, song in found:
        print(f"{ts:%Y-%m-%d %H:%M}  {station:<22} {artist} - {song}")
    print(f"\n{len(found)} to insert | {log_duplicates} duplicate log lines collapsed | {db_duplicates} already in tracked_songs"
          f" | {already_tracked_lines} lines written by the live detector | {len(uncertain)} skipped as uncertain date")
    for i, station, match, hm in uncertain:
        print(f"  uncertain: log line {i + 1}  [{hm}] {station}: {match[0]} - {match[1]}")

    if not args.commit:
        print("Dry run - rerun with --commit to insert.")
        return
    db.init_database()  # makes sure tracked_songs exists
    for ts, station, artist, song in found:
        db.execute_query(c, "INSERT INTO tracked_songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                         (station, song, artist, ts.isoformat()), db_type)
    conn.commit()
    conn.close()
    print(f"Inserted {len(found)} rows. Run upload_db.py to push them to the web server.")


if __name__ == '__main__':
    main()
