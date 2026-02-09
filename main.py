import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Database setup
conn = sqlite3.connect('radio_songs.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY,
    station TEXT,
    song TEXT,
    artist TEXT,
    timestamp TEXT
)''')
conn.commit()

# Artists to check
TARGET_ARTISTS = ['Phil Collins', 'Genesis']

# Song titles to check (case-insensitive matching)
# Examples: TARGET_SONGS = ['In The Air Tonight', 'Another Day in Paradise', 'Land of Confusion']
TARGET_SONGS = []

def get_timestamp():
    """Get current time in HH:mm format"""
    return datetime.now().strftime('%H:%M')

def normalize_song_title(title):
    """Remove prefix patterns like '#742: ' from song titles"""
    # Pattern matches: # followed by digits, then :, then optional space(s)
    # Example: "#742: Two Hearts" becomes "Two Hearts"
    normalized = re.sub(r'^#\d+:\s*', '', title)
    return normalized

def create_song_key(artist, song):
    """Create a normalized key for song comparison to handle different orderings"""
    # Normalize both parts
    norm_artist = normalize_song_title(artist.lower().strip())
    norm_song = normalize_song_title(song.lower().strip())
    
    # Sort them alphabetically to create a consistent key regardless of order
    # This way "Artist - Song" and "Song - Artist" will produce the same key
    parts = sorted([norm_artist, norm_song])
    return f"{parts[0]} | {parts[1]}"

def fetch_icy_metadata_from_stream(stream_url, station_name):
    """Extract ICY metadata from streaming server"""
    try:
        headers = {'Icy-MetaData': '1'}
        response = requests.get(stream_url, timeout=10, headers=headers, stream=True)
        
        if response.status_code != 200:
            return None
        
        icy_metaint = int(response.headers.get('icy-metaint', 0))
        if icy_metaint == 0:
            return None
        
        # Read audio data until we hit a metadata block
        bytes_read = 0
        for chunk in response.iter_content(chunk_size=4096):
            if not chunk:
                break
            
            bytes_read += len(chunk)
            
            if bytes_read >= icy_metaint:
                # We've reached metadata
                remainder = len(chunk) - (bytes_read - icy_metaint)
                metadata_chunk = chunk[remainder:]
                
                if metadata_chunk:
                    # First byte is length (in 16-byte blocks)
                    metadata_length = metadata_chunk[0] * 16
                    if metadata_length > 0:
                        metadata = metadata_chunk[1:1+metadata_length].decode('utf-8', errors='ignore').strip('\x00')
                        
                        # Parse StreamTitle from metadata
                        if 'StreamTitle=' in metadata:
                            title_part = metadata.split("StreamTitle='")[1].split("'")[0]
                            
                            # Skip ads and empty titles
                            if title_part and title_part.strip() and 'adw_ad' not in metadata.lower():
                                # Try to parse "artist - song" format
                                if ' - ' in title_part:
                                    parts = title_part.split(' - ', 1)
                                    artist = parts[0].strip()
                                    song = parts[1].strip()
                                    return (artist, song)
                                else:
                                    # If no dash separator, treat whole thing as song (no artist)
                                    return ('Unknown', title_part.strip())
                
                break
        
        return None
    
    except Exception as e:
        print(f"Error fetching ICY metadata from {station_name}: {e}")
        return None


def fetch_joe_from_myonlineradio():
    """Fetch and parse joe radio from myonlineradio.nl playlist page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://myonlineradio.nl/joe/playlist', timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the js-songListC div with data-url="joe"
        song_list = soup.find('div', {'class': 'js-songListC', 'data-url': 'joe'})
        if not song_list:
            return None
        
        # Find all song rows (they have class yt-row or live-link)
        tracks = song_list.find_all('div', {'class': lambda x: x and 'yt-row' in x})
        
        if not tracks:
            return None
        
        # Get the first track (most recent)
        first_track = tracks[0]
        
        # Extract artist (byArtist span)
        artist_span = first_track.find('span', {'itemprop': 'byArtist'})
        if not artist_span:
            return None
        artist = artist_span.text.strip()
        
        # Extract song name (name span)
        song_span = first_track.find('span', {'itemprop': 'name'})
        if not song_span:
            return None
        song = song_span.text.strip()
        
        if artist and song:
            return (artist, song)
        
        return None
    
    except Exception as e:
        print(f"Error fetching joe from myonlineradio.nl: {e}")
        return None


def fetch_all_stations_from_relisten():
    """Fetch and parse all stations from https://www.relisten.nl/"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.relisten.nl/', timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dict to store station -> (artist, song) mapping
        stations_data = {}
        
        # Find all h2 tags (station names)
        h2_tags = soup.find_all('h2')
        
        for h2 in h2_tags:
            station_name = h2.text.strip()
            
            # Skip non-station h2 tags (like "Muziekspeler")
            if not station_name or len(station_name) < 2 or station_name == 'Muziekspeler':
                continue
            
            # Find the next h4 (song title) after this h2
            h4 = h2.find_next('h4')
            if not h4:
                continue
            
            # Extract song title from h4 (remove timestamp)
            song = h4.text.strip()
            song = song.split('\n')[0].strip()  # Remove everything after newline
            if not song or len(song) < 2:
                continue
            
            # Find the artist in the next <p> tag
            artist_p = h4.find_next('p')
            if not artist_p:
                continue
            
            artist = artist_p.text.strip()
            if not artist or len(artist) < 2:
                continue
            
            # Store the station data
            stations_data[station_name] = (artist, song)
        
        return stations_data
    
    except Exception as e:
        print(f"Error fetching from relisten.nl: {e}")
        return {}



def main():
    """Main loop - Monitor Dutch radio stations for target artists and songs"""
    print("Initializing radio checker...")
    print("- Monitoring 19 stations from relisten.nl")
    print("- Monitoring joe.nl (via stream metadata + myonlineradio.nl fallback)")
    print(f"- Target artists: {', '.join(TARGET_ARTISTS) if TARGET_ARTISTS else 'None'}")
    print(f"- Target songs: {', '.join(TARGET_SONGS) if TARGET_SONGS else 'None'}")
    print("=" * 60)
    
    # Track the last song played on each station to detect changes
    last_songs = {}
    
    try:
        while True:
            # Fetch all real-time playlist data from relisten.nl
            stations_data = fetch_all_stations_from_relisten()
            
            # Fetch joe.nl data - prioritize myonlineradio.nl for consistent artist/song order
            joe_data = fetch_joe_from_myonlineradio()
            if joe_data:
                stations_data['joe.nl'] = joe_data
            else:
                # Fall back to ICY stream metadata if webpage fails
                metadata = fetch_icy_metadata_from_stream('https://stream.joe.nl/joe/mp3', 'joe.nl')
                if metadata:
                    stations_data['joe.nl'] = metadata
            
            if not stations_data:
                print("Warning: No station data retrieved")
                time.sleep(60)
                continue
            
            # Process each station
            for station in sorted(stations_data.keys()):
                artist, song = stations_data[station]
                
                if song and artist:
                    # Normalize song title (remove patterns like "#742: ")
                    normalized_song = normalize_song_title(song)
                    normalized_artist = normalize_song_title(artist)
                    normalized_song_info = f"{normalized_artist} - {normalized_song}"
                    
                    # Create a unique key to detect if this is the same song (handles ordering issues)
                    song_key = create_song_key(artist, song)
                    
                    # Check if this is different from last known song (using song key)
                    if station not in last_songs or last_songs[station] != song_key:
                        ts = get_timestamp()
                        print(f"[{ts}] [{station}] {normalized_song_info}")
                        last_songs[station] = song_key
                        
                        # Check if artist is in target list
                        matched = False
                        for target_artist in TARGET_ARTISTS:
                            if target_artist and target_artist.lower() in normalized_artist.lower():
                                matched = True
                                break
                        
                        # Check if song is in target list (using normalized song title)
                        if not matched:
                            for target_song in TARGET_SONGS:
                                if target_song and target_song.lower() in normalized_song.lower():
                                    matched = True
                                    break
                        
                        # Log to database if matched
                        if matched:
                            # Log to database (store normalized song title)
                            timestamp = datetime.now().isoformat()
                            c.execute("INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                                      (station, normalized_song, normalized_artist, timestamp))
                            conn.commit()
                            
                            # Print with red warning and timestamp
                            ts = get_timestamp()
                            print(f"{Fore.RED}{Style.BRIGHT}[{ts}] ✓ {normalized_artist} - {normalized_song} ({station}){Style.RESET_ALL}")

            
            # Wait 60 seconds before next check
            time.sleep(60)
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        conn.close()

if __name__ == '__main__':
    main()