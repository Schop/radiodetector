#!/usr/bin/env python3
"""
Find Phil Collins / Genesis detections in radio.log since a given date.
Read-only: it does not touch the database.

Usage: python find_log_detections.py [since] [logfile] [--station JOE] [--csv out.csv]
Example: python find_log_detections.py 2026-07-23 radio.log --station JOE

Understands both log formats:
  [2026-03-03 13:32:48] [13:32] [JOE] [myonlineradio.nl] Artist - Title   (old)
  [2026-07-24 13:32:48] [13:32] JOE: Artist - Title (via myonlineradio.nl) (terminal run)
  [13:32] JOE: Artist - Title (via myonlineradio.nl)                      (systemd, no date)

Lines without a date (systemd) get one by walking backwards from the log file's
last-modified date and stepping back a day whenever the clock time jumps forward.
That is approximate if the service was down for a full day or more; those rows
are marked with '~'.
"""

import argparse
import csv
import os
import re
from datetime import datetime, timedelta

DATE_PREFIX = r'(?:\[(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\] )?'
OLD_FORMAT = re.compile(DATE_PREFIX + r'\[(\d{2}:\d{2})\] \[(.+?)\] (?:\[(.+?)\] )?(.+?) - (.+)$')
NEW_FORMAT = re.compile(DATE_PREFIX + r'\[(\d{2}:\d{2})\] ([^\[\]]+?): (.+?) - (.+?)(?: \(via (.+)\))?$')
ANY_TIME = re.compile(DATE_PREFIX + r'\[(\d{2}:\d{2})\]')


def parse_line(line):
    """Return (date or None, 'HH:MM', station, artist, song, source) or None"""
    m = OLD_FORMAT.match(line)
    if m:
        date, hm, station, source, artist, song = m.groups()
        return date, hm, station, artist.strip(), song.strip(), source or ''
    m = NEW_FORMAT.match(line)
    if m:
        date, hm, station, artist, song, source = m.groups()
        return date, hm, station, artist.strip(), song.strip(), source or ''
    return None


def is_target(artist, song):
    """Phil Collins or Genesis in either field (some stations report title first)"""
    for field in (artist, song):
        low = field.lower()
        if 'phil collins' in low or low == 'genesis':
            return True
    return False


def assign_dates(lines, end_date):
    """Return a date string per line (or None) plus a flag if it was inferred.
    Walks backwards from end_date; a time later than the following line's means midnight passed."""
    dates = [None] * len(lines)
    inferred = [False] * len(lines)
    current = end_date
    next_minutes = None
    for i in range(len(lines) - 1, -1, -1):
        m = ANY_TIME.match(lines[i])
        if not m:
            continue
        explicit, hm = m.groups()
        minutes = int(hm[:2]) * 60 + int(hm[3:])
        if explicit:
            current = datetime.strptime(explicit, '%Y-%m-%d').date()
        elif next_minutes is not None and minutes > next_minutes + 5:
            current -= timedelta(days=1)
        dates[i] = current.isoformat()
        inferred[i] = not explicit
        next_minutes = minutes
    return dates, inferred


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('since', nargs='?', default='2026-07-23', help='start date YYYY-MM-DD (default 2026-07-23)')
    ap.add_argument('logfile', nargs='?', default='radio.log')
    ap.add_argument('--station', help='only this station, e.g. JOE')
    ap.add_argument('--csv', help='also write results to this CSV file')
    args = ap.parse_args()

    since = datetime.strptime(args.since, '%Y-%m-%d').date().isoformat()
    end_date = datetime.fromtimestamp(os.path.getmtime(args.logfile)).date()

    with open(args.logfile, encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]

    dates, inferred = assign_dates(lines, end_date)

    rows = []
    for line, date, inf in zip(lines, dates, inferred):
        if not date or date < since:
            continue
        parsed = parse_line(line)
        if not parsed:
            continue
        _, hm, station, artist, song, source = parsed
        if args.station and station.lower() != args.station.lower():
            continue
        if is_target(artist, song):
            rows.append((date, hm, station, artist, song, source, inf))

    for date, hm, station, artist, song, source, inf in rows:
        print(f"{date}{'~' if inf else ' '} {hm}  {station:<20} {artist} - {song}  {source}")
    print(f"\n{len(rows)} detection(s) since {since}" + (f" on {args.station}" if args.station else ''))
    if any(r[6] for r in rows):
        print("~ = date inferred from the file's last-modified date (no date in the log line)")

    if args.csv:
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['date', 'time', 'station', 'artist', 'song', 'source', 'date_inferred'])
            w.writerows(rows)
        print(f"Wrote {args.csv}")


if __name__ == '__main__':
    main()
