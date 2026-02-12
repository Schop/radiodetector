import sqlite3
import os

# Check static_web database
os.chdir('static_web')
conn = sqlite3.connect('radio_songs.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM songs')
count = c.fetchone()[0]
print(f'Rows in static_web db: {count}')

# Get all songs
c.execute('SELECT * FROM songs ORDER BY timestamp DESC')
songs = c.fetchall()
print(f'First song: {songs[0] if songs else "None"}')
print(f'Last song: {songs[-1] if songs else "None"}')
conn.close()

# Check main database
os.chdir('..')
conn = sqlite3.connect('radio_songs.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM songs')
count = c.fetchone()[0]
print(f'Rows in main db: {count}')
conn.close()