#!/usr/bin/env python3
"""
Backfill missed Phil Collins / Genesis detections on Arrow Classic Rock from arrow.nl's own
playlist API (https://www.arrow.nl/api/playlist). Dry run by default; nothing is written
without --commit.

The API only keeps about a week of history (days 0-6 complete, day 7 partial), so run this
soon after an outage.

Usage (run from the radiochecker directory, next to radio_songs.db):
    python backfill_arrow.py                 # dry run, last 8 days
    python backfill_arrow.py --days 3        # only the last 3 days
    python backfill_arrow.py --commit        # insert into the database
"""

import argparse
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

import db_connection as db

STATION = 'Arrow Classic Rock'
API = 'https://www.arrow.nl/api/playlist'
TZ = ZoneInfo('Europe/Amsterdam')
DEDUPE_WINDOW = timedelta(minutes=10)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def normalize_song_title(title):
    """Same normalisation as main.py: strip '#742: ' prefixes and title-case"""
    normalized = re.sub(r'^#\d+:\s*', '', title).strip()
    words = []
    for word in normalized.split():
        if "'" in word:
            parts = word.split("'")
            word = parts[0].capitalize() + "'" + "'".join(p.lower() for p in parts[1:])
        else:
            word = word.capitalize()
        words.append(word)
    return ' '.join(words)


def load_target_songs(c, db_type):
    try:
        db.execute_query(c, "SELECT value FROM settings WHERE key = ?", ('target_songs',), db_type)
        row = c.fetchone()
        return [s for s in json.loads(row[0]) if s] if row else []
    except Exception:
        return []


def match_target(artist, song, target_songs):
    """Return the normalised (artist, song) if it is a target, else None (same rules as main.py)"""
    n_artist = normalize_song_title(artist)
    n_song = normalize_song_title(song)
    if 'phil collins' in n_artist.lower():
        return ('Phil Collins & Philip Bailey' if 'bailey' in n_artist.lower() else 'Phil Collins'), n_song
    if n_artist.lower() == 'genesis':
        return 'Genesis', n_song
    if any(t.lower() in n_song.lower() for t in target_songs):
        return n_artist, n_song
    return None


def fetch_tracks(days):
    """All tracks for day offsets 0..days-1, every hour; de-duplicated on timestamp"""
    session = requests.Session()
    session.headers.update(HEADERS)
    tracks = {}
    for day in range(days):
        count = 0
        for hour in range(24):
            try:
                r = session.get(API, params={'day': day, 'hour': hour}, timeout=15)
                r.raise_for_status()
                for t in r.json().get('tracks', []):
                    tracks[(t['timestamp'], t['artist'], t['title'])] = t
                    count += 1
            except Exception as e:
                print(f"  day {day} hour {hour}: {e}")
        print(f"  day {day}: {count} tracks")
    return list(tracks.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--days', type=int, default=8, help='how many days back to fetch (default 8; API keeps ~7)')
    ap.add_argument('--commit', action='store_true', help='actually insert (default is a dry run)')
    args = ap.parse_args()

    conn, db_type = db.get_connection()
    c = conn.cursor()
    target_songs = load_target_songs(c, db_type)

    print(f"Fetching Arrow playlist for the last {args.days} days...")
    tracks = fetch_tracks(args.days)
    if not tracks:
        print("No tracks returned - nothing to do.")
        return
    first = min(t['timestamp'] for t in tracks)
    print(f"{len(tracks)} tracks, oldest {datetime.fromtimestamp(first, TZ):%Y-%m-%d %H:%M}")

    db.execute_query(c, "SELECT song, timestamp FROM songs WHERE station = ?", (STATION,), db_type)
    existing = []
    for song, ts in c.fetchall():
        try:
            existing.append((song.lower(), datetime.fromisoformat(ts)))
        except (AttributeError, TypeError, ValueError):
            continue

    found, duplicates = [], 0
    for t in sorted(tracks, key=lambda t: t['timestamp']):
        target = match_target(t['artist'], t['title'], target_songs)
        if not target:
            continue
        artist, song = target
        # Stored timestamps are naive local (Amsterdam) time, like the live detector writes them
        ts = datetime.fromtimestamp(t['timestamp'], TZ).replace(tzinfo=None, microsecond=0)
        if any(s == song.lower() and abs(ts - e) <= DEDUPE_WINDOW for s, e in existing):
            duplicates += 1
            continue
        found.append((ts, artist, song))

    for ts, artist, song in found:
        print(f"{ts:%Y-%m-%d %H:%M}  {STATION}  {artist} - {song}")
    print(f"\n{len(found)} to insert, {duplicates} already in database")

    if not args.commit:
        print("Dry run - rerun with --commit to insert.")
        return
    for ts, artist, song in found:
        db.execute_query(c, "INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                         (STATION, song, artist, ts.isoformat()), db_type)
    conn.commit()
    conn.close()
    print(f"Inserted {len(found)} rows. Run upload_db.py to push them to the web server.")


if __name__ == '__main__':
    main()
