#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delete_feb10.py

Backs up `radio_songs.db`, optionally shows matching rows (dry-run),
and deletes all rows from `songs` where `timestamp` starts with 2026-02-10.
"""

import os
import sqlite3
import argparse
import shutil
import datetime
import sys


def backup_db(db_path):
    """Create a timestamped backup of the database file and return its path."""
    ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = f"{db_path}.bak-{ts}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def delete_feb10_records(dry_run=False, do_backup=True):
    """Delete or show rows matching 2026-02-10 in the local radio_songs.db.

    Args:
        dry_run (bool): If True, print count and up to 10 example rows, do not delete.
        do_backup (bool): If True, create a timestamped backup before deleting.
    """
    db_path = os.path.join(os.path.dirname(__file__), 'radio_songs.db')

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return 1

    if do_backup:
        try:
            backup_path = backup_db(db_path)
            print(f"Backup created: {backup_path}")
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return 1

    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        select_query = "SELECT COUNT(*) FROM songs WHERE timestamp LIKE ?"
        params = ('2026-02-10%',)
        cursor.execute(select_query, params)
        row = cursor.fetchone()
        match_count = row[0] if row else 0

        if dry_run:
            print(f"Dry run: {match_count} matching rows found for 2026-02-10")
            cursor.execute("SELECT id, station, song, artist, timestamp FROM songs WHERE timestamp LIKE ? LIMIT 10", params)
            rows = cursor.fetchall()
            for r in rows:
                print(r)
            return 0

        # Perform deletion
        delete_query = "DELETE FROM songs WHERE timestamp LIKE ?"
        cursor.execute(delete_query, params)
        deleted_count = cursor.rowcount
        conn.commit()

        print(f"Successfully deleted {deleted_count} records from February 10, 2026")
        return 0

    except Exception as e:
        print(f"Error deleting records: {e}")
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return 1
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description='Delete songs from 2026-02-10 in local radio_songs.db')
    parser.add_argument('--dry-run', action='store_true', help='Show matching rows/count but do not delete')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup before deleting')
    args = parser.parse_args()

    exit_code = delete_feb10_records(dry_run=args.dry_run, do_backup=not args.no_backup)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
