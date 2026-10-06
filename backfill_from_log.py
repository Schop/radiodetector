#!/usr/bin/env python3
"""
Backfill missed Phil Collins / Genesis detections for one station (default JOE) from radio.log.
Dry run by default; nothing is written without --commit.

Usage (run from the radiochecker directory, next to radio_songs.db):
    python backfill_from_log.py 2026-07-23                 # dry run
    python backfill_from_log.py 2026-07-23 --commit        # insert into the database

radio.log under systemd has only [HH:MM] per line, no date. Dates are recovered by
anchoring to detections that are already in the database: a log line for another
station with the same song at the same time (+/- 2 min) as a database row gets that
row's real date. Other lines are dated relative to the nearest anchors. A line is only
used if the anchors before and after it agree on its date; otherwise it is reported
as uncertain and skipped.
"""

import argparse
import bisect
import os
from collections import defaultdict
from datetime import datetime, time, timedelta

import db_connection as db
from find_log_detections import ANY_TIME, parse_line

DEDUPE_WINDOW = timedelta(minutes=10)


def minutes_of(hm):
    return int(hm[:2]) * 60 + int(hm[3:])


def day_offsets(lines):
    """Days elapsed since the first timed line, per line (None for lines without a time)"""
    offsets = [None] * len(lines)
    day, prev = 0, None
    for i, line in enumerate(lines):
        m = ANY_TIME.match(line)
        if not m:
            continue
        mins = minutes_of(m.group(2))
        if prev is not None and mins < prev - 60:  # clock went backwards: midnight passed
            day += 1
        prev = mins
        offsets[i] = day
    return offsets


def load_db_rows():
    conn, db_type = db.get_connection()
    c = conn.cursor()
    db.execute_query(c, "SELECT station, song, artist, timestamp FROM songs", db_type=db_type)
    rows = []
    for station, song, artist, ts in c.fetchall():
        try:
            rows.append((station, song, artist, datetime.fromisoformat(ts)))
        except (TypeError, ValueError):
            continue
    return conn, db_type, rows


def find_anchors(parsed, offsets, db_rows, lo, hi):
    """[(line_index, real_date)] for DB rows that match exactly one log line"""
    index = defaultdict(list)
    for i, (hm, station, artist, song) in parsed.items():
        index[(station.lower(), song.lower())].append(i)

    anchors = {}
    for station, song, _, ts in db_rows:
        if station == 'JOE' or not (lo <= ts.date() <= hi):
            continue
        db_min = ts.hour * 60 + ts.minute
        hits = []
        for i in index.get((station.lower(), song.lower()), []):
            diff = abs(minutes_of(parsed[i][0]) - db_min)
            if min(diff, 1440 - diff) <= 2:
                hits.append(i)
        if len(hits) != 1:
            continue  # no match, or ambiguous (same song/time on several days)
        i = hits[0]
        hm = parsed[i][0]
        log_time = time(int(hm[:2]), int(hm[3:]))
        best = min((ts.date() + timedelta(days=k) for k in (-1, 0, 1)),
                   key=lambda d: abs(datetime.combine(d, log_time) - ts))
        anchors[i] = best
    return sorted(anchors.items())


def make_dater(anchors, offsets):
    """Return date_for(i) -> (date or None, confident bool)"""
    idxs = [a[0] for a in anchors]

    def date_for(i):
        k = bisect.bisect_right(idxs, i)
        preds = []
        if k > 0:
            ai, ad = anchors[k - 1]
            preds.append(ad + timedelta(days=offsets[i] - offsets[ai]))
        if k < len(anchors):
            bi, bd = anchors[k]
            preds.append(bd - timedelta(days=offsets[bi] - offsets[i]))
        if not preds:
            return None, False
        return preds[0], len(set(preds)) == 1

    return date_for


def normalize_target(field_artist, field_song):
    """Pick artist/song out of a possibly swapped pair; None if neither field is a target"""
    for artist, song in ((field_artist, field_song), (field_song, field_artist)):
        low = artist.lower()
        if 'phil collins' in low:
            return ('Phil Collins & Philip Bailey' if 'bailey' in low else 'Phil Collins'), song
        if low == 'genesis':
            return 'Genesis', song
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('since', help='first date to backfill, YYYY-MM-DD')
    ap.add_argument('logfile', nargs='?', default='radio.log')
    ap.add_argument('--station', default='JOE')
    ap.add_argument('--commit', action='store_true', help='actually insert (default is a dry run)')
    args = ap.parse_args()

    since = datetime.strptime(args.since, '%Y-%m-%d').date()
    end_date = datetime.fromtimestamp(os.path.getmtime(args.logfile)).date()

    with open(args.logfile, encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]

    offsets = day_offsets(lines)
    parsed = {}
    for i, line in enumerate(lines):
        p = parse_line(line)
        if p:
            parsed[i] = (p[1], p[2], p[3], p[4])  # hm, station, artist, song
    span = max(o for o in offsets if o is not None)

    conn, db_type, db_rows = load_db_rows()
    anchors = find_anchors(parsed, offsets, db_rows, end_date - timedelta(days=span + 1), end_date + timedelta(days=1))
    print(f"{len(lines)} log lines spanning ~{span + 1} days, {len(anchors)} date anchors from the database")
    if not anchors:
        print("No anchors found - cannot date the log lines. Is this the right database/log?")
        return

    date_for = make_dater(anchors, offsets)
    first_i = next(i for i, o in enumerate(offsets) if o is not None)
    first_date, _ = date_for(first_i)
    print(f"Log starts around {first_date} and ends {end_date}")

    # Drift between consecutive anchors = a stretch where the clock-based day count is unreliable
    drifts = 0
    for (ai, ad), (bi, bd) in zip(anchors, anchors[1:]):
        expected = ad + timedelta(days=offsets[bi] - offsets[ai])
        if expected != bd:
            drifts += 1
            print(f"  Date drift of {(bd - expected).days:+d} day(s) between log lines {ai + 1} ({ad}) and {bi + 1} ({bd})")
    if not drifts:
        print("Anchors are consistent with each other (no missing days detected)")

    existing = [(s.lower(), ts) for st, s, _, ts in db_rows if st == args.station]

    found, uncertain, duplicates = [], 0, 0
    for i, (hm, station, artist, song) in parsed.items():
        if station != args.station:
            continue
        target = normalize_target(artist, song)
        if not target:
            continue
        date, confident = date_for(i)
        if date is None or date < since:
            continue
        if not confident:
            uncertain += 1
            continue
        new_artist, new_song = target
        ts = datetime.combine(date, time(int(hm[:2]), int(hm[3:])))
        if any(s == new_song.lower() and abs(ts - t) <= DEDUPE_WINDOW for s, t in existing):
            duplicates += 1
            continue
        found.append((ts, new_artist, new_song))

    for ts, artist, song in found:
        print(f"{ts:%Y-%m-%d %H:%M}  {args.station:<10} {artist} - {song}")
    print(f"\n{len(found)} to insert, {duplicates} already in database, {uncertain} skipped as uncertain date")

    if not args.commit:
        print("Dry run - rerun with --commit to insert.")
        return
    c = conn.cursor()
    for ts, artist, song in found:
        db.execute_query(c, "INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                         (args.station, song, artist, ts.isoformat()), db_type)
    conn.commit()
    conn.close()
    print(f"Inserted {len(found)} rows. Run upload_db.py to push them to the web server.")


if __name__ == '__main__':
    main()
