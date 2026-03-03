"""
One-off normalization script for the database.

Searches for any rows where the `song` field is exactly "Two Hearts" (case-insensitive)
and updates the `artist` value to the canonical "Phil Collins & Philip Bailey".
This is useful for ensuring consistent artist naming for this song.

The script uses `db_connection` so it works with both the default
SQLite `radio_songs.db` and a MySQL backend if configured.

Usage:
    python normalize_two_hearts.py
"""

import db_connection as db

CANONICAL_NAME = "Phil Collins & Philip Bailey"
TARGET_TITLE = "Two Hearts"

def normalize_two_hearts():
    conn, db_type = db.get_connection()
    c = conn.cursor()

    # build the pattern/placeholder for the current database
    placeholder = db.get_placeholder(db_type)

    # count how many records will be affected
    count_q = f"SELECT COUNT(*) FROM songs WHERE LOWER(song) = {placeholder}"
    db.execute_query(c, count_q, (TARGET_TITLE.lower(),), db_type=db_type)
    count = c.fetchone()[0]

    if count == 0:
        print("No songs with title 'Two Hearts' were found; nothing to do.")
    else:
        print(f"Normalizing {count} artist(s) to '{CANONICAL_NAME}' for title '{TARGET_TITLE}'...")
        upd_q = (
            f"UPDATE songs SET artist = {placeholder} "
            f"WHERE LOWER(song) = {placeholder}"
        )
        db.execute_query(c, upd_q, (CANONICAL_NAME, TARGET_TITLE.lower()), db_type=db_type)
        conn.commit()
        print(f"Completed – {count} row(s) updated.")

    conn.close()

if __name__ == '__main__':
    try:
        normalize_two_hearts()
    except Exception as e:
        print(f"Error during normalization: {e}")
