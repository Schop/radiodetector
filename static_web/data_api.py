#!/usr/bin/env python3
"""
CGI API script for RadioChecker data
Serves JSON data for the static frontend
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
import cgi
import cgitb
cgitb.enable()

# Database path - adjust as needed
DB_PATH = 'radio_songs.db'

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH), 'sqlite'

def parse_iso_timestamp(ts_str):
    """Parse ISO timestamp string"""
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except:
        return None

def get_setting(key, default=None):
    """Get a setting value from database"""
    try:
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return default
    except:
        return default

def chart_data():
    """JSON API for chart data"""
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Songs per station (top 5)
    c.execute("""
        SELECT station, COUNT(*) as count 
        FROM songs 
        GROUP BY station 
        ORDER BY count DESC 
        LIMIT 5
    """)
    stations_data = c.fetchall()
    
    # Songs by hour of day
    c.execute("SELECT timestamp FROM songs")
    all_songs = c.fetchall()
    
    hours = [0] * 24
    days_of_week = [0] * 7
    days_count = {}
    
    for row in all_songs:
        ts = parse_iso_timestamp(row[0])
        if ts:
            hours[ts.hour] += 1
            days_of_week[ts.weekday()] += 1
            date_key = ts.strftime('%Y-%m-%d')
            days_count[date_key] = days_count.get(date_key, 0) + 1
    
    # Get last 14 days
    sorted_days = sorted(days_count.items(), reverse=True)[:14]
    sorted_days.reverse()
    
    conn.close()
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return {
        'stations': {
            'labels': [row[0] for row in stations_data],
            'data': [row[1] for row in stations_data]
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
            'labels': [k for k, v in sorted_days],
            'data': [v for k, v in sorted_days]
        }
    }

def now_playing():
    """Get currently playing songs by target artists (detected in last 10 minutes)"""
    from datetime import datetime, timedelta
    
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Get target artists
    target_artists = get_setting('target_artists', [])
    
    if not target_artists:
        return {'success': True, 'playing': []}
    
    # Get songs detected in last 10 minutes - most recent per station
    cutoff_time = (datetime.now() - timedelta(minutes=10)).isoformat()
    
    # Get all stations that have songs in the last 10 minutes
    c.execute("SELECT DISTINCT station FROM songs WHERE timestamp > ?", (cutoff_time,))
    stations = [row[0] for row in c.fetchall()]
    
    # Get the most recent song for each station
    now_playing_list = []
    for station in stations:
        c.execute("""
            SELECT station, artist, song, timestamp
            FROM songs
            WHERE station = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (station, cutoff_time))
        
        song_data = c.fetchone()
        if song_data and song_data[1] in target_artists:
            ts = parse_iso_timestamp(song_data[3])
            if ts:
                time_ago = datetime.now() - ts
                minutes_ago = int(time_ago.total_seconds() / 60)
                if minutes_ago == 0:
                    time_ago_str = 'Just now'
                elif minutes_ago == 1:
                    time_ago_str = '1 min ago'
                else:
                    time_ago_str = f'{minutes_ago} mins ago'
            else:
                time_ago_str = 'Recently'
            
            now_playing_list.append({
                'station': song_data[0],
                'artist': song_data[1],
                'song': song_data[2],
                'time_ago': time_ago_str
            })
    
    conn.close()
    
    return {
        'success': True,
        'playing': now_playing_list
    }

def station_charts(station_name):
    """Charts for specific station"""
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Songs by hour and weekday for this station
    c.execute("SELECT timestamp FROM songs WHERE station = ?", (station_name,))
    songs = c.fetchall()
    
    hours = [0] * 24
    weekdays = [0] * 7
    for row in songs:
        ts = parse_iso_timestamp(row[0])
        if ts:
            hours[ts.hour] += 1
            weekdays[ts.weekday()] += 1
    
    # Top songs for this station
    c.execute("""
        SELECT song, COUNT(*) as count
        FROM songs
        WHERE station = ?
        GROUP BY song
        ORDER BY count DESC
        LIMIT 10
    """, (station_name,))
    top_songs = c.fetchall()
    
    conn.close()
    
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    return {
        'hours': {
            'labels': [f"{h}:00" for h in range(24)],
            'data': hours
        },
        'weekdays': {
            'labels': day_names,
            'data': weekdays
        },
        'top_songs': {
            'labels': [row[0] for row in top_songs],
            'data': [row[1] for row in top_songs]
        }
    }

def song_charts(song_name):
    """Charts for specific song"""
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Plays by hour
    c.execute("SELECT timestamp FROM songs WHERE song = ?", (song_name,))
    songs = c.fetchall()
    
    hours = [0] * 24
    stations = {}
    for row in songs:
        ts = parse_iso_timestamp(row[0])
        if ts:
            hours[ts.hour] += 1
    
    # By station
    c.execute("""
        SELECT station, COUNT(*) as count
        FROM songs
        WHERE song = ?
        GROUP BY station
        ORDER BY count DESC
    """, (song_name,))
    station_data = c.fetchall()
    
    conn.close()
    
    return {
        'hours': {
            'labels': [f"{h}:00" for h in range(24)],
            'data': hours
        },
        'stations': {
            'labels': [row[0] for row in station_data],
            'data': [row[1] for row in station_data]
        }
    }

def station_data(station_name):
    """Get data for station page"""
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Get all songs from station
    c.execute("SELECT * FROM songs WHERE station = ? ORDER BY timestamp DESC", (station_name,))
    songs = c.fetchall()
    
    total_songs = len(songs)
    
    # Unique artists
    c.execute("SELECT DISTINCT artist FROM songs WHERE station = ? ORDER BY artist", (station_name,))
    artists = [row[0] for row in c.fetchall()]
    
    # Unique songs
    c.execute("SELECT DISTINCT song FROM songs WHERE station = ? ORDER BY song", (station_name,))
    song_titles = [row[0] for row in c.fetchall()]
    
    conn.close()
    
    # Format songs
    songs_data = []
    for song in songs:
        ts = parse_iso_timestamp(song[3])
        ts_formatted = ts.strftime('%d %b %Y at %H:%M').replace(' 0', ' ') if ts else song[3]
        songs_data.append({
            'station': song[1],
            'artist': song[2],
            'song': song[0],
            'timestamp': ts_formatted,
            'timestamp_raw': song[3]
        })
    
    return {
        'station_name': station_name,
        'total_songs': total_songs,
        'artists': artists,
        'song_titles': song_titles,
        'songs': songs_data
    }

def main():
    """Main CGI handler"""
    # Get the path
    path_info = os.environ.get('PATH_INFO', '/')
    
    # Route to functions
    routes = {
        '/api/chart-data': chart_data,
        '/api/now-playing': now_playing,
        '/api/index-data': index_data,
    }
    
    # Special case for export
    if path_info == '/api/export':
        export_csv()
        return
    
    # Handle station, song, artist
    if path_info.startswith('/api/station/'):
        parts = path_info[len('/api/station/'):].split('/')
        station_name = parts[0]
        if len(parts) > 1 and parts[1] == 'charts':
            data = station_charts(station_name)
        elif len(parts) > 1 and parts[1] == 'data':
            data = station_data(station_name)
        else:
            data = {'error': 'Not implemented'}
    elif path_info.startswith('/api/song/'):
        parts = path_info[len('/api/song/'):].split('/')
        song_name = parts[0]
        if len(parts) > 1 and parts[1] == 'charts':
            data = song_charts(song_name)
        else:
            data = {'error': 'Not implemented'}
    elif path_info.startswith('/api/artist/'):
        parts = path_info[len('/api/artist/'):].split('/')
        artist_name = parts[0]
        if len(parts) > 1 and parts[1] == 'charts':
            data = artist_charts(artist_name)
        else:
            data = {'error': 'Not implemented'}
    else:
        func = routes.get(path_info)
        if func:
            data = func()
        else:
            data = {'error': 'Endpoint not found'}
    
    # Output JSON
    print("Content-Type: application/json")
    print()
    print(json.dumps(data))

if __name__ == '__main__':
    main()