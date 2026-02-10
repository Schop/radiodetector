# Changes Summary

## Normalization (Completed ✅)

### Files Modified:
1. **main.py** - Updated `normalize_song_title()` function
   - Now converts artist and song titles to consistent title case
   - Handles apostrophes correctly (e.g., "I Can't Dance" not "I Can'T Dance")
   - Eliminates duplicates like "PHIL COLLINS" vs "Phil Collins"

2. **normalize_db.py** - Created script to fix existing database entries
   - Normalizes all existing songs in the database
   - Shows what changed
   - Works with both SQLite and MySQL

## MySQL Support (In Progress ⚠️)

### Files Created:
1. **db_connection.py** - Database abstraction layer
   - Supports both SQLite and MySQL
   - Auto-adapts SQL queries (? vs %s placeholders)
   - Handles INSERT OR REPLACE → REPLACE (MySQL)
   - Handles INSERT OR IGNORE → INSERT IGNORE (MySQL)
   - Creates appropriate table schemas for each database type

2. **convert_webapp_to_mysql.py** - Automated conversion script
   - Updates all database calls in web_app.py
   - Must be run to complete the migration

3. **MYSQL_MIGRATION.md** - Complete setup guide
   - Step-by-step instructions
   - Troubleshooting tips
   - Performance recommendations

### Files Modified:
1. **config.yaml** - Added database configuration section
   - Choose between 'sqlite' or 'mysql'
   - MySQL connection parameters

2. **requirements.txt** - Added mysql-connector-python

3. **main.py** - Updated to use db_connection module  
   - All SQL queries now auto-adapt to database type
   - ✅ Fully migrated

4. **web_app.py** - Partially updated
   - ✅ Database connection functions updated
   - ✅ Key read operations updated  
   - ✅ Critical write operations updated
   - ⚠️ Need to run convert_webapp_to_mysql.py to finish

5. **normalize_db.py** - Updated to support MySQL
   - ✅ Fully migrated

## Next Steps

### For Normalization:
1. Transfer files to Raspberry Pi
2. Stop the service: `sudo systemctl stop radiochecker`
3. Run: `python3 normalize_db.py`
4. Restart: `sudo systemctl start radiochecker`

### For MySQL Migration:
1. **Complete web_app.py conversion**:
   ```bash
   python convert_webapp_to_mysql.py
   ```

2. **Test locally with SQLite** (verify nothing broke)

3. **Set up MySQL server** (see MYSQL_MIGRATION.md)

4. **Update config.yaml** with MySQL credentials

5. **Test with MySQL locally**

6. **Deploy to Raspberry Pi**

## Database Schema

Both SQLite and MySQL will use these tables:

### songs table
- id: Primary key
- station: Station name
- song: Song title (normalized)
- artist: Artist name (normalized)
- timestamp: ISO format timestamp
- Indexes: station, artist,timestamp (MySQL only)

### settings table
- key: Setting name (primary key)
- value: JSON-encoded value
- updated_at: ISO timestamp

### stations table
- id: Auto-increment primary key
- name: Station display name
- slug: URL slug for station
- source: relisten/myonlineradio/playlist24
- enabled: 1 or 0
- priority: 1 or 0
- updated_at: ISO timestamp
- Unique constraint: (name, source)

## Testing Checklist

### Normalization:
- [ ] Run normalize_db.py
- [ ] Check "PHIL COLLINS" became "Phil Collins"
- [ ] Check "I CAN'T DANCE" became "I Can't Dance"
- [ ] Check "I Can't Dance" and "I can't dance" are now same
- [ ] Verify detection still works

### MySQL (if implementing):
- [ ] Run convert_webapp_to_mysql.py
- [ ] Test with type: sqlite (verify still works)
- [ ] Set up MySQL database
- [ ] Test with type: mysql
- [ ] Verify web interface works
- [ ] Verify songs are logged
- [ ] Verify settings can be changed
- [ ] Check performance
- [ ] Deploy to Pi
- [ ] Monitor for 24 hours

## Rollback Plan

### If Normalization Breaks Something:
- Restore database from backup:
  ```bash
  cp radio_songs.db.backup radio_songs.db
  ```

### If MySQL Migration Breaks Something:
- Change `type: mysql` back to `type: sqlite` in config.yaml
- Restart services
- App will automatically use SQLite again
