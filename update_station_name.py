#!/usr/bin/env python3
"""
Script to update station names in the radio database
Usage: python update_station_name.py <old_name> <new_name>
Example: python update_station_name.py "Joe" "JOE"
"""

import sys
import db_connection as db

def update_station_name(old_name, new_name):
    """Update all entries with old station name to new station name"""
    try:
        # Initialize database connection
        db_type = db.init_database()
        conn, db_type = db.get_connection()
        c = conn.cursor()
        
        # First, check how many records will be affected
        db.execute_query(c, "SELECT COUNT(*) FROM songs WHERE station = ?", (old_name,), db_type)
        count = c.fetchone()[0]
        
        if count == 0:
            print(f"No records found with station name '{old_name}'")
            conn.close()
            return False
        
        print(f"Found {count} records with station name '{old_name}'")
        
        # Ask for confirmation
        confirm = input(f"Update all {count} records from '{old_name}' to '{new_name}'? (Y/n): ").strip().lower()
        if confirm not in ['', 'y', 'yes']:
            print("Cancelled.")
            conn.close()
            return False
        
        # Perform the update
        db.execute_query(c, "UPDATE songs SET station = ? WHERE station = ?", (new_name, old_name), db_type)
        updated_count = c.rowcount
        conn.commit()
        conn.close()
        
        print(f"✓ Successfully updated {updated_count} records from '{old_name}' to '{new_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error updating station names: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("Usage: python update_station_name.py <old_name> <new_name>")
        print("Example: python update_station_name.py 'Joe' 'JOE'")
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    
    print(f"Station Name Updater")
    print("=" * 30)
    print(f"Updating '{old_name}' to '{new_name}'")
    print()
    
    if update_station_name(old_name, new_name):
        print("Done!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()