"""
Database connection module supporting both SQLite and MySQL
"""
import sqlite3
import yaml
import os
import sys

# Global variables for database config
DB_TYPE = 'sqlite'
DB_CONFIG = {}

def load_db_config():
    """Load database configuration from config.yaml"""
    global DB_TYPE, DB_CONFIG
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            db_config = config.get('database', {})
            
            DB_TYPE = db_config.get('type', 'sqlite')
            
            if DB_TYPE == 'mysql':
                DB_CONFIG = {
                    'host': db_config.get('mysql_host', 'localhost'),
                    'port': db_config.get('mysql_port', 3306),
                    'user': db_config.get('mysql_user', 'radiochecker'),
                    'password': db_config.get('mysql_password', ''),
                    'database': db_config.get('mysql_database', 'radiochecker')
                }
            else:
                DB_CONFIG = {
                    'database': db_config.get('sqlite_file', 'radio_songs.db')
                }
    except Exception as e:
        print(f"Warning: Could not load database config, using SQLite: {e}")
        DB_TYPE = 'sqlite'
        DB_CONFIG = {'database': 'radio_songs.db'}

def get_connection():
    """Get a database connection based on configuration"""
    if DB_TYPE == 'mysql':
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                autocommit=False
            )
            return conn, 'mysql'
        except ImportError:
            print("Warning: mysql-connector-python not installed, falling back to SQLite")
            print("Install with: pip install mysql-connector-python")
            conn = sqlite3.connect('radio_songs.db')
            return conn, 'sqlite'
        except Exception as e:
            print(f"Error connecting to MySQL: {e}")
            print("Falling back to SQLite...")
            # Fall back to SQLite
            conn = sqlite3.connect('radio_songs.db')
            return conn, 'sqlite'
    else:
        conn = sqlite3.connect(DB_CONFIG.get('database', 'radio_songs.db'))
        return conn, 'sqlite'

def get_dict_connection():
    """Get a database connection that returns rows as dictionaries"""
    if DB_TYPE == 'mysql':
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                autocommit=False
            )
            # MySQL returns tuples by default, we'll handle row_factory in cursor
            return conn, 'mysql'
        except ImportError:
            print("Warning: mysql-connector-python not installed, falling back to SQLite")
            conn = sqlite3.connect('radio_songs.db')
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'
        except Exception as e:
            print(f"Error connecting to MySQL: {e}")
            print("Falling back to SQLite...")
            # Fall back to SQLite
            conn = sqlite3.connect('radio_songs.db')
            conn.row_factory = sqlite3.Row
            return conn, 'sqlite'
    else:
        conn = sqlite3.connect(DB_CONFIG.get('database', 'radio_songs.db'))
        conn.row_factory = sqlite3.Row
        return conn, 'sqlite'

def get_dict_cursor(conn, db_type):
    """Get a cursor that returns rows as dictionaries"""
    if db_type == 'mysql':
        return conn.cursor(dictionary=True)
    else:
        return conn.cursor()

def get_placeholder(db_type=None):
    """Get the parameter placeholder for the database type"""
    if db_type is None:
        db_type = DB_TYPE
    return '%s' if db_type == 'mysql' else '?'

def adapt_query(query, db_type=None):
    """Adapt SQL query for specific database type"""
    if db_type is None:
        db_type = DB_TYPE
    
    if db_type == 'mysql':
        # Convert SQLite placeholders to MySQL
        query = query.replace('?', '%s')
        # Convert INSERT OR REPLACE to REPLACE INTO
        query = query.replace('INSERT OR REPLACE', 'REPLACE')
        # Convert INSERT OR IGNORE to INSERT IGNORE
        query = query.replace('INSERT OR IGNORE', 'INSERT IGNORE')
    
    return query

def execute_query(cursor, query, params=None, db_type=None):
    """Execute a query with automatic SQL adaptation"""
    adapted_query = adapt_query(query, db_type)
    if params:
        cursor.execute(adapted_query, params)
    else:
        cursor.execute(adapted_query)

def executemany_query(cursor, query, params_list, db_type=None):
    """Execute many queries with automatic SQL adaptation"""
    adapted_query = adapt_query(query, db_type)
    cursor.executemany(adapted_query, params_list)

def init_database():
    """Initialize database tables"""
    conn, db_type = get_connection()
    c = conn.cursor()
    
    if db_type == 'mysql':
        # MySQL table creation
        c.execute('''CREATE TABLE IF NOT EXISTS songs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            station VARCHAR(255),
            song TEXT,
            artist VARCHAR(255),
            timestamp VARCHAR(50),
            INDEX idx_station (station),
            INDEX idx_artist (artist),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            `key` VARCHAR(255) PRIMARY KEY,
            value TEXT,
            updated_at VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS stations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            source VARCHAR(50) NOT NULL,
            enabled TINYINT DEFAULT 1,
            priority INT DEFAULT 0,
            updated_at VARCHAR(50),
            UNIQUE KEY unique_station (name, source)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
    else:
        # SQLite table creation
        c.execute('''CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            station TEXT,
            song TEXT,
            artist TEXT,
            timestamp TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            source TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            priority INTEGER DEFAULT 0,
            updated_at TEXT,
            UNIQUE(name, source)
        )''')
    
    conn.commit()
    conn.close()
    
    return db_type

# Load configuration on module import
load_db_config()
