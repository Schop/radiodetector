# Radio Checker

A Python script that monitors Dutch radio stations for songs by target artists (Phil Collins, Genesis), storing detected songs in a SQLite database with red console alerts.

## Features

- **Real-time monitoring** of 40 Dutch radio stations via [relisten.nl](https://www.relisten.nl) (primary) or 99 stations via [myonlineradio.nl](https://myonlineradio.nl) (fallback)
- **Automatic fallback** - Switches to myonlineradio.nl when relisten.nl is unavailable
- **Configurable stations** - Easy-to-edit JSON file for station mappings
- **Target artist detection** with red terminal alerts when Phil Collins or Genesis songs are played
- **SQLite database** logging all detected target artist songs with timestamps
- **Pi Zero compatible** - No Selenium/Chromium, just pure Python libraries
- **Efficient** - Fetches all stations in ~100-200ms per cycle

## Configuration

### Station Mappings

Station configurations are stored in [`config.yaml`](config.yaml):

```yaml
# Comment out stations with # to disable them
relisten:
  Veronica: veronica
  Radio 10: radio10
  # Juize: juize    # Disabled

myonlineradio:
  Radio 10: radio-10
  Sky Radio: sky-radio
  
priority_stations:
  - Radio 10
  - Sky Radio
```

**To disable any station:** Just add `#` at the start of the line  
**To re-enable:** Remove the `#`

See [STATIONS.md](STATIONS.md) for detailed documentation.

## Supported Radio Stations

**Primary source (relisten.nl):** 40 stations including SLAM!, 538, NPO 3FM, Q-music, 100% NL, Sky Radio, Radio Veronica, Radio 10, KINK, Joe, and many more.

**Fallback source (myonlineradio.nl):** 99 stations including all major Dutch national stations plus regional and specialty stations.

## Installation

1. Clone or download the project
2. Install Python 3.12+
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Start the Radio Detector (Background)

Run in a terminal:
```bash
python main.py
```

The script will:
- Display current songs every minute for each station
- Alert in red when a target artist (Phil Collins/Genesis) is detected
- Log all target artist songs to `radio_songs.db` with timestamps

### 2. View Results via Web Dashboard (Optional)

While `main.py` runs, start the Flask web server in another terminal:
```bash
python web_app.py
```

Then open your browser:
- Local: **http://localhost:5000**
- From another machine (Pi): **http://<your-pi-ip>:5000**

The dashboard shows:
- 📊 Total detections and unique stations
- 🎵 Full song history with filters
- 🔍 Filter by station or date range
- 📥 Export to CSV
- ✨ Auto-refresh every 60 seconds

## Database

The SQLite database `radio_songs.db` stores detected target songs in a `songs` table:

| Column    | Type    | Description                              |
|-----------|---------|------------------------------------------|
| id        | INTEGER | Primary key                              |
| station   | TEXT    | Radio station name                       |
| song      | TEXT    | Song title                               |
| artist    | TEXT    | Artist name                              |
| timestamp | TEXT    | ISO format timestamp of detection        |

## Project Structure

```
radiochecker/
├── main.py                 # Radio detector daemon
├── web_app.py              # Flask web dashboard
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── radio_songs.db         # SQLite database (auto-created)
└── templates/
    └── index.html         # Web dashboard template
```

## Running on Raspberry Pi Zero

On your Pi, you can run both services in tmux sessions:

```bash
# Terminal 1: Start radio detector
tmux new-session -d -s detector "cd ~/radiochecker && python main.py"

# Terminal 2: Start web dashboard
tmux new-session -d -s dashboard "cd ~/radiochecker && python web_app.py"

# View sessions
tmux list-sessions

# Connect to detector output
tmux attach-session -t detector

# Stop both
tmux kill-session -t detector
tmux kill-session -t dashboard
```

Or as background services with `nohup`:

```bash
nohup python main.py > detector.log 2>&1 &
nohup python web_app.py > dashboard.log 2>&1 &
```

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

- **Python 3.12** (or 3.9+ for Raspberry Pi Zero)
- **requests** - HTTP library for fetching relisten.nl
- **BeautifulSoup4** - HTML parsing
- **flask** - Lightweight web framework
- **Inline CSS** - Minimal styling (no external dependencies)
- **sqlite3** - Built-in database
- **colorama** - Cross-platform colored terminal output

**Total dependencies: 4 lightweight pure-Python packages** (no Selenium, no Chromium, no JavaScript rendering, no external CSS)

