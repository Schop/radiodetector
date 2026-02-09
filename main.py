import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
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
    """Main loop - Monitor Dutch radio stations for target artists"""
    print("Initializing radio checker...")
    print("- Monitoring 19 stations from relisten.nl")
    print("- Logging Phil Collins and Genesis songs")
    print("=" * 60)
    
    # Track the last song played on each station to detect changes
    last_songs = {}
    
    try:
        while True:
            # Fetch all real-time playlist data
            stations_data = fetch_all_stations_from_relisten()
            
            if not stations_data:
                print("Warning: No station data retrieved")
                time.sleep(60)
                continue
            
            # Process each station
            for station in sorted(stations_data.keys()):
                artist, song = stations_data[station]
                
                if song and artist:
                    # Create song info string
                    song_info = f"{artist} - {song}"
                    
                    # Check if this is different from last known song
                    if station not in last_songs or last_songs[station] != song_info:
                        print(f"[{station}] Now playing: {song_info}")
                        last_songs[station] = song_info
                        
                        # Check if artist is in target list
                        for target_artist in TARGET_ARTISTS:
                            if target_artist.lower() in artist.lower():
                                # Log to database
                                timestamp = datetime.now().isoformat()
                                c.execute("INSERT INTO songs (station, song, artist, timestamp) VALUES (?, ?, ?, ?)",
                                          (station, song, artist, timestamp))
                                conn.commit()
                                
                                # Print with red warning
                                print(f"{Fore.RED}{Style.BRIGHT}>>> FOUND TARGET ARTIST: {artist} - {song} on {station}{Style.RESET_ALL}")
                                break
            
            # Wait 60 seconds before next check
            time.sleep(60)
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        conn.close()

if __name__ == '__main__':
    main()