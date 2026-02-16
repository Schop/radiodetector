#!/usr/bin/env python3
"""
Script to delete all records from the songs table with date February 10, 2026
"""

import sys
import os

# Add the current directory to the path so we can import db_connection
sys.path.insert(0, os.path.dirname(__file__))

from db_connection import load_db_config, get_connection

def delete_feb10_records():
    """Delete all songs records from February 10, 2026"""
    try:
        # Load database configuration
        load_db_config()

        # Get database connection
        conn = get_connection()
        cursor = conn.cursor()

        # Delete records where timestamp starts with '2026-02-10'
        delete_query = "DELETE FROM songs WHERE timestamp LIKE '2026-02-10%'"
        cursor.execute(delete_query)

        # Get the number of deleted rows
        deleted_count = cursor.rowcount

        # Commit the changes
        conn.commit()

        print(f"Successfully deleted {deleted_count} records from February 10, 2026")

    except Exception as e:
        print(f"Error deleting records: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    delete_feb10_records()