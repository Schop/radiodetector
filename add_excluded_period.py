#!/usr/bin/env python3
"""
Mark a period (e.g. the Pi was offline) to be left out of the website's averages and
largest-gap statistics. The detections themselves are not touched.

Usage (run next to radio_songs.db):
    python3 add_excluded_period.py 2026-09-06T04:33:43 2026-09-07T03:59:06
    python3 add_excluded_period.py --list
    python3 add_excluded_period.py --remove 2026-09-06T04:33:43

The period is stored in the 'excluded_periods' setting; static_web/api.php reads it.
Run upload_db.py afterwards to push the setting to the web server.
"""

import json
import sys
from datetime import datetime

import db_connection as db

KEY = 'excluded_periods'


def load(c, db_type):
    db.execute_query(c, "SELECT value FROM settings WHERE key = ?", (KEY,), db_type)
    row = c.fetchone()
    return json.loads(row[0]) if row else []


def save(conn, c, db_type, periods):
    db.execute_query(c, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                     (KEY, json.dumps(periods), datetime.now().isoformat()), db_type)
    conn.commit()


def main():
    args = sys.argv[1:]
    conn, db_type = db.get_connection()
    c = conn.cursor()
    periods = load(c, db_type)

    if args == ['--list']:
        for p in periods:
            print(f"{p['start']}  ->  {p['end']}")
        print(f"{len(periods)} excluded period(s)")
    elif len(args) == 2 and args[0] == '--remove':
        kept = [p for p in periods if p['start'] != args[1]]
        save(conn, c, db_type, kept)
        print(f"Removed {len(periods) - len(kept)} period(s)")
    elif len(args) == 2:
        start, end = (datetime.fromisoformat(a) for a in args)
        if end <= start:
            sys.exit("End must be after start")
        periods.append({'start': start.isoformat(), 'end': end.isoformat()})
        save(conn, c, db_type, periods)
        print(f"Added {start} -> {end} ({(end - start).total_seconds() / 3600:.1f} h). Now {len(periods)} period(s).")
    else:
        print(__doc__)
        sys.exit(1)
    conn.close()


if __name__ == '__main__':
    main()
