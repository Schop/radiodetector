#!/usr/bin/env python3
"""
Find (and optionally delete) duplicate plays: the same song on the same station logged again within
a few minutes. These come from a restart while a song was playing, or from a source flip (an
aggregator site re-reporting the previous song). main.py no longer logs them; this cleans up old ones.

Dry run by default; nothing is deleted without --commit. With --commit a backup copy of the SQLite
file is made first (radio_songs.db.before_dedupe_<timestamp>).

Usage (run next to radio_songs.db):
    python3 remove_duplicate_plays.py                          # dry run, songs and tracked_songs
    python3 remove_duplicate_plays.py --station "Arrow Classic Rock"
    python3 remove_duplicate_plays.py --window 15              # minutes (default 10)
    python3 remove_duplicate_plays.py --table songs
    python3 remove_duplicate_plays.py --commit                 # delete the listed rows

Per station and song, plays are sorted by time and a play within --window minutes of the previous
play (kept or not) is a duplicate, so a run of repeats keeps only its first play. Artist and title
are compared ignoring case and punctuation, like main.py does.

A repeat further from the first play than the window is not found. A stale song that came back
11 minutes after the real play, for example, needs a larger --window or a manual
DELETE FROM songs WHERE id = ...; (the dry run prints the ids).
Run upload_db.py afterwards to push the cleaned database to the web server.
"""

import argparse
import re
import shutil
import sqlite3
from datetime import datetime, timedelta

import db_connection as db

TABLES = ('songs', 'tracked_songs')


def fold_text(text):
    """Same as main.py's fold_text: lowercase, punctuation ignored"""
    text = re.sub(r"['‘’`]", '', (text or '').lower())
    return ' '.join(re.sub(r'[\W_]+', ' ', text).split())


def find_duplicates(c, db_type, table, window, station=None):
    """[(id, station, artist, song, timestamp, minutes_after_previous)] of the duplicate plays"""
    query = f"SELECT id, station, artist, song, timestamp FROM {table}"
    params = ()
    if station:
        query += " WHERE station = ?"
        params = (station,)
    db.execute_query(c, query, params, db_type)

    groups = {}
    for row_id, st, artist, song, ts in c.fetchall():
        try:
            when = datetime.fromisoformat(ts)
        except (TypeError, ValueError):
            continue
        groups.setdefault((st, fold_text(artist), fold_text(song)), []).append((when, row_id, artist, song, ts))

    duplicates = []
    for (st, _, _), plays in groups.items():
        plays.sort()
        for (prev_when, *_), (when, row_id, artist, song, ts) in zip(plays, plays[1:]):
            gap = when - prev_when
            if gap <= window:
                duplicates.append((row_id, st, artist, song, ts, gap.total_seconds() / 60))
    duplicates.sort(key=lambda d: d[4])
    return duplicates


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--table', choices=TABLES, help='only this table (default: both)')
    ap.add_argument('--station', help='only this station, exact name')
    ap.add_argument('--window', type=float, default=10, help='minutes between plays that count as a duplicate (default 10)')
    ap.add_argument('--commit', action='store_true', help='actually delete (default is a dry run)')
    args = ap.parse_args()

    window = timedelta(minutes=args.window)
    conn, db_type = db.get_connection()
    c = conn.cursor()

    to_delete = {}
    for table in ([args.table] if args.table else TABLES):
        try:
            found = find_duplicates(c, db_type, table, window, args.station)
        except Exception as e:
            print(f"{table}: skipped ({e})")
            continue
        to_delete[table] = found
        print(f"\n== {table}: {len(found)} duplicate play(s) within {args.window:g} min ==")
        for row_id, st, artist, song, ts, gap in found:
            print(f"  id {row_id:<6} {ts[:16]}  {st:<22} {artist} - {song}   ({gap:.1f} min after previous)")

    total = sum(len(v) for v in to_delete.values())
    if not total:
        print("\nNothing to remove.")
        return
    if not args.commit:
        print(f"\nDry run: {total} row(s) would be deleted. Rerun with --commit to delete them.")
        return

    if db_type == 'sqlite':
        backup = f"radio_songs.db.before_dedupe_{datetime.now():%Y%m%d%H%M%S}"
        dest = sqlite3.connect(backup)
        conn.backup(dest)  # a consistent copy, safe even while the checker is writing
        dest.close()
        print(f"\nBackup written: {backup}")
    else:
        print("\nNo automatic backup for MySQL: make one first if you need it.")

    for table, found in to_delete.items():
        for row_id, *_ in found:
            db.execute_query(c, f"DELETE FROM {table} WHERE id = ?", (row_id,), db_type)
    conn.commit()
    conn.close()
    print(f"Deleted {total} row(s). Run upload_db.py to push the cleaned database to the web server.")


if __name__ == '__main__':
    main()
