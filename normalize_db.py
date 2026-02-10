"""
Script to normalize existing artist and song titles in the database
Applies the same normalization rules to eliminate duplicates from case variations
"""
import sqlite3
import re
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def normalize_song_title(title):
    """Remove prefix patterns like '#742: ' from song titles and normalize case"""
    # Pattern matches: # followed by digits, then :, then optional space(s)
    # Example: "#742: Two Hearts" becomes "Two Hearts"
    normalized = re.sub(r'^#\d+:\s*', '', title)
    normalized = normalized.strip()
    
    # Normalize to title case for consistent storage (e.g., "PHIL COLLINS" -> "Phil Collins")
    # This prevents duplicates due to different capitalization
    # We use a custom title case that handles apostrophes correctly
    words = []
    for word in normalized.split():
        # Handle words with apostrophes (e.g., "can't", "I'm")
        if "'" in word:
            parts = word.split("'")
            # Capitalize first part, lowercase rest
            word = parts[0].capitalize() + "'" + "'".join(p.lower() for p in parts[1:])
        else:
            word = word.capitalize()
        words.append(word)
    
    return ' '.join(words)

def normalize_database():
    """Normalize all artist and song entries in the database"""
    conn = sqlite3.connect('radio_songs.db')
    c = conn.cursor()
    
    # Get all songs
    c.execute("SELECT id, artist, song FROM songs")
    songs = c.fetchall()
    
    print(f"{Fore.CYAN}Found {len(songs)} entries in database")
    print(f"{Fore.CYAN}Starting normalization...{Style.RESET_ALL}\n")
    
    updated_count = 0
    unchanged_count = 0
    
    for song_id, artist, song in songs:
        # Normalize
        normalized_artist = normalize_song_title(artist)
        normalized_song = normalize_song_title(song)
        
        # Check if anything changed
        if artist != normalized_artist or song != normalized_song:
            # Update the record
            c.execute(
                "UPDATE songs SET artist = ?, song = ? WHERE id = ?",
                (normalized_artist, normalized_song, song_id)
            )
            updated_count += 1
            
            # Show what changed
            if artist != normalized_artist:
                print(f"{Fore.YELLOW}Artist: '{artist}' -> '{normalized_artist}'")
            if song != normalized_song:
                print(f"{Fore.YELLOW}Song:   '{song}' -> '{normalized_song}'")
            print()
        else:
            unchanged_count += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Summary
    print(f"{Fore.GREEN}{'='*60}")
    print(f"{Fore.GREEN}Normalization complete!")
    print(f"{Fore.GREEN}Updated: {updated_count} entries")
    print(f"{Fore.GREEN}Unchanged: {unchanged_count} entries")
    print(f"{Fore.GREEN}Total: {len(songs)} entries")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")

if __name__ == '__main__':
    try:
        normalize_database()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Operation cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
