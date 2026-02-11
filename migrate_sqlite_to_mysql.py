#!/usr/bin/env python3
"""
Migrate data from SQLite to MySQL
Copies all songs, settings, and stations from local SQLite to remote MySQL database
"""

import sqlite3
import mysql.connector
import sys
from datetime import datetime

# SQLite configuration
SQLITE_DB = 'radio_songs.db'

# MySQL configuration (FreeSQLDatabase)
MYSQL_CONFIG = {
    'host': 'sql7.freesqldatabase.com',
    'database': 'sql7816777',
    'user': 'sql7816777',
    'password': 'EusbhwFIKb',
    'port': 3306,
    'connect_timeout': 15
}

def connect_sqlite():
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        print(f"✅ Connected to SQLite: {SQLITE_DB}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to SQLite: {e}")
        sys.exit(1)

def connect_mysql():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print(f"✅ Connected to MySQL: {MYSQL_CONFIG['host']}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        sys.exit(1)

def create_mysql_tables(mysql_conn):
    """Create tables in MySQL if they don't exist"""
    cursor = mysql_conn.cursor()
    
    print("\n📋 Creating MySQL tables...")
    
    # Songs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            station VARCHAR(255) NOT NULL,
            artist VARCHAR(255) NOT NULL,
            song VARCHAR(255) NOT NULL,
            timestamp VARCHAR(255) NOT NULL,
            INDEX idx_timestamp (timestamp(100)),
            INDEX idx_station (station(100)),
            INDEX idx_artist (artist(100))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("  ✅ Created 'songs' table")
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `key` VARCHAR(100) NOT NULL UNIQUE,
            value TEXT,
            updated_at VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("  ✅ Created 'settings' table")
    
    # Stations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            source VARCHAR(50) NOT NULL,
            enabled TINYINT(1) DEFAULT 1,
            priority TINYINT(1) DEFAULT 0,
            updated_at VARCHAR(255),
            UNIQUE KEY unique_station (name(100), source)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("  ✅ Created 'stations' table")
    
    mysql_conn.commit()
    cursor.close()

def migrate_songs(sqlite_conn, mysql_conn):
    """Migrate songs from SQLite to MySQL"""
    print("\n📦 Migrating songs...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    # Get all songs from SQLite
    sqlite_cursor.execute("SELECT station, artist, song, timestamp FROM songs")
    songs = sqlite_cursor.fetchall()
    
    if not songs:
        print("  ⚠️  No songs found in SQLite")
        return 0
    
    print(f"  Found {len(songs)} songs to migrate")
    
    # Insert into MySQL (use INSERT IGNORE to skip duplicates)
    inserted = 0
    for song in songs:
        try:
            mysql_cursor.execute("""
                INSERT INTO songs (station, artist, song, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (song['station'], song['artist'], song['song'], song['timestamp']))
            inserted += 1
            if inserted % 100 == 0:
                print(f"  Migrated {inserted}/{len(songs)} songs...")
        except mysql.connector.IntegrityError:
            pass  # Skip duplicates
    
    mysql_conn.commit()
    print(f"  ✅ Migrated {inserted} songs")
    
    sqlite_cursor.close()
    mysql_cursor.close()
    return inserted

def migrate_settings(sqlite_conn, mysql_conn):
    """Migrate settings from SQLite to MySQL"""
    print("\n⚙️  Migrating settings...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # Get all settings from SQLite
        sqlite_cursor.execute("SELECT `key`, value, updated_at FROM settings")
        settings = sqlite_cursor.fetchall()
        
        if not settings:
            print("  ⚠️  No settings found in SQLite")
            return 0
        
        print(f"  Found {len(settings)} settings to migrate")
        
        # Insert into MySQL
        inserted = 0
        for setting in settings:
            try:
                mysql_cursor.execute("""
                    INSERT INTO settings (`key`, value, updated_at)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE value = VALUES(value), updated_at = VALUES(updated_at)
                """, (setting['key'], setting['value'], setting['updated_at']))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Failed to migrate setting {setting['key']}: {e}")
        
        mysql_conn.commit()
        print(f"  ✅ Migrated {inserted} settings")
        
        sqlite_cursor.close()
        mysql_cursor.close()
        return inserted
        
    except sqlite3.OperationalError:
        print("  ⚠️  Settings table doesn't exist in SQLite, skipping")
        return 0

def migrate_stations(sqlite_conn, mysql_conn):
    """Migrate stations from SQLite to MySQL"""
    print("\n📻 Migrating stations...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # Get all stations from SQLite
        sqlite_cursor.execute("SELECT name, slug, source, enabled, priority, updated_at FROM stations")
        stations = sqlite_cursor.fetchall()
        
        if not stations:
            print("  ⚠️  No stations found in SQLite")
            return 0
        
        print(f"  Found {len(stations)} stations to migrate")
        
        # Insert into MySQL
        inserted = 0
        for station in stations:
            try:
                mysql_cursor.execute("""
                    INSERT INTO stations (name, slug, source, enabled, priority, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        slug = VALUES(slug),
                        enabled = VALUES(enabled),
                        priority = VALUES(priority),
                        updated_at = VALUES(updated_at)
                """, (station['name'], station['slug'], station['source'], 
                      station['enabled'], station['priority'], station['updated_at']))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Failed to migrate station {station['name']}: {e}")
        
        mysql_conn.commit()
        print(f"  ✅ Migrated {inserted} stations")
        
        sqlite_cursor.close()
        mysql_cursor.close()
        return inserted
        
    except sqlite3.OperationalError:
        print("  ⚠️  Stations table doesn't exist in SQLite, skipping")
        return 0

def verify_migration(sqlite_conn, mysql_conn):
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    # Check songs count
    sqlite_cursor.execute("SELECT COUNT(*) FROM songs")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    mysql_cursor.execute("SELECT COUNT(*) FROM songs")
    mysql_count = mysql_cursor.fetchone()[0]
    
    print(f"  Songs: SQLite={sqlite_count}, MySQL={mysql_count}")
    
    if mysql_count >= sqlite_count:
        print("  ✅ Song count matches!")
    else:
        print("  ⚠️  MySQL has fewer songs than SQLite")
    
    sqlite_cursor.close()
    mysql_cursor.close()

def main():
    print("=" * 60)
    print("SQLite to MySQL Migration Tool")
    print("=" * 60)
    
    # Connect to databases
    sqlite_conn = connect_sqlite()
    mysql_conn = connect_mysql()
    
    # Create MySQL tables
    create_mysql_tables(mysql_conn)
    
    # Migrate data
    total_songs = migrate_songs(sqlite_conn, mysql_conn)
    total_settings = migrate_settings(sqlite_conn, mysql_conn)
    total_stations = migrate_stations(sqlite_conn, mysql_conn)
    
    # Verify
    verify_migration(sqlite_conn, mysql_conn)
    
    # Close connections
    sqlite_conn.close()
    mysql_conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"  Songs migrated: {total_songs}")
    print(f"  Settings migrated: {total_settings}")
    print(f"  Stations migrated: {total_stations}")
    print("\nYou can now update config.yaml to use MySQL:")
    print("  database:")
    print("    type: mysql")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        sys.exit(1)
