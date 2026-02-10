"""
Quick test script to verify MySQL connection without running the full application
"""
import db_connection as db
from colorama import Fore, Style, init

init(autoreset=True)

print(f"{Fore.CYAN}Testing MySQL connection...{Style.RESET_ALL}")
print(f"Database type configured: {db.DB_TYPE}")
print(f"MySQL host: {db.DB_CONFIG.get('host', 'N/A')}")
print(f"MySQL database: {db.DB_CONFIG.get('database', 'N/A')}")
print()

try:
    # Try to connect
    print(f"{Fore.YELLOW}Attempting to connect (timeout: 10 seconds)...{Style.RESET_ALL}")
    
    # Set connection timeout
    if db.DB_TYPE == 'mysql':
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=db.DB_CONFIG['host'],
                port=db.DB_CONFIG['port'],
                user=db.DB_CONFIG['user'],
                password=db.DB_CONFIG['password'],
                database=db.DB_CONFIG['database'],
                connection_timeout=10
            )
            db_type = 'mysql'
        except ImportError:
            print(f"{Fore.RED}✗ mysql-connector-python not installed{Style.RESET_ALL}")
            print("Install with: pip install mysql-connector-python")
            raise
    else:
        conn, db_type = db.get_connection()
    
    print(f"{Fore.GREEN}✓ Successfully connected to {db_type.upper()}!{Style.RESET_ALL}")
    
    # Try to create tables
    print(f"{Fore.YELLOW}Creating tables...{Style.RESET_ALL}")
    actual_db_type = db.init_database()
    print(f"{Fore.GREEN}✓ Tables created successfully!{Style.RESET_ALL}")
    
    # Test a simple query
    print(f"{Fore.YELLOW}Testing database query...{Style.RESET_ALL}")
    c = conn.cursor()
    db.execute_query(c, "SELECT COUNT(*) FROM songs", db_type=db_type)
    count = c.fetchone()[0]
    print(f"{Fore.GREEN}✓ Query successful! Songs table has {count} entries{Style.RESET_ALL}")
    
    conn.close()
    
    print()
    print(f"{Fore.GREEN}{'='*60}")
    print(f"✓ MySQL connection test PASSED!")
    print(f"✓ You can now run main.py to start monitoring")
    print(f"{'='*60}{Style.RESET_ALL}")
    
except Exception as e:
    print(f"{Fore.RED}✗ Connection failed: {e}{Style.RESET_ALL}")
    print()
    print(f"{Fore.YELLOW}Troubleshooting tips:")
    print(f"  - Check MySQL server is running")
    print(f"  - Verify credentials in config.yaml")
    print(f"  - Check firewall allows connection to port {db.DB_CONFIG.get('port', 3306)}")
    print(f"  - Verify user has remote access permissions{Style.RESET_ALL}")
