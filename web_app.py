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
from main import TARGET_ARTISTS, TARGET_SONGS

app = Flask(__name__)
DB_PATH = 'radio_songs.db'
LOG_FILE = 'radio.log'
UPTIME_FILE = '.uptime'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    
    return render_template(
        'index.html',
        target_artists=TARGET_ARTISTS,
        target_songs=TARGET_SONGS,
        songs=songs_data,
        stations=stations,
        total_count=len(songs_data)
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
