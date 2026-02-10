# MySQL Migration Guide

This guide explains how to migrate your Radio Checker from SQLite to MySQL.

## What's Been Done

✅ Added MySQL configuration to `config.yaml`
✅ Created `db_connection.py` - database abstraction layer supporting both SQLite and MySQL  
✅ Updated `main.py` to use the new database module
✅ Updated `normalize_db.py` to work with both databases
✅ Partially updated `web_app.py` (read operations and critical write operations)
✅ Added `mysql-connector-python` to `requirements.txt`

## What You Need to Do

### 1. Set Up MySQL Database

On your MySQL server, create the database and user:

```sql
CREATE DATABASE radiochecker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'radiochecker'@'%' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON radiochecker.* TO 'radiochecker'@'%';
FLUSH PRIVILEGES;
```

### 2. Update Configuration

**First, ensure you have a config.yaml file:**
```bash
# If you don't have config.yaml yet, copy from the example:
cp config.yaml.example config.yaml
```

Edit `config.yaml` and update the database section:

```yaml
database:
  type: mysql  # Change from 'sqlite' to 'mysql'
  # SQLite settings (used when type = sqlite)
  sqlite_file: radio_songs.db
  # MySQL settings (used when type = mysql)
  mysql_host: your-mysql-server.com  # or IP address
  mysql_port: 3306
  mysql_user: radiochecker
  mysql_password: your_secure_password  # ⚠️ Use your actual password
  mysql_database: radiochecker
```

**⚠️ Security Note:** 
- `config.yaml` is excluded from git (in `.gitignore`)
- Never commit your actual `config.yaml` with credentials
- Only `config.yaml.example` (with placeholder credentials) is tracked in git
- When deploying to new servers, always copy from the example and update credentials
- See [CREDENTIAL_SECURITY.md](CREDENTIAL_SECURITY.md) for more details

### 3. Complete web_app.py Conversion

Run the conversion script to automatically update all remaining database calls in web_app.py:

```bash
python convert_webapp_to_mysql.py
```

This will update all remaining `c.execute()` calls to use `db.execute_query()`.

### 4. Install MySQL Connector

On your Raspberry Pi:

```bash
pip3 install mysql-connector-python
```

Or if using a virtual environment:

```bash
source venv/bin/activate
pip install mysql-connector-python
```

### 5. Initialize MySQL Database

The tables will be created automatically when you first run the application. The `db_connection.py` module will:
- Create the necessary tables (songs, settings, stations)
- Use appropriate data types for MySQL
- Add indexes for better performance

### 6. Migrate Existing Data (Optional)

If you want to migrate existing SQLite data to MySQL:

**Option A: Fresh Start** 
- Start with an empty MySQL database
- The app will migrate configuration from config.yaml automatically

**Option B: Migrate SQLite Data**
```bash
# Export from SQLite
sqlite3 radio_songs.db .dump > backup.sql

# Manually import into MySQL (requires manual SQL conversion)
# SQLite and MySQL SQL syntax differs, so this needs manual editing
```

### 7. Test the Application

1. **Test locally first** (keeps SQLite):
   - Leave `type: sqlite` in config.yaml
   - Run: `python main.py`
   - Verify it still works

2. **Test MySQL connection**:
   - Change `type: mysql` in config.yaml
   - Run: `python main.py`
   - Should see: "Using MYSQL database"
   - Check for any connection errors

3. **Test the web interface**:
   - Run: `python web_app.py`
   - Open: http://localhost:5000
   - Test viewing songs, settings, etc.

### 8. Deploy to Raspberry Pi

1. **Copy all files** to your Pi:
   ```bash
   scp -r * pi@your-pi-ip:/home/pi/radiochecker/
   ```

2. **Update config.yaml** on the Pi with MySQL credentials

3. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Restart services**:
   ```bash
   sudo systemctl restart radiochecker
   sudo systemctl restart radiochecker-web
   ```

5. **Check logs**:
   ```bash
   sudo journalctl -u radiochecker -f
   sudo journalctl -u radiochecker-web -f
   ```

## Benefits of MySQL

✅ **Remote Access**: Query your database from anywhere
✅ **Better Performance**: Concurrent access, indexing
✅ **Easier Backups**: Standard MySQL backup tools
✅ **Scalability**: Can handle much larger datasets
✅ **Multi-device**: Multiple Raspberry Pis can share one database

## Rollback to SQLite

If you need to go back to SQLite:

1. Change `type: sqlite` in config.yaml
2. Restart the application
3. It will automatically use the local SQLite database

## Troubleshooting

### Connection Refused
- Check MySQL is running: `sudo systemctl status mysql`
- Check firewall allows port 3306
- Verify user has remote access permissions

### Authentication Failed
- Verify password in config.yaml
- Check MySQL user exists: `SELECT User, Host FROM mysql.user;`

### Tables Not Created
- Check MySQL user has CREATE TABLE permission
- Look for error messages in the log output

### Fallback to SQLite
If MySQL connection fails, the app automatically falls back to SQLite and logs a warning.

## Performance Tips

1. **Add Indexes** (if not auto-created):
   ```sql
   CREATE INDEX idx_songs_station ON songs(station);
   CREATE INDEX idx_songs_artist ON songs(artist);
   CREATE INDEX idx_songs_timestamp ON songs(timestamp);
   ```

2. **Regular Backups**:
   ```bash
   mysqldump -u radiochecker -p radiochecker > backup_$(date +%Y%m%d).sql
   ```

3. **Monitor Size**:
   ```sql
   SELECT table_name, 
          ROUND((data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
   FROM information_schema.tables 
   WHERE table_schema = 'radiochecker';
   ```
