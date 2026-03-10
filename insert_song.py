#!/usr/bin/env python3
"""
Script to manually insert songs into the radio database
Usage: python insert_song.py
"""

import sys
import os
from datetime import datetime
import db_connection as db

def get_user_input():
    """Get song details from user input"""
    print("Manual Song Entry")
    print("=" * 40)
    
    station = input("Enter station name: ").strip()
    if not station:
        print("Station name is required!")
        return None
    
    artist = input("Enter artist name: ").strip()
    if not artist:
        print("Artist name is required!")
        return None
    
    song = input("Enter song title: ").strip()
    if not song:
        print("Song title is required!")
        return None
    
    # Ask for custom timestamp or use current time
    use_current = input("Use current timestamp? (Y/n): ").strip().lower()
    if use_current in ['', 'y', 'yes']:
        timestamp = datetime.now().isoformat()
    else:
        timestamp_input = input("Enter timestamp (YYYY-MM-DD HH:MM:SS or leave empty for now): ").strip()
        if timestamp_input:
            try:
                # Try to parse the input timestamp
                parsed_time = datetime.strptime(timestamp_input, '%Y-%m-%d %H:%M:%S')
                timestamp = parsed_time.isoformat()
            except ValueError:
                print("Invalid timestamp format! Using current time instead.")
                timestamp = datetime.now().isoformat()
        else:
            timestamp = datetime.now().isoformat()
    
    return {
        'station': station,
        'artist': artist,
        'song': song,
        'timestamp': timestamp
    }

def insert_song_to_db(song_data):
    """Insert song data into the database"""
    try:
        # Initialize database connection
        db_type = db.init_database()
        conn, db_type = db.get_connection()
        c = conn.cursor()
        
        # Insert the song
        db.execute_query(c, 
            "INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
            (song_data['station'], song_data['song'], song_data['artist'], song_data['timestamp']),
            db_type
        )
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Successfully inserted:")
        print(f"  Station: {song_data['station']}")
        print(f"  Artist: {song_data['artist']}")
        print(f"  Song: {song_data['song']}")
        print(f"  Timestamp: {song_data['timestamp']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error inserting song: {e}")
        return False

def insert_from_command_line():
    """Insert song using command line arguments"""
    if len(sys.argv) < 4:
        print("Usage: python insert_song.py <station> <artist> <song> [timestamp]")
        print("Example: python insert_song.py 'Radio 538' 'Phil Collins' 'In The Air Tonight'")
        return False
    
    station = sys.argv[1]
    artist = sys.argv[2] 
    song = sys.argv[3]
    
    if len(sys.argv) > 4:
        timestamp_input = sys.argv[4]
        try:
            parsed_time = datetime.strptime(timestamp_input, '%Y-%m-%d %H:%M:%S')
            timestamp = parsed_time.isoformat()
        except ValueError:
            print("Invalid timestamp format! Use: YYYY-MM-DD HH:MM:SS")
            return False
    else:
        timestamp = datetime.now().isoformat()
    
    song_data = {
        'station': station,
        'artist': artist,
        'song': song,
        'timestamp': timestamp
    }
    
    return insert_song_to_db(song_data)

def main():
    """Main function"""
    print("Radio Song Database - Manual Insert Tool")
    print("=" * 50)
    
    # Check if command line arguments were provided
    if len(sys.argv) > 1:
        if insert_from_command_line():
            print("\nDone!")
        else:
            sys.exit(1)
    else:
        # Interactive mode
        while True:
            try:
                song_data = get_user_input()
                if not song_data:
                    continue
                
                # Confirm before inserting
                print(f"\nReady to insert:")
                print(f"  Station: {song_data['station']}")
                print(f"  Artist: {song_data['artist']}")
                print(f"  Song: {song_data['song']}")
                print(f"  Timestamp: {song_data['timestamp']}")
                
                confirm = input("\nInsert this song? (Y/n): ").strip().lower()
                if confirm in ['', 'y', 'yes']:
                    if insert_song_to_db(song_data):
                        print("\nSong inserted successfully!")
                    else:
                        print("\nFailed to insert song.")
                else:
                    print("Cancelled.")
                
                # Ask if user wants to insert another song
                another = input("\nInsert another song? (Y/n): ").strip().lower()
                if another not in ['', 'y', 'yes']:
                    break
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
        
        print("\nGoodbye!")

if __name__ == "__main__":
    main()