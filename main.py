import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time
import re
import os
import yaml
import sys
from colorama import Fore, Style, init
import db_connection as db
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# Log file path
LOG_FILE = 'radio.log'
UPTIME_FILE = '.uptime'

def log_print(message, color='', style=''):
    """Print to console with color and write to log file"""
    # When stdout is redirected (systemd -> radio.log) there is no other timestamp,
    # so prefix the full date/time to keep the log datable
    prefix = '' if sys.stdout.isatty() else f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "

    # Print to console with color
    if color or style:
        print(f"{prefix}{color}{style}{message}{Style.RESET_ALL}")
    else:
        print(f"{prefix}{message}")

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
db_type = db.init_database()
log_print(f"Using {db_type.upper()} database", Fore.CYAN)

# Get persistent connection
conn, db_type = db.get_connection()

def migrate_database():
    """Check database schema version and perform migrations"""
    c = conn.cursor()
    
    # Check if settings table exists and has data
    db.execute_query(c, "SELECT COUNT(*) FROM settings", db_type=db_type)
    settings_count = c.fetchone()[0]
    
    # Check if stations table has data
    db.execute_query(c, "SELECT COUNT(*) FROM stations", db_type=db_type)
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
                ('tracked_songs', json.dumps(config.get('tracked_songs', []))),
                ('priority_myonlineradio', json.dumps(config.get('priority_myonlineradio', [])))
            ]
            
            for key, value in settings_to_migrate:
                db.execute_query(c, "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                         (key, value, timestamp), db_type)
        
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
            
            db.executemany_query(c,
                "INSERT OR IGNORE INTO stations (name, slug, source, enabled, priority, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                stations_to_migrate, db_type)
        
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
    settings_keys = ['target_artists', 'target_songs', 'tracked_songs', 'priority_myonlineradio']
    
    for key in settings_keys:
        db.execute_query(c, "SELECT value FROM settings WHERE key = ?", (key,), db_type)
        row = c.fetchone()
        if row:
            try:
                config[key] = json.loads(row[0])
            except json.JSONDecodeError:
                config[key] = []
        else:
            config[key] = []
    
    # Load stations from stations table
    db.execute_query(c, "SELECT name, slug, source FROM stations WHERE enabled = 1", db_type=db_type)
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
    global TARGET_ARTISTS, TARGET_SONGS, TRACKED_SONGS, PRIORITY_MYONLINERADIO
    global RELISTEN_STATIONS, ALL_MYONLINERADIO_STATIONS, ALL_PLAYLIST24_STATIONS
    global MYONLINERADIO_STATIONS, PLAYLIST24_STATIONS
    
    config = load_station_config()
    
    TARGET_ARTISTS = config.get('target_artists', [])
    TARGET_SONGS = config.get('target_songs', [])
    TRACKED_SONGS = config.get('tracked_songs', [])
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
TRACKED_SONGS = STATION_CONFIG.get('tracked_songs', [])
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

# Stations whose sources sometimes report "title - artist" instead of "artist - title"
SWAPPED_ORDER_STATIONS = {'JOE'}

def parse_target_song(entry):
    """'Toto - Africa' -> ('toto', 'africa'); a plain 'Africa' -> (None, 'africa') matches any artist"""
    if ' - ' in entry:
        artist, title = entry.split(' - ', 1)
        return artist.strip().lower(), title.strip().lower()
    return None, entry.strip().lower()

def matches_song_list(entries, artist, song):
    """True if artist/song (already normalized) match an entry; 'Artist - Title' entries need both"""
    for entry in entries:
        if not entry:
            continue
        target_artist, target_title = parse_target_song(entry)
        if target_title and target_title in song.lower() and (target_artist is None or target_artist == artist.lower()):
            return True
    return False

def matches_target(artist, song):
    """True if the artist or song matches a configured target or tracked song (artist/song already normalized)"""
    for target_artist in TARGET_ARTISTS:
        if target_artist == "Phil Collins" and target_artist.lower() in artist.lower():
            return True
        if target_artist == "Genesis" and target_artist.lower() == artist.lower():
            return True
    return matches_song_list(TARGET_SONGS, artist, song) or matches_song_list(TRACKED_SONGS, artist, song)

def upload_database():
    """Upload the database to the web server (non-fatal)"""
    try:
        import subprocess
        result = subprocess.run(['python3', 'upload_db.py'],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log_print(f"✓ Database uploaded to web server", Fore.GREEN)
        else:
            log_print(f"⚠️ Database upload failed: {result.stderr.strip()}", Fore.YELLOW)
    except Exception as e:
        log_print(f"⚠️ Database upload error: {e}", Fore.YELLOW)

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



def fetch_station_from_myonlineradio_selenium(station_slug):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1280,800")
    options.binary_location = "/usr/bin/chromium-browser"  # Pi OS location


    driver = webdriver.Chrome()
   

    url = f'https://myonlineradio.nl/{station_slug}'
    driver.get(url)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    act_song_div = soup.find('div', {'class': 'actSong'})
    if act_song_div:
        a_tag = act_song_div.find('a')
        if a_tag:
            song_info = a_tag.get_text(strip=True)
            if ' - ' in song_info:
                artist, song = song_info.split(' - ', 1)
                return (artist.strip(), song.strip())
            else:
                return ('Unknown', song_info.strip())
    return None

def fetch_station_from_myonlineradio(station_slug):
    """Fetch current song from the main myonlineradio.nl station page (using .actSong)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,nl-NL;q=0.8,nl;q=0.7',
            'Referer': 'https://myonlineradio.nl/service-worker.min.js?info=260305190604',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'same-origin',
            'Sec-Fetch-Site': 'same-origin',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',  # Let requests handle encoding
            'Cookie': 'stpdsck=1; webp_support=1; ttv7_act=2026-3-7; ttv7=4; PHPSESSID=850n54govpphtj7h5fccqlp9mv; sw-version=260305190604; radioSteps=eyJqb2UiOnsibmFtZSI6IkpPRSIsInJpZCI6IjYwIiwicGljIjoianBnIiwidGltZSI6MTc3MjkxMTM5Niwidmlld19udW0iOjR9LCJyYWRpby1yaWpubW9uZCI6eyJuYW1lIjoiUmFkaW8lMjBSaWpubW9uZCIsInJpZCI6IjI3IiwicGljIjoianBnIiwidGltZSI6MTc3MjkxMDkyMiwidmlld19udW0iOjF9fQ%3D%3D'
        }
        url = f'https://myonlineradio.nl/{station_slug}'
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the .actSong div
        act_song_div = soup.find('div', {'class': 'actSong'})
        if not act_song_div:
            return None
        
        # Find the <a> inside .actSong
        a_tag = act_song_div.find('a')
        if not a_tag:
            return None
        
        # The text is "ARTIST - Title"
        song_info = a_tag.get_text(strip=True)
        # Sometimes there are multiple " - ", so split on the first only
        if ' - ' in song_info:
            artist, song = song_info.split(' - ', 1)
            artist = artist.strip()
            song = song.strip()
            return (artist, song)
        else:
            # fallback: treat all as title, artist unknown
            return ('Unknown', song_info.strip())
        
    except Exception as e:
        print(f"Error fetching {station_slug} on myonlineradio.nl: {e}")
        return None

# NPO stations share one now-playing API: https://www.<site>.nl/api/tracks
NPO_STATION_SITES = {
    'NPO Radio 1': 'nporadio1',
    'NPO Radio 2': 'nporadio2',
    'NPO 3FM': 'npo3fm',
    'NPO Radio 5': 'nporadio5',
}
NPO_MAX_AGE = timedelta(minutes=20)  # ignore a feed whose newest track ended longer ago than this

def fetch_station_from_npo(site):
    """Fetch current song from an NPO station's own tracks API (the broadcaster's feed)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(f'https://www.{site}.nl/api/tracks', timeout=15, headers=headers)
        response.raise_for_status()
        tracks = response.json().get('data', [])

        # Times are naive Amsterdam local time
        now = datetime.now(ZoneInfo('Europe/Amsterdam')).replace(tzinfo=None)
        started = []
        for t in tracks:
            try:
                start = datetime.fromisoformat(t['startdatetime'])
            except (KeyError, TypeError, ValueError):
                continue
            if start <= now and (t.get('artist') or '').strip() and (t.get('title') or '').strip():
                started.append((start, t))
        if not started:
            return None

        start, track = max(started, key=lambda x: x[0])
        try:
            end = datetime.fromisoformat(track['enddatetime'])
        except (KeyError, TypeError, ValueError):
            end = start
        if now - max(start, end) > NPO_MAX_AGE:
            return None  # feed looks stale, let the other sources handle it
        return (track['artist'].strip(), track['title'].strip())

    except Exception as e:
        log_print(f"Error fetching {site} from its NPO API: {e}", Fore.YELLOW)
        return None

# Talpa stations embed their last ~24 hours of plays in their playlist page (Next.js page data)
TALPA_PLAYLIST_PAGES = {
    '538': 'https://www.538.nl/playlist/radio-538',
    'Sky Radio': 'https://www.skyradio.nl/playlist/sky-radio',
    'Radio 10': 'https://www.radio10.nl/playlist/radio-10',
    'Radio Noordzee': 'https://www.radionoordzee.nl/playlist/radio-noordzee',
}
TALPA_MAX_AGE = timedelta(minutes=30)  # plays are 3-17 min apart; older than this means the feed is stale

def fetch_station_from_talpa(station_name, url):
    """Fetch current song from a Talpa station's own playlist page (the broadcaster's feed)"""
    try:
        import json
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.S)
        if not match:
            return None
        groups = json.loads(match.group(1))['props']['pageProps']['initialPlaylist']

        # broadcastDate is UTC; "show" items are programme blocks, not songs
        now = datetime.now(ZoneInfo('UTC'))
        plays = []
        for group in groups:
            for item in group:
                if item.get('type') != 'playout':
                    continue
                try:
                    started = datetime.fromisoformat(item['broadcastDate'].replace('Z', '+00:00'))
                except (KeyError, ValueError):
                    continue
                track = item.get('track') or {}
                if started <= now and (track.get('artistName') or '').strip() and (track.get('title') or '').strip():
                    plays.append((started, track))
        if not plays:
            return None

        started, track = max(plays, key=lambda p: p[0])
        if now - started > TALPA_MAX_AGE:
            return None  # feed looks stale, let the other sources handle it
        return (track['artistName'].strip(), track['title'].strip())

    except Exception as e:
        log_print(f"Error fetching {station_name} from its own playlist page: {e}", Fore.YELLOW)
        return None

# Mediahuis Radio brands share one now-playing API (it has no timestamp, so no staleness check is possible)
MEDIAHUIS_STATIONS = {
    'Radio Veronica': 'veronica',
    'SLAM!': 'slam',
    '100% NL': '100pnl',
    'Sublime FM': 'sublime',
}

def fetch_station_from_mediahuis(station_name, station_key):
    """Fetch current song from Mediahuis Radio's now-playing API (the broadcaster's feed)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://api.mediahuisradio.nl/api/nowplaying', params={'stationKey': station_key},
                                timeout=15, headers=headers)
        response.raise_for_status()
        data = response.json()

        artist = (data.get('artist') or '').strip()
        title = (data.get('title') or '').strip()
        if not artist or not title:
            return None  # e.g. an ad break or an unknown station key
        return (artist, title)

    except Exception as e:
        log_print(f"Error fetching {station_name} from mediahuisradio.nl: {e}", Fore.YELLOW)
        return None

def fetch_radionl_from_site():
    """Fetch current song from radionl.fm's own playlist page (the 'Nu op RADIONL' block)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://radionl.fm/playlist', timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        artist_tag = soup.find(attrs={'data-np-artist': True})
        title_tag = soup.find(attrs={'data-np-title': True})
        if not artist_tag or not title_tag:
            return None
        artist, title = artist_tag.get_text(strip=True), title_tag.get_text(strip=True)
        if not artist or not title:
            return None
        return (artist, title)

    except Exception as e:
        log_print(f"Error fetching RadioNL from radionl.fm: {e}", Fore.YELLOW)
        return None

# Radio 8FM runs its own WordPress site; its player polls this open endpoint for the current song
RADIO8FM_URL = 'https://www.radio8fm.nl/wp-json/r8fm/v1/latest'
RADIO8FM_MAX_AGE = timedelta(minutes=30)  # songs are 3-5 min apart; older than this means the feed is stale

def fetch_radio8fm():
    """Fetch current song from Radio 8FM's own now-playing endpoint (the broadcaster's feed)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(RADIO8FM_URL, timeout=15, headers=headers)
        response.raise_for_status()
        data = response.json()

        artist = (data.get('artist') or '').strip()
        title = (data.get('title') or '').strip()
        if not artist or not title:
            return None

        # "timestamp" is when the song started, in Amsterdam local time
        try:
            started = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            now = datetime.now(ZoneInfo('Europe/Amsterdam')).replace(tzinfo=None)
            if now - started > RADIO8FM_MAX_AGE:
                return None  # feed looks stale, let the fallback handle it
        except (KeyError, TypeError, ValueError):
            pass
        return (artist, title)

    except Exception as e:
        log_print(f"Error fetching Radio 8FM from radio8fm.nl: {e}", Fore.YELLOW)
        return None

# Fallback for stations without a usable feed of their own: wathoorjewaar.nl lists the latest plays of an
# artist across all stations. Only target artists are covered, which is all we store anyway. Its robots.txt
# allows /artist/ pages; we poll gently (at most once per WATHOORJEWAAR_MIN_INTERVAL per artist page).
WATHOORJEWAAR_ARTIST_PAGES = {
    'Phil Collins': 'https://www.wathoorjewaar.nl/artist/phil-collins/',
    'Genesis': 'https://www.wathoorjewaar.nl/artist/genesis/',
}
WATHOORJEWAAR_STATIONS = {'Radio 8FM': 'Radio 8FM'}  # our station name -> the name they use
WATHOORJEWAAR_MIN_INTERVAL = 240  # seconds
WATHOORJEWAAR_MAX_AGE = timedelta(minutes=20)  # a play older than this is not "current"; the live loop would have seen it
WATHOORJEWAAR_HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; PhilCollinsDetector/1.0; +https://philcollinsdetector.nl)'}
_wathoorjewaar_state = {'fetched_at': 0.0, 'plays': []}

def fetch_recent_plays_from_wathoorjewaar():
    """[(started naive Amsterdam datetime, artist, title, station)] for the target artists, newest first.
    Cached for WATHOORJEWAAR_MIN_INTERVAL so the main loop can call this every cycle."""
    if time.time() - _wathoorjewaar_state['fetched_at'] < WATHOORJEWAAR_MIN_INTERVAL:
        return _wathoorjewaar_state['plays']
    _wathoorjewaar_state['fetched_at'] = time.time()  # also throttles retries after an error

    plays = []
    now = datetime.now(ZoneInfo('Europe/Amsterdam')).replace(tzinfo=None)
    for artist, url in WATHOORJEWAAR_ARTIST_PAGES.items():
        try:
            response = requests.get(url, timeout=15, headers=WATHOORJEWAAR_HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for table in soup.find_all('table'):
                for row in table.find_all('tr')[1:]:
                    cells = [td.get_text(' ', strip=True) for td in row.find_all('td')]
                    if len(cells) != 3:
                        continue
                    try:
                        # "09-10 09:05" = day-month hour:minute, no year
                        started = datetime.strptime(f"{now.year}-{cells[0]}", '%Y-%d-%m %H:%M')
                    except ValueError:
                        continue
                    if started > now + timedelta(days=1):
                        started = started.replace(year=now.year - 1)  # 31-12 read on 01-01
                    title = cells[1].replace('’', "'").replace('‘', "'")  # we store straight apostrophes
                    plays.append((started, artist, title, cells[2]))
        except Exception as e:
            log_print(f"Error fetching {artist} plays from wathoorjewaar.nl: {e}", Fore.YELLOW)
    plays.sort(key=lambda p: p[0], reverse=True)
    _wathoorjewaar_state['plays'] = plays
    return plays

def fetch_station_from_wathoorjewaar(station_name):
    """Newest recent play of a target artist on this station, if it is recent enough to be 'current'"""
    their_name = WATHOORJEWAAR_STATIONS.get(station_name)
    if not their_name:
        return None
    now = datetime.now(ZoneInfo('Europe/Amsterdam')).replace(tzinfo=None)
    for started, artist, title, station in fetch_recent_plays_from_wathoorjewaar():
        if station == their_name and now - started <= WATHOORJEWAAR_MAX_AGE:
            return (artist, title)
    return None

# DPG Media stations (JOE, Q-music) get their songs from a shared real-time server (SockJS).
# We join the "plays" feed with backlog=1 over SockJS's plain-HTTP transport, which returns the latest play.
DPG_SOCKET_URL = 'https://socket.qmusic.nl/api'
DPG_SOCKET_STATIONS = {
    'JOE': 'joe_nl',
    'Q Music': 'qmusic_nl',
}
DPG_MAX_AGE = timedelta(minutes=30)  # songs are 3-5 min apart; older than this means the feed is stale

def fetch_station_from_dpg_socket(station_name, station_key):
    """Fetch the latest play from DPG Media's real-time plays feed (the broadcaster's feed)"""
    try:
        import json
        import random
        import string
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        base = f"{DPG_SOCKET_URL}/{random.randint(100, 999)}/{session_id}"

        with requests.Session() as http:
            http.headers.update(headers)
            if not http.post(f"{base}/xhr", timeout=(5, 10)).text.startswith('o'):
                return None  # no SockJS "open" frame
            join = {"action": "join", "id": 0,
                    "sub": {"station": station_key, "entity": "plays", "action": "play"}, "backlog": 1}
            http.post(f"{base}/xhr_send", data=json.dumps([json.dumps(join)]), timeout=(5, 10))

            play = None
            deadline = time.time() + 10
            while play is None and time.time() < deadline:
                text = http.post(f"{base}/xhr", timeout=(5, 10)).text
                if not text.startswith('a['):
                    continue  # heartbeat frame, keep polling
                for frame in json.loads(text[1:]):
                    message = json.loads(frame)
                    if message.get('action') == 'data':
                        play = json.loads(message['data']).get('data')
        if not play:
            return None

        artist = play.get('artist')
        artist = (artist.get('name') if isinstance(artist, dict) else artist) or ''
        artist, title = artist.strip(), (play.get('title') or '').strip()
        if not artist or not title:
            return None

        # played_at carries a UTC offset
        try:
            played_at = datetime.fromisoformat(play['played_at'])
            if datetime.now(played_at.tzinfo) - played_at > DPG_MAX_AGE:
                return None  # feed looks stale, let the other sources handle it
        except (KeyError, TypeError, ValueError):
            pass
        return (artist, title)

    except Exception as e:
        log_print(f"Error fetching {station_name} from the DPG plays feed: {e}", Fore.YELLOW)
        return None

def fetch_arrow_from_arrow_nl():
    """Fetch current song from arrow.nl's own now-playing API (the broadcaster's feed)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://www.arrow.nl/api/nowplaying', timeout=15, headers=headers)
        response.raise_for_status()
        data = response.json()

        artist = (data.get('artist') or '').strip()
        title = (data.get('title') or '').strip()
        if not data.get('hasCurrentTrack', True) or not artist or not title:
            return None
        return (artist, title)

    except Exception as e:
        log_print(f"Error fetching Arrow Classic Rock from arrow.nl: {e}", Fore.YELLOW)
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
        
        # Dict to store station -> (artist, song, source) mapping
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
            
            # Store the station data with source
            stations_data[station_name] = (artist, song, 'relisten.nl')
        
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
    log_print(f"- Tracked songs (separate table): {', '.join(TRACKED_SONGS) if TRACKED_SONGS else 'None'}")
    log_print("=" * 60)
    
    # Create database cursor
    c = conn.cursor()
    
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
                db.execute_query(c, "SELECT MAX(updated_at) FROM settings", db_type=db_type)
                latest_update = c.fetchone()[0]
                if last_settings_check is None:
                    last_settings_check = latest_update
                elif latest_update and latest_update != last_settings_check:
                    log_print("Detected settings change, reloading configuration...", Fore.YELLOW)
                    reload_settings()
                    last_settings_check = latest_update
            
            stations_data = {}
            relisten_failed = False
            
            # Arrow Classic Rock: the station's own API is fresher than the aggregator sites
            arrow_name = 'Arrow Classic Rock'
            if arrow_name in RELISTEN_STATIONS or arrow_name in ALL_MYONLINERADIO_STATIONS or arrow_name in ALL_PLAYLIST24_STATIONS:
                result = fetch_arrow_from_arrow_nl()
                if result:
                    stations_data[arrow_name] = (result[0], result[1], 'arrow.nl')

            # NPO stations: their own tracks API, same idea as Arrow
            for npo_name, site in NPO_STATION_SITES.items():
                if npo_name in RELISTEN_STATIONS or npo_name in ALL_MYONLINERADIO_STATIONS or npo_name in ALL_PLAYLIST24_STATIONS:
                    result = fetch_station_from_npo(site)
                    if result:
                        stations_data[npo_name] = (result[0], result[1], f'{site}.nl')

            # Talpa stations (538, Sky Radio, Radio 10, Radio Noordzee): their own playlist pages
            for talpa_name, page_url in TALPA_PLAYLIST_PAGES.items():
                if talpa_name in RELISTEN_STATIONS or talpa_name in ALL_MYONLINERADIO_STATIONS or talpa_name in ALL_PLAYLIST24_STATIONS:
                    result = fetch_station_from_talpa(talpa_name, page_url)
                    if result:
                        stations_data[talpa_name] = (result[0], result[1], page_url.split('/')[2].removeprefix('www.'))

            # Mediahuis Radio stations (Veronica, SLAM!, 100% NL, Sublime FM): their own now-playing API
            for mh_name, station_key in MEDIAHUIS_STATIONS.items():
                if mh_name in RELISTEN_STATIONS or mh_name in ALL_MYONLINERADIO_STATIONS or mh_name in ALL_PLAYLIST24_STATIONS:
                    result = fetch_station_from_mediahuis(mh_name, station_key)
                    if result:
                        stations_data[mh_name] = (result[0], result[1], 'mediahuisradio.nl')

            # RadioNL: its own playlist page
            radionl_name = 'RadioNL'
            if radionl_name in RELISTEN_STATIONS or radionl_name in ALL_MYONLINERADIO_STATIONS or radionl_name in ALL_PLAYLIST24_STATIONS:
                result = fetch_radionl_from_site()
                if result:
                    stations_data[radionl_name] = (result[0], result[1], 'radionl.fm')

            # Radio 8FM: its own now-playing endpoint, with wathoorjewaar.nl as fallback for target artists
            radio8fm_name = 'Radio 8FM'
            if radio8fm_name in RELISTEN_STATIONS or radio8fm_name in ALL_MYONLINERADIO_STATIONS or radio8fm_name in ALL_PLAYLIST24_STATIONS:
                result = fetch_radio8fm()
                if result:
                    stations_data[radio8fm_name] = (result[0], result[1], 'radio8fm.nl')
                else:
                    result = fetch_station_from_wathoorjewaar(radio8fm_name)
                    if result:
                        stations_data[radio8fm_name] = (result[0], result[1], 'wathoorjewaar.nl')

            # DPG Media stations (JOE, Q-music): their own real-time plays feed
            for dpg_name, station_key in DPG_SOCKET_STATIONS.items():
                if dpg_name in RELISTEN_STATIONS or dpg_name in ALL_MYONLINERADIO_STATIONS or dpg_name in ALL_PLAYLIST24_STATIONS:
                    result = fetch_station_from_dpg_socket(dpg_name, station_key)
                    if result:
                        stations_data[dpg_name] = (result[0], result[1], 'socket.qmusic.nl')

            # PRIORITY STATIONS: Fetch from myonlineradio FIRST for stations that need it
            # (e.g., Radio 538 which is not reliably on relisten.nl homepage)
            if PRIORITY_MYONLINERADIO and ALL_MYONLINERADIO_STATIONS:
                for station_name in PRIORITY_MYONLINERADIO:
                    if station_name in stations_data:
                        continue  # already have data from a better source
                    if station_name in ALL_MYONLINERADIO_STATIONS:
                        slug = ALL_MYONLINERADIO_STATIONS[station_name]
                        result = fetch_station_from_myonlineradio(slug)
                        if result:
                            stations_data[station_name] = (result[0], result[1], 'myonlineradio.nl')
                        else:
                            log_print(f"Warning: no now-playing data for priority station {station_name} on myonlineradio.nl", Fore.YELLOW)

            # Fetch from relisten.nl (homepage scraping)
            if RELISTEN_STATIONS:
                relisten_data = fetch_all_stations_from_relisten()
                if relisten_data:
                    # Priority stations already fetched from myonlineradio keep that data:
                    # relisten can show stale songs (e.g. Arrow Classic Rock: months old)
                    for station_name, data in relisten_data.items():
                        stations_data.setdefault(station_name, data)
                else:
                    relisten_failed = True
                    log_print("Warning: relisten.nl returned no data, falling back to other sources", Fore.YELLOW)
            
            # Fetch from myonlineradio.nl (individual station playlists)
            # Always consider ALL myonlineradio stations: anything relisten did not deliver
            # (failed fetch or rotated off its homepage) is fetched here, the rest is skipped below
            myonline_stations_to_check = ALL_MYONLINERADIO_STATIONS
            
            if myonline_stations_to_check:
                for station_name, slug in myonline_stations_to_check.items():
                    # Skip if already fetched from relisten (avoid duplicates)
                    if station_name in stations_data:
                        continue
                    
                    result = fetch_station_from_myonlineradio(slug)
                    if result:
                        stations_data[station_name] = (result[0], result[1], 'myonlineradio.nl')
            
            # Fetch from playlist24.nl (individual station playlists)
            # Same per-station fallback: only stations still missing after the other sources are fetched
            playlist24_stations_to_check = ALL_PLAYLIST24_STATIONS
            
            if playlist24_stations_to_check:
                for station_name, slug in playlist24_stations_to_check.items():
                    # Skip if already fetched from other sources (avoid duplicates)
                    if station_name in stations_data:
                        continue
                    
                    result = fetch_station_from_playlist24(slug)
                    if result:
                        stations_data[station_name] = (result[0], result[1], 'playlist24.nl')
            
            if not stations_data:
                log_print(f"Warning: No station data retrieved from any source", Fore.RED)
                time.sleep(60)
                continue
            
            # Track if any songs changed in this iteration
            songs_changed = 0
            
            # Process each station
            for station in sorted(stations_data.keys()):
                artist, song, source = stations_data[station]

                if song and artist:
                    
                    # Normalize song title (remove patterns like "#742: ")
                    normalized_song = normalize_song_title(song)
                    normalized_artist = normalize_song_title(artist)

                    # Some stations report title first; swap if only the swapped order hits a target
                    if (station in SWAPPED_ORDER_STATIONS
                            and not matches_target(normalized_artist, normalized_song)
                            and matches_target(normalized_song, normalized_artist)):
                        artist, song = song, artist
                        normalized_artist, normalized_song = normalized_song, normalized_artist

                    normalized_song_info = f"{normalized_artist} - {normalized_song}"

                    # Create a unique key to detect if this is the same song (handles ordering issues)
                    song_key = create_song_key(artist, song)

                    # Check if this is different from last known song (using song key)
                    if station not in last_songs or last_songs[station] != song_key:
                        ts = get_timestamp()
                        last_songs[station] = song_key
                        songs_changed += 1

                        # Side-project songs (e.g. Toto - Africa) go to their own table, so they
                        # never show up in the Phil Collins / Genesis statistics
                        if matches_song_list(TRACKED_SONGS, normalized_artist, normalized_song):
                            db.execute_query(c, "INSERT INTO tracked_songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                                      (station, normalized_song, normalized_artist, datetime.now().isoformat()), db_type)
                            conn.commit()
                            log_print(f"[{ts}] {station}: {normalized_song_info} (tracked, via {source})", Fore.MAGENTA)
                            upload_database()
                            continue

                        # Check if artist is in target list
                        matched = False
                        for target_artist in TARGET_ARTISTS:
                            if target_artist == "Phil Collins" and target_artist.lower() in normalized_artist.lower():
                                matched = True
                                # Normalize artist if 'bailey' is present
                                if 'bailey' in normalized_artist.lower():
                                    normalized_artist = "Phil Collins & Philip Bailey"
                                else:
                                    normalized_artist = "Phil Collins"
                                break
                            if target_artist == "Genesis" and target_artist.lower() == normalized_artist.lower():
                                matched = True
                                break

                        # Check if song is in target list ('Artist - Title' entries must match the artist too)
                        if not matched:
                            matched = matches_song_list(TARGET_SONGS, normalized_artist, normalized_song)

                        # Log to database and print if matched
                        if matched:
                            # Log to database (store normalized song title)
                            timestamp = datetime.now().isoformat()
                            db.execute_query(c, "INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                                      (station, normalized_song, normalized_artist, timestamp), db_type)
                            conn.commit()
                            # Print with red warning and timestamp
                            log_print("=" * 60, Fore.RED, Style.BRIGHT)
                            log_print(f"[{ts}] {station}: {normalized_song_info} (via {source})", Fore.RED, Style.BRIGHT)

                            # Upload database to web server after new detection
                            upload_database()
                            log_print("=" * 60, Fore.RED, Style.BRIGHT)
                            # Beep to alert user (works on Windows and Linux)
                            print('\a', end='', flush=True)

                        else:
                            # Print normally for non-matching songs
                            log_print(f"[{ts}] {station}: {normalized_song_info} (via {source})")
            
            # Print status message
            if songs_changed == 0:
                ts = get_timestamp()
                log_print(f"[{ts}] No song changes detected", Fore.CYAN)
            
            # Wait 60 seconds before next check
            log_print("-" * 60, Fore.CYAN)
            log_print("Waiting 60 seconds to update the list again...", Fore.CYAN)
            log_print("-" * 60, Fore.CYAN)
            time.sleep(60)
    
    except KeyboardInterrupt:
        log_print("\n\nShutting down...")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "testmyradiosel":
        station_slug = sys.argv[2]
        print(f"Testing Selenium for slug: {station_slug}")
        result = fetch_station_from_myonlineradio_selenium(station_slug)
        print("Result:", result)
    else:
        main()