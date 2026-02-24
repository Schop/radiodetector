"""
One‑off normalization script for the database.

Searches for any rows where the `artist` field contains the substring
"bailey" (case‑insensitive) and updates the value to the canonical
"Phil Collins & Philip Bailey".  This is useful when multiple variants
(such as "Phil Collins Ft. Philip Bailey", "Philip Bailey & Phil Collins",
etc.) have been logged and you want a consistent name for reporting.

The script uses `db_connection` so it works with both the default
SQLite `radio_songs.db` and a MySQL backend if configured.

Usage:
    python normalize_bailey.py

"""

import db_connection as db

CANONICAL_NAME = "Phil Collins & Philip Bailey"


def normalize_bailey():
    conn, db_type = db.get_connection()
    c = conn.cursor()

    # build the pattern/placeholder for the current database
    pattern = "%bailey%"
    placeholder = db.get_placeholder(db_type)

    # count how many records will be affected
    count_q = f"SELECT COUNT(*) FROM songs WHERE LOWER(artist) LIKE {placeholder}"
    db.execute_query(c, count_q, (pattern,), db_type=db_type)
    count = c.fetchone()[0]

    if count == 0:
        print("No artists containing 'bailey' were found; nothing to do.")
    else:
        print(f"Normalizing {count} artist(s) to '{CANONICAL_NAME}'...")
        upd_q = (
            f"UPDATE songs SET artist = {placeholder} "
            f"WHERE LOWER(artist) LIKE {placeholder}"
        )
        db.execute_query(c, upd_q, (CANONICAL_NAME, pattern), db_type=db_type)
        conn.commit()
        print(f"Completed – {count} row(s) updated.")

    conn.close()
        # Normalize 'bailey' in artist
        if 'bailey' in artist.lower():
            artist = "Phil Collins & Philip Bailey"


if __name__ == '__main__':
    try:
        normalize_bailey()
    except Exception as e:
        print(f"Error during normalization: {e}")
