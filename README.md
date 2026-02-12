# Radio Checker

A Python script that monitors Dutch radio stations for songs by target artists (Phil Collins, Genesis), storing detected songs in a SQLite database with red console alerts.

## Features

- **Real-time monitoring** of 40 Dutch radio stations via [relisten.nl](https://www.relisten.nl) (primary), 18 stations via [myonlineradio.nl](https://myonlineradio.nl) (secondary fallback), or 13 stations via [playlist24.nl](https://playlist24.nl) (tertiary fallback)
- **Triple fallback system** - Automatically switches between sources when unavailable
- **Configurable stations** - Easy-to-edit YAML file for station mappings and target artists/songs
- **Target artist & song detection** with red terminal alerts and beep when matches are found
- **SQLite database** logging all detected target artist songs with timestamps
- **Pi Zero compatible** - No Selenium/Chromium, just pure Python libraries
- **Efficient** - Fetches all stations in ~100-200ms per cycle

## Configuration

### Initial Setup

Before running the application, copy the example configuration:
```bash
cp config.yaml.example config.yaml
```

Then edit `config.yaml` with your preferred settings.

### Station Mappings

Station configurations are stored in `config.yaml`:

```yaml
# Comment out stations with # to disable them

# Target artists and songs to check
target_artists:
  - Phil Collins
  - Genesis

target_songs:
  - Africa

relisten:
  Veronica: veronica
  Radio 10: radio10
  # Juize: juize    # Disabled

myonlineradio:
  Radio 10: radio-10
  Sky Radio: sky-radio

playlist24:
  KINK: kink-playlist
  NPO 3FM: 3fm-playlist
```

**To disable any station:** Just add `#` at the start of the line  
**To re-enable:** Remove the `#`

See [STATIONS.md](STATIONS.md) for detailed documentation.

## Supported Radio Stations

**Primary source (relisten.nl):** 14 stations including SLAM!, 538, NPO 3FM, Q-music, 100% NL, Sky Radio, Radio Veronica, Radio 10, FunX, Arrow Classic Rock, RadioNL, NPO Radio 1, and NPO Radio 2.

**Secondary fallback (myonlineradio.nl):** 18 stations including all major Dutch national stations plus regional and specialty stations.

**Tertiary fallback (playlist24.nl):** 13 stations including 3FM Alternative, Aardschok, Arrow Classic Rock, KINK, NPO 3FM, NPO Radio 1, and more.

## Installation

1. Clone or download the project
2. Install Python 3.12+
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up configuration:**
   ```bash
   # Copy the example config file
   cp config.yaml.example config.yaml
   
   # Edit config.yaml with your settings
   # For SQLite (default): No changes needed
   # For MySQL: Update database credentials
   ```
   
   ⚠️ **Important:** `config.yaml` contains credentials and is excluded from git. Never commit it!

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
- ✨ **Real-time updates**: Data refreshes every 30 seconds, page reloads every 10 minutes

## Database

The SQLite database `radio_songs.db` stores detected target songs in a `songs` table:

| Column    | Type    | Description                              |
|-----------|---------|------------------------------------------|
| id        | INTEGER | Primary key                              |
| station   | TEXT    | Radio station name                       |
| song      | TEXT    | Song title                               |
| artist    | TEXT    | Artist name                              |
| timestamp | TEXT    | ISO format timestamp of detection        |

### Automatic Upload to Web Server

When a target song is detected, both the database and web application files are automatically uploaded to the web server via SFTP. This ensures the web dashboard stays synchronized with the latest detections and any code changes.

**Features:**
- ✅ Only uploads database when it has actually changed (hash-based)
- 🔄 Web files uploaded with every database upload (ensures latest code)
- 📊 Web dashboard updates immediately after new detections
- 📝 Upload logs saved to `upload.log`

**Configuration:** Copy `upload_db.py.example` to `upload_db.py` and add your SFTP credentials.

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

