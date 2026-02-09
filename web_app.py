"""
Simple Flask web interface for RadioDetector
Displays detected Phil Collins and Genesis songs from SQLite database
Lightweight and Pi Zero friendly
"""

from flask import Flask, render_template, request
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__)
DB_PATH = 'radio_songs.db'

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
    
    # Get filter parameters
    station_filter = request.args.get('station', '')
    days_filter = request.args.get('days', '7')
    
    try:
        days_back = int(days_filter)
    except:
        days_back = 7
    
    # Build query
    query = "SELECT * FROM songs WHERE 1=1"
    params = []
    
    if station_filter:
        query += " AND station LIKE ?"
        params.append(f"%{station_filter}%")
    
    if days_back > 0:
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        query += " AND timestamp > ?"
        params.append(cutoff_date)
    
    query += " ORDER BY timestamp DESC LIMIT 500"
    
    c.execute(query, params)
    songs = c.fetchall()
    
    # Get unique stations for filter dropdown
    c.execute("SELECT DISTINCT station FROM songs ORDER BY station")
    stations = [row['station'] for row in c.fetchall()]
    
    conn.close()
    
    # Convert timestamps to readable format
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song['timestamp'])
        ts_formatted = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else song['timestamp']
        songs_data.append({
            'station': song['station'],
            'artist': song['artist'],
            'song': song['song'],
            'timestamp': ts_formatted,
            'timestamp_raw': song['timestamp']
        })
    
    return render_template(
        'index.html',
        songs=songs_data,
        stations=stations,
        station_filter=station_filter,
        days_filter=days_filter,
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
    app.run(host='0.0.0.0', port=5000, debug=False)
