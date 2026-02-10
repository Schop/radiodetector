import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import os
import yaml
import sys
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Log file path
LOG_FILE = 'radio.log'
UPTIME_FILE = '.uptime'

def log_print(message, color='', style=''):
    """Print to console with color and write to log file"""
    # Print to console with color
    if color or style:
        print(f"{color}{style}{message}{Style.RESET_ALL}")
    else:
        print(message)
    
    # Only write to log file explicitly if stdout is a terminal (not redirected)
    # When running as systemd service, stdout is redirected to radio.log
    # so we don't need to write to file explicitly (avoids duplicates)
    if sys.stdout.isatty():
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

# Database setup
conn = sqlite3.connect('radio_songs.db')
c = conn.cursor()

# Create songs table
c.execute('''CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY,
    station TEXT,
    song TEXT,
    artist TEXT,
    timestamp TEXT
)''')

# Create settings table
c.execute('''CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
)''')

# Create stations table
c.execute('''CREATE TABLE IF NOT EXISTS stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    source TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 0,
    updated_at TEXT,
    UNIQUE(name, source)
)''')

conn.commit()

def migrate_database():
    """Check database schema version and perform migrations"""
    c = conn.cursor()
    
    # Check if settings table exists and has data
    c.execute("SELECT COUNT(*) FROM settings")
    settings_count = c.fetchone()[0]
    
    # Check if stations table has data
    c.execute("SELECT COUNT(*) FROM stations")
    stations_count = c.fetchone()[0]
    
    # If tables are empty, migrate from config.yaml
    if settings_count == 0 or stations_count == 0:
        log_print("Migrating configuration from YAML to database...", Fore.YELLOW)
        config = load_station_config_from_yaml()
        
        # Import simple settings into settings table
        import json
        timestamp = datetime.now().isoformat()
        
        if settings_count == 0:
            settings_to_migrate = [
                ('target_artists', json.dumps(config.get('target_artists', []))),
                ('target_songs', json.dumps(config.get('target_songs', []))),
                ('priority_myonlineradio', json.dumps(config.get('priority_myonlineradio', [])))
            ]
            
            for key, value in settings_to_migrate:
                c.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                         (key, value, timestamp))
        
        # Import stations into stations table
        if stations_count == 0:
            stations_to_migrate = []
            
            # Add relisten stations
            for name, slug in config.get('relisten', {}).items():
                stations_to_migrate.append((name, slug, 'relisten', 1, 0, timestamp))
            
            # Add myonlineradio stations
            for name, slug in config.get('myonlineradio', {}).items():
                # Check if this station should be prioritized
                priority = 1 if name in config.get('priority_myonlineradio', []) else 0
                stations_to_migrate.append((name, slug, 'myonlineradio', 1, priority, timestamp))
            
            # Add playlist24 stations
            for name, slug in config.get('playlist24', {}).items():
                stations_to_migrate.append((name, slug, 'playlist24', 1, 0, timestamp))
            
            c.executemany(
                "INSERT OR IGNORE INTO stations (name, slug, source, enabled, priority, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                stations_to_migrate
            )
        
        conn.commit()
        log_print("Configuration migration completed!", Fore.GREEN)

def load_station_config_from_yaml():
    """Load station mappings from config.yaml (fallback/initial load)"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config
    except FileNotFoundError:
        log_print(f"Error: config.yaml not found", Fore.RED)
        return {'relisten': {}, 'myonlineradio': {}, 'playlist24': {}}
    except yaml.YAMLError as e:
        log_print(f"Error parsing config.yaml: {e}", Fore.RED)
        return {'relisten': {}, 'myonlineradio': {}, 'playlist24': {}}

def load_station_config():
    """Load station configuration from database"""
    import json
    c = conn.cursor()
    
    config = {}
    
    # Load simple settings from settings table
    settings_keys = ['target_artists', 'target_songs', 'priority_myonlineradio']
    
    for key in settings_keys:
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        if row:
            try:
                config[key] = json.loads(row[0])
            except json.JSONDecodeError:
                config[key] = []
        else:
            config[key] = []
    
    # Load stations from stations table
    c.execute("SELECT name, slug, source FROM stations WHERE enabled = 1")
    stations = c.fetchall()
    
    config['relisten'] = {}
    config['myonlineradio'] = {}
    config['playlist24'] = {}
    
    for row in stations:
        name, slug, source = row
        if source == 'relisten':
            config['relisten'][name] = slug
        elif source == 'myonlineradio':
            config['myonlineradio'][name] = slug
        elif source == 'playlist24':
            config['playlist24'][name] = slug
    
    return config

def reload_settings():
    """Reload settings from database and update global variables"""
    global TARGET_ARTISTS, TARGET_SONGS, PRIORITY_MYONLINERADIO
    global RELISTEN_STATIONS, ALL_MYONLINERADIO_STATIONS, ALL_PLAYLIST24_STATIONS
    global MYONLINERADIO_STATIONS, PLAYLIST24_STATIONS
    
    config = load_station_config()
    
    TARGET_ARTISTS = config.get('target_artists', [])
    TARGET_SONGS = config.get('target_songs', [])
    PRIORITY_MYONLINERADIO = config.get('priority_myonlineradio', [])
    RELISTEN_STATIONS = {str(k): v for k, v in config.get('relisten', {}).items()}
    ALL_MYONLINERADIO_STATIONS = config.get('myonlineradio', {})
    ALL_PLAYLIST24_STATIONS = config.get('playlist24', {})
    
    # Filter out myonlineradio stations that are already in relisten
    relisten_station_names = set(RELISTEN_STATIONS.keys())
    MYONLINERADIO_STATIONS = {name: slug for name, slug in ALL_MYONLINERADIO_STATIONS.items() 
                               if name not in relisten_station_names}
    
    # Filter out playlist24 stations that are already in relisten or myonlineradio
    all_covered_stations = set(RELISTEN_STATIONS.keys()) | set(ALL_MYONLINERADIO_STATIONS.keys())
    PLAYLIST24_STATIONS = {name: slug for name, slug in ALL_PLAYLIST24_STATIONS.items() 
                           if name not in all_covered_stations}
    
    log_print("Settings reloaded from database", Fore.GREEN)

# Perform database migration
migrate_database()

# Load configuration from database
STATION_CONFIG = load_station_config()

# Load target artists and songs from config
TARGET_ARTISTS = STATION_CONFIG.get('target_artists', [])
TARGET_SONGS = STATION_CONFIG.get('target_songs', [])
PRIORITY_MYONLINERADIO = STATION_CONFIG.get('priority_myonlineradio', [])
RELISTEN_STATIONS = {str(k): v for k, v in STATION_CONFIG.get('relisten', {}).items()}
ALL_MYONLINERADIO_STATIONS = STATION_CONFIG.get('myonlineradio', {})
ALL_PLAYLIST24_STATIONS = STATION_CONFIG.get('playlist24', {})

# Filter out myonlineradio stations that are already in relisten (to avoid duplicates and reduce fetching)
# This reduces 89 stations to only unique ones not available on relisten.nl
relisten_station_names = set(RELISTEN_STATIONS.keys())
MYONLINERADIO_STATIONS = {name: slug for name, slug in ALL_MYONLINERADIO_STATIONS.items() 
                           if name not in relisten_station_names}

# Filter out playlist24 stations that are already in relisten or myonlineradio (to avoid duplicates)
all_covered_stations = set(RELISTEN_STATIONS.keys()) | set(ALL_MYONLINERADIO_STATIONS.keys())
PLAYLIST24_STATIONS = {name: slug for name, slug in ALL_PLAYLIST24_STATIONS.items() 
                       if name not in all_covered_stations}

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


def fetch_station_from_myonlineradio(station_slug):
    """Fetch and parse any station from myonlineradio.nl playlist page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(f'https://myonlineradio.nl/{station_slug}/playlist', timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the js-songListC div with data-url matching the station
        song_list = soup.find('div', {'class': 'js-songListC', 'data-url': station_slug})
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
        # Only print if verbose debugging needed
        # print(f"Error fetching {station_slug} from myonlineradio.nl: {e}")
        return None


def fetch_station_from_playlist24(station_slug):
    """Fetch and parse any station from playlist24.nl playlist page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(f'https://playlist24.nl/{station_slug}/', timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # First try the track-block structure (used by Sublime FM and others)
        track_blocks = soup.find_all('div', {'class': 'track-block'})
        
        if track_blocks:
            # Iterate through track blocks to find the first one with valid data
            for block in track_blocks:
                # Find links with /titel/ and /artiest/ in href
                links = block.find_all('a', href=lambda x: x and ('titel' in x or 'artiest' in x))
                
                if not links:
                    continue
                
                title = None
                artist = None
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Only use links with actual text content
                    if not text:
                        continue
                    
                    if '/titel/' in href and not title:
                        title = text
                    elif '/artiest/' in href and not artist:
                        artist = text
                
                if title and artist:
                    return (artist, title)
        
        # Fallback: Try table structure (used by some other stations)
        table = soup.find('table', {'class': lambda x: x and 'playlist' in str(x).lower() if x else False})
        
        if not table:
            # Try finding any table that might contain playlist data
            table = soup.find('table')
        
        if not table:
            return None
        
        # Try to find the first row with song data (skip header)
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) >= 2:
                # Usually format is: [Time, Artist, Title] or [Artist, Title]
                # Try to extract artist and title
                # Common patterns: time in first cell, then artist, then title
                # Or: artist in first, title in second
                
                if len(cells) >= 3:
                    # Likely: [Time, Artist, Title]
                    artist = cells[1].get_text(strip=True)
                    song = cells[2].get_text(strip=True)
                else:
                    # Likely: [Artist, Title]
                    artist = cells[0].get_text(strip=True)
                    song = cells[1].get_text(strip=True)
                
                # Validate we have actual data (not header text)
                if artist and song and len(artist) > 1 and len(song) > 1:
                    # Skip if looks like header
                    if artist.lower() not in ['artiest', 'artist', 'tijd', 'time'] and \
                       song.lower() not in ['nummer', 'title', 'song', 'track']:
                        return (artist, song)
        
        return None
    
    except Exception as e:
        # Only print if verbose debugging needed
        # print(f"Error fetching {station_slug} from playlist24.nl: {e}")
        return None


def fetch_all_stations_from_relisten():
    """Fetch and parse all stations from https://www.relisten.nl/ homepage"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.relisten.nl/', timeout=15, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dict to store station -> (artist, song) mapping
        stations_data = {}
        
        # Get list of stations to monitor from config (use as filter)
        monitored_stations = set(RELISTEN_STATIONS.keys()) if RELISTEN_STATIONS else None
        
        # Find all h2 tags (station names)
        h2_tags = soup.find_all('h2')
        
        for h2 in h2_tags:
            station_name = h2.text.strip()
            
            # Skip non-station h2 tags (like "Muziekspeler")
            if not station_name or len(station_name) < 2 or station_name == 'Muziekspeler':
                continue
            
            # If we have a filter, only include configured stations
            if monitored_stations and station_name not in monitored_stations:
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
        log_print(f"Error fetching from relisten.nl: {e}", Fore.YELLOW)
        return {}


def main():
    """Main loop - Monitor Dutch radio stations for target artists and songs"""
    # Record start time for uptime tracking
    start_time = datetime.now().isoformat()
    try:
        with open(UPTIME_FILE, 'w') as f:
            f.write(start_time)
    except Exception as e:
        log_print(f"Warning: Could not write uptime file: {e}", Fore.YELLOW)
    
    log_print("Initializing radio checker...")
    log_print(f"- Monitoring {len(RELISTEN_STATIONS)} stations from relisten.nl")
    log_print(f"- Monitoring {len(MYONLINERADIO_STATIONS)} unique stations from myonlineradio.nl (excluding duplicates)")
    log_print(f"- Monitoring {len(PLAYLIST24_STATIONS)} unique stations from playlist24.nl (excluding duplicates)")
    if PRIORITY_MYONLINERADIO:
        log_print(f"- Prioritizing myonlineradio for: {', '.join(PRIORITY_MYONLINERADIO)}")
    log_print(f"- Target artists: {', '.join(TARGET_ARTISTS) if TARGET_ARTISTS else 'None'}")
    log_print(f"- Target songs: {', '.join(TARGET_SONGS) if TARGET_SONGS else 'None'}")
    log_print("=" * 60)
    
    # Track the last song played on each station to detect changes
    last_songs = {}
    
    # Track settings reload (check every 5 minutes)
    settings_check_counter = 0
    last_settings_check = None
    
    try:
        while True:
            # Check if settings have been updated (every 5 iterations = 5 minutes)
            settings_check_counter += 1
            if settings_check_counter >= 5:
                settings_check_counter = 0
                c.execute("SELECT MAX(updated_at) FROM settings")
                latest_update = c.fetchone()[0]
                if last_settings_check is None:
                    last_settings_check = latest_update
                elif latest_update and latest_update != last_settings_check:
                    log_print("Detected settings change, reloading configuration...", Fore.YELLOW)
                    reload_settings()
                    last_settings_check = latest_update
            
            stations_data = {}
            relisten_failed = False
            
            # PRIORITY STATIONS: Fetch from myonlineradio FIRST for stations that need it
            # (e.g., Radio 538 which is not reliably on relisten.nl homepage)
            if PRIORITY_MYONLINERADIO and ALL_MYONLINERADIO_STATIONS:
                for station_name in PRIORITY_MYONLINERADIO:
                    if station_name in ALL_MYONLINERADIO_STATIONS:
                        slug = ALL_MYONLINERADIO_STATIONS[station_name]
                        result = fetch_station_from_myonlineradio(slug)
                        if result:
                            stations_data[station_name] = result
            
            # Fetch from relisten.nl (homepage scraping)
            if RELISTEN_STATIONS:
                relisten_data = fetch_all_stations_from_relisten()
                if relisten_data:
                    stations_data.update(relisten_data)
                else:
                    relisten_failed = True
            
            # Fetch from myonlineradio.nl (individual station playlists)
            # If relisten failed, use ALL myonlineradio stations (including duplicates)
            # Otherwise use only unique stations to avoid redundant checks
            myonline_stations_to_check = ALL_MYONLINERADIO_STATIONS if relisten_failed else MYONLINERADIO_STATIONS
            
            if myonline_stations_to_check:
                for station_name, slug in myonline_stations_to_check.items():
                    # Skip if already fetched from relisten (avoid duplicates)
                    if station_name in stations_data:
                        continue
                    
                    result = fetch_station_from_myonlineradio(slug)
                    if result:
                        stations_data[station_name] = result
            
            # Fetch from playlist24.nl (individual station playlists)
            # If both relisten and myonlineradio failed or returned few results, try all playlist24 stations
            # Otherwise use only unique stations to avoid redundant checks
            use_all_playlist24 = relisten_failed or len(stations_data) < 5
            playlist24_stations_to_check = ALL_PLAYLIST24_STATIONS if use_all_playlist24 else PLAYLIST24_STATIONS
            
            if playlist24_stations_to_check:
                for station_name, slug in playlist24_stations_to_check.items():
                    # Skip if already fetched from other sources (avoid duplicates)
                    if station_name in stations_data:
                        continue
                    
                    result = fetch_station_from_playlist24(slug)
                    if result:
                        stations_data[station_name] = result
            
            if not stations_data:
                log_print(f"Warning: No station data retrieved from any source", Fore.RED)
                time.sleep(60)
                continue
            
            # Track if any songs changed in this iteration
            songs_changed = 0
            
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
                        last_songs[station] = song_key
                        songs_changed += 1
                        
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
                        
                        # Log to database and print if matched
                        if matched:
                            # Log to database (store normalized song title)
                            timestamp = datetime.now().isoformat()
                            c.execute("INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                                      (station, normalized_song, normalized_artist, timestamp))
                            conn.commit()
                            
                            # Beep to alert user (works on Windows and Linux)
                            print('\a', end='', flush=True)
                            
                            # Print with red warning and timestamp
                            log_print(f"[{ts}] [{station}] {normalized_song_info}", Fore.RED, Style.BRIGHT)
                        else:
                            # Print normally for non-matching songs
                            log_print(f"[{ts}] [{station}] {normalized_song_info}")
            
            # Print status message
            if songs_changed == 0:
                log_print("No song changes detected", Fore.CYAN)
            
            # Wait 60 seconds before next check
            log_print("Waiting 60 seconds to update the list again...", Fore.CYAN)
            time.sleep(60)
    
    except KeyboardInterrupt:
        log_print("\n\nShutting down...")
    finally:
        conn.close()

if __name__ == '__main__':
    main()