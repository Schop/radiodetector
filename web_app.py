"""
Simple Flask web interface for RadioDetector
Displays detected Phil Collins and Genesis songs from SQLite database
Lightweight and Pi Zero friendly
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
import platform
import json

app = Flask(__name__)
DB_PATH = 'radio_songs.db'
LOG_FILE = 'radio.log'
UPTIME_FILE = '.uptime'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(key, default=None):
    """Get a setting value from database"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['value'])
        return default
    except:
        return default

def parse_iso_timestamp(iso_string):
    """Parse ISO format timestamp"""
    try:
        return datetime.fromisoformat(iso_string)
    except:
        return None

@app.route('/')
def index():
    """Main page - display all detected songs"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all songs (DataTables will handle filtering client-side)
    c.execute("SELECT * FROM songs ORDER BY timestamp DESC LIMIT 1000")
    songs = c.fetchall()
    
    # Get unique stations
    c.execute("SELECT DISTINCT station FROM songs ORDER BY station")
    stations = [row['station'] for row in c.fetchall()]
    
    conn.close()
    
    # Convert timestamps to readable format
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song['timestamp'])
        # Format: "10:46, 2 Feb 2026" (use %#d for Windows, %d and strip for others)
        if ts:
            ts_formatted = ts.strftime('%d %b %Y at %H:%M').replace(' 0', ' ')
        else:
            ts_formatted = song['timestamp']
        songs_data.append({
            'station': song['station'],
            'artist': song['artist'],
            'song': song['song'],
            'timestamp': ts_formatted,
            'timestamp_raw': song['timestamp']
        })
    
    # Get target artists and songs from database
    target_artists = get_setting('target_artists', [])
    target_songs = get_setting('target_songs', [])
    
    return render_template(
        'index.html',
        target_artists=target_artists,
        target_songs=target_songs,
        songs=songs_data,
        stations=stations,
        total_count=len(songs_data)
    )

@app.route('/station/<station_name>')
def station_detail(station_name):
    """Station detail page - show all songs detected from this station"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all songs from this station
    c.execute("SELECT * FROM songs WHERE station = ? ORDER BY timestamp DESC", (station_name,))
    songs = c.fetchall()
    
    # Get total count
    total_songs = len(songs)
    
    # Get unique artists from this station
    c.execute("SELECT DISTINCT artist FROM songs WHERE station = ? ORDER BY artist", (station_name,))
    artists = [row['artist'] for row in c.fetchall()]
    
    # Get unique song titles from this station
    c.execute("SELECT DISTINCT song FROM songs WHERE station = ? ORDER BY song", (station_name,))
    song_titles = [row['song'] for row in c.fetchall()]
    
    conn.close()
    
    # Format timestamps
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song['timestamp'])
        if ts:
            ts_formatted = ts.strftime('%d %b %Y at %H:%M').replace(' 0', ' ')
        else:
            ts_formatted = song['timestamp']
        songs_data.append({
            'station': song['station'],
            'artist': song['artist'],
            'song': song['song'],
            'timestamp': ts_formatted,
            'timestamp_raw': song['timestamp']
        })
    
    return render_template(
        'station.html',
        station_name=station_name,
        songs=songs_data,
        total_songs=total_songs,
        artists=artists,
        song_titles=song_titles,
        title = f"Station: {station_name}"
    )

@app.route('/song/<path:song_name>')
def song_detail(song_name):
    """Song detail page - show all stations that played this song"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all detections of this song
    c.execute("SELECT * FROM songs WHERE song = ? ORDER BY timestamp DESC", (song_name,))
    songs = c.fetchall()
    
    # Get total count
    total_detections = len(songs)
    
    # Get stations that played this song with counts
    c.execute("""
        SELECT station, COUNT(*) as count 
        FROM songs 
        WHERE song = ? 
        GROUP BY station 
        ORDER BY count DESC
    """, (song_name,))
    stations_data = c.fetchall()
    
    # Get unique artists who performed this song
    c.execute("SELECT DISTINCT artist FROM songs WHERE song = ? ORDER BY artist", (song_name,))
    artists = [row['artist'] for row in c.fetchall()]
    
    conn.close()
    
    # Format timestamps
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song['timestamp'])
        if ts:
            ts_formatted = ts.strftime('%d %b %Y at %H:%M').replace(' 0', ' ')
        else:
            ts_formatted = song['timestamp']
        songs_data.append({
            'station': song['station'],
            'artist': song['artist'],
            'song': song['song'],
            'timestamp': ts_formatted,
            'timestamp_raw': song['timestamp']
        })
    
    # Prepare station chart data
    stations_list = [{'station': row['station'], 'count': row['count']} for row in stations_data]
    
    return render_template(
        'song.html',
        song_name=song_name,
        songs=songs_data,
        total_detections=total_detections,
        artists=artists,
        stations=stations_list,
        title=f"Song: {song_name}"
    )

@app.route('/api/stats')
def stats():
    """JSON API for statistics"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Total songs detected
    c.execute("SELECT COUNT(*) as count FROM songs")
    total = c.fetchone()['count']
    
    # Songs per station
    c.execute("SELECT station, COUNT(*) as count FROM songs GROUP BY station ORDER BY count DESC")
    by_station = {row['station']: row['count'] for row in c.fetchall()}
    
    # Last detection
    c.execute("SELECT timestamp FROM songs ORDER BY timestamp DESC LIMIT 1")
    last_detection = c.fetchone()
    
    conn.close()
    
    return {
        'total_songs': total,
        'by_station': by_station,
        'last_detection': last_detection['timestamp'] if last_detection else None
    }

@app.route('/api/chart-data')
def chart_data():
    """JSON API for chart data (lightweight for Pi Zero)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Songs per station (top 10)
    c.execute("""
        SELECT station, COUNT(*) as count 
        FROM songs 
        GROUP BY station 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stations_data = c.fetchall()
    
    # Songs by hour of day
    c.execute("SELECT timestamp FROM songs")
    all_songs = c.fetchall()
    
    hours = [0] * 24
    days_of_week = [0] * 7
    days_count = {}
    
    for row in all_songs:
        ts = parse_iso_timestamp(row['timestamp'])
        if ts:
            # Hour distribution
            hours[ts.hour] += 1
            
            # Day of week (0=Monday, 6=Sunday)
            days_of_week[ts.weekday()] += 1
            
            # Daily count
            date_key = ts.strftime('%Y-%m-%d')
            days_count[date_key] = days_count.get(date_key, 0) + 1
    
    # Get last 14 days for timeline
    sorted_days = sorted(days_count.items(), reverse=True)[:14]
    sorted_days.reverse()  # Oldest to newest
    
    conn.close()
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return {
        'stations': {
            'labels': [row['station'] for row in stations_data],
            'data': [row['count'] for row in stations_data]
        },
        'hours': {
            'labels': [f"{h}:00" for h in range(24)],
            'data': hours
        },
        'weekdays': {
            'labels': day_names,
            'data': days_of_week
        },
        'timeline': {
            'labels': [day[0] for day in sorted_days],
            'data': [day[1] for day in sorted_days]
        }
    }

@app.route('/api/station/<station_name>/charts')
def station_charts(station_name):
    """Get chart data for a specific station (hourly and weekday distribution)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all timestamps for this station
    c.execute("SELECT timestamp FROM songs WHERE station = ?", (station_name,))
    songs = c.fetchall()
    conn.close()
    
    # Count by hour and weekday
    hours = [0] * 24
    weekdays = [0] * 7
    
    for row in songs:
        ts = parse_iso_timestamp(row['timestamp'])
        if ts:
            hours[ts.hour] += 1
            weekdays[ts.weekday()] += 1
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return jsonify({
        'hourly': {
            'labels': [f"{h}:00" for h in range(24)],
            'data': hours
        },
        'weekdays': {
            'labels': day_names,
            'data': weekdays
        }
    })

@app.route('/api/song/<path:song_name>/charts')
def song_charts(song_name):
    """Get chart data for a specific song (hourly and weekday distribution)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all timestamps for this song
    c.execute("SELECT timestamp FROM songs WHERE song = ?", (song_name,))
    songs = c.fetchall()
    conn.close()
    
    # Count by hour and weekday
    hours = [0] * 24
    weekdays = [0] * 7
    
    for row in songs:
        ts = parse_iso_timestamp(row['timestamp'])
        if ts:
            hours[ts.hour] += 1
            weekdays[ts.weekday()] += 1
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return jsonify({
        'hourly': {
            'labels': [f"{h}:00" for h in range(24)],
            'data': hours
        },
        'weekdays': {
            'labels': day_names,
            'data': weekdays
        }
    })

@app.route('/api/export')
def export_csv():
    """Export songs as CSV"""
    from flask import send_file
    import csv
    import io
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT station, artist, song, timestamp FROM songs ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Station', 'Artist', 'Song', 'Detected At'])
    for row in rows:
        writer.writerow([row['station'], row['artist'], row['song'], row['timestamp']])
    
    # Convert to bytes
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=radiodetector_songs.csv'}
    )

@app.route('/api/logs')
def get_logs():
    """Get recent log entries"""
    lines = request.args.get('lines', 100, type=int)
    
    # Try to read from log file
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                # Read all lines and get the last N
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:]
                return jsonify({
                    'success': True,
                    'logs': ''.join(recent_lines),
                    'line_count': len(recent_lines)
                })
        else:
            return jsonify({
                'success': False,
                'error': 'Log file not found. Make sure main.py is running.'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error reading log file: {str(e)}'
        })

@app.route('/logs')
def logs_page():
    """Display logs page"""
    return render_template('logs.html')

@app.route('/api/uptime')
def get_uptime():
    """Get uptime of radio checker service"""
    try:
        if os.path.exists(UPTIME_FILE):
            with open(UPTIME_FILE, 'r') as f:
                start_time_str = f.read().strip()
                start_time = datetime.fromisoformat(start_time_str)
                uptime = datetime.now() - start_time
                
                # Format uptime
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                if days > 0:
                    uptime_str = f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    uptime_str = f"{hours}h {minutes}m"
                else:
                    uptime_str = f"{minutes}m {seconds}s"
                
                return jsonify({
                    'success': True,
                    'uptime': uptime_str,
                    'start_time': start_time_str
                })
        else:
            return jsonify({
                'success': False,
                'uptime': 'Unknown',
                'error': 'Service not running'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'uptime': 'Error',
            'error': str(e)
        })

@app.route('/admin')
def admin_page():
    """Database maintenance page - browse, edit, delete entries"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all songs (DataTables will handle filtering/pagination client-side)
    c.execute("SELECT * FROM songs ORDER BY timestamp DESC")
    songs = c.fetchall()
    
    conn.close()
    
    # Convert timestamps to readable format
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song['timestamp'])
        # Format: "10 Feb 2026 at 14:30" (use %#d for Windows, %d and strip for others)
        if ts:
            ts_formatted = ts.strftime('%d %b %Y at %H:%M').replace(' 0', ' ')
        else:
            ts_formatted = song['timestamp']
        songs_data.append({
            'id': song['id'],
            'station': song['station'],
            'artist': song['artist'],
            'song': song['song'],
            'timestamp': ts_formatted,
            'timestamp_raw': song['timestamp']
        })
    
    return render_template(
        'maintenance.html',
        songs=songs_data
    )

@app.route('/api/delete/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    """Delete a song entry"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Song ID {song_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/edit/<int:song_id>', methods=['POST'])
def edit_song(song_id):
    """Edit a song entry"""
    try:
        data = request.get_json()
        station = data.get('station')
        artist = data.get('artist')
        song = data.get('song')
        timestamp = data.get('timestamp')
        
        if not all([station, artist, song, timestamp]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE songs 
            SET station = ?, artist = ?, song = ?, timestamp = ?
            WHERE id = ?
        """, (station, artist, song, timestamp, song_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Song ID {song_id} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/settings')
def settings_page():
    """Settings management page"""
    import json
    conn = get_db_connection()
    c = conn.cursor()
    
    # Load simple settings from settings table
    settings = {}
    settings_keys = ['target_artists', 'target_songs', 'priority_myonlineradio']
    
    for key in settings_keys:
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        if row:
            try:
                settings[key] = json.loads(row['value'])
            except json.JSONDecodeError:
                settings[key] = []
        else:
            settings[key] = []
    
    # Load stations from stations table
    c.execute("SELECT id, name, slug, source, enabled, priority FROM stations ORDER BY source, name")
    stations_rows = c.fetchall()
    
    # Organize stations by source
    stations_by_source = {
        'relisten': [],
        'myonlineradio': [],
        'playlist24': []
    }
    
    for row in stations_rows:
        station = {
            'id': row['id'],
            'name': row['name'],
            'slug': row['slug'],
            'source': row['source'],
            'enabled': bool(row['enabled']),
            'priority': bool(row['priority'])
        }
        stations_by_source[row['source']].append(station)
    
    conn.close()
    
    return render_template('settings.html', settings=settings, stations=stations_by_source)

@app.route('/api/settings/<key>', methods=['GET'])
def get_setting_api(key):
    """Get a specific setting"""
    import json
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    
    conn.close()
    
    if row:
        try:
            value = json.loads(row['value'])
            return jsonify({'success': True, 'key': key, 'value': value})
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid JSON in database'}), 500
    else:
        return jsonify({'success': False, 'error': 'Setting not found'}), 404

@app.route('/api/settings/<key>', methods=['POST'])
def update_setting(key):
    """Update a specific setting"""
    import json
    try:
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({'success': False, 'error': 'No value provided'}), 400
        
        # Validate key
        valid_keys = ['target_artists', 'target_songs', 'priority_myonlineradio', 
                      'relisten', 'myonlineradio', 'playlist24']
        if key not in valid_keys:
            return jsonify({'success': False, 'error': 'Invalid setting key'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        json_value = json.dumps(value)
        
        c.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                 (key, json_value, timestamp))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Setting {key} updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """Get all stations"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, slug, source, enabled, priority FROM stations ORDER BY source, name")
        stations = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'stations': stations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stations/<int:station_id>/toggle', methods=['POST'])
def toggle_station(station_id):
    """Toggle station enabled/disabled"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Toggle enabled status
        c.execute("UPDATE stations SET enabled = 1 - enabled, updated_at = ? WHERE id = ?",
                 (datetime.now().isoformat(), station_id))
        conn.commit()
        
        # Get updated station
        c.execute("SELECT enabled FROM stations WHERE id = ?", (station_id,))
        row = c.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'enabled': bool(row['enabled']) if row else False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stations/<int:station_id>/priority', methods=['POST'])
def toggle_station_priority(station_id):
    """Toggle station priority"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Toggle priority status
        c.execute("UPDATE stations SET priority = 1 - priority, updated_at = ? WHERE id = ?",
                 (datetime.now().isoformat(), station_id))
        conn.commit()
        
        # Get updated station
        c.execute("SELECT priority FROM stations WHERE id = ?", (station_id,))
        row = c.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'priority': bool(row['priority']) if row else False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stations', methods=['POST'])
def add_station():
    """Add a new station"""
    try:
        data = request.get_json()
        name = data.get('name')
        slug = data.get('slug')
        source = data.get('source')
        
        if not all([name, slug, source]):
            return jsonify({'success': False, 'error': 'Name, slug, and source are required'}), 400
        
        if source not in ['relisten', 'myonlineradio', 'playlist24']:
            return jsonify({'success': False, 'error': 'Invalid source'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        c.execute(
            "INSERT INTO stations (name, slug, source, enabled, priority, updated_at) VALUES (?, ?, ?, 1, 0, ?)",
            (name, slug, source, timestamp)
        )
        conn.commit()
        station_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Station {name} added successfully',
            'id': station_id
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Station already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stations/<int:station_id>', methods=['DELETE'])
def delete_station(station_id):
    """Delete a station"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM stations WHERE id = ?", (station_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Station deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found!")
        print("Make sure main.py has run at least once to create the database.")
        exit(1)
    
    print("RadioDetector Web Server")
    print("=" * 50)
    print("Starting Flask app on http://0.0.0.0:5000")
    print("Access from: http://localhost:5000")
    print("Or from other machines: http://<your-pi-ip>:5000")
    print("=" * 50)
    
    # Run on all interfaces (so it's accessible from other machines)
    # Debug mode disabled for production use
    app.run(host='0.0.0.0', port=5000, debug=False)
