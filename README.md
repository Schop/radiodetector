# Radio Checker

A Python script that monitors Dutch radio stations for songs by target artists (Phil Collins, Genesis), storing detected songs in a SQLite database with red console alerts.

## Features

- **Real-time monitoring** of 19 Dutch radio stations via [relisten.nl](https://www.relisten.nl) aggregator
- **Target artist detection** with red terminal alerts when Phil Collins or Genesis songs are played
- **SQLite database** logging all detected target artist songs with timestamps
- **Pi Zero compatible** - No Selenium/Chromium, just pure Python libraries
- **Efficient** - Fetches all stations in ~100-200ms per cycle

## Supported Radio Stations

The script monitors 19 stations from relisten.nl:

1. SLAM!
2. 538
3. NPO 3FM
4. Q-MUSIC
5. 100% NL
6. Sky Radio
7. Radio Veronica
8. Radio 10
9. Juize
10. FunX
11. Arrow Caz
12. Arrow Classic Rock
13. RadioNL
14. Simone FM
15. NPO Radio 1
16. Sublime FM
17. Radio Decibel
18. NPO Radio 2
19. WILD FM Hitradio

## Installation

1. Clone or download the project
2. Install Python 3.12+
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```bash
python main.py
```

The script will:
- Display current songs every minute for each station
- Alert in red when a target artist (Phil Collins/Genesis) is detected
- Log all target artist songs to `radio_songs.db` with timestamps

## Database

The SQLite database `radio_songs.db` stores detected target songs in a `songs` table:

| Column    | Type    | Description                              |
|-----------|---------|------------------------------------------|
| id        | INTEGER | Primary key                              |
| station   | TEXT    | Radio station name                       |
| song      | TEXT    | Song title                               |
| artist    | TEXT    | Artist name                              |
| timestamp | TEXT    | ISO format timestamp of detection        |

## How It Works

1. **Fetch playlists** (~100-200ms):
   - Fetches the relisten.nl homepage displaying real-time playlists for 19 stations
   - Parses HTML to extract current song information (artist + title)
   - Returns {station_name: (artist, song)} dictionary

2. **Detect changes**:
   - Compares with previous songs to avoid spam
   - Only processes new songs

3. **Check target artists**:
   - Searches for "Phil Collins" and "Genesis" (case-insensitive)
   - If found: logs to database and prints red alert

4. **Loop**: Waits 60 seconds and repeats

## Technology Stack

- **Python 3.12** (or 3.9+ for older systems like Raspberry Pi Zero)
- **requests** - HTTP library for fetching relisten.nl
- **BeautifulSoup4** - HTML parsing
- **sqlite3** - Built-in database
- **colorama** - Cross-platform colored terminal output

**Total dependencies: 3 lightweight pure-Python packages** (no Selenium, no Chromium, no JavaScript rendering)

