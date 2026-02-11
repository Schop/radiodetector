#!/usr/bin/env python3
"""
Test connection to STRATO MySQL database
"""

import mysql.connector
import sys

# STRATO MySQL configuration
MYSQL_CONFIG = {
    'host': 'database-5019663848.webspace-host.com',
    'database': 'dbs15302621',
    'user': 'dbu5562565',
    'password': 'Passie.19720104',
    'port': 3306,
    'connect_timeout': 15
}

print("Testing MySQL connection to STRATO...")
print(f"Host: {MYSQL_CONFIG['host']}")
print(f"Database: {MYSQL_CONFIG['database']}")
print(f"User: {MYSQL_CONFIG['user']}")
print("-" * 50)

try:
    print("Attempting connection...")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    
    print("\n✅ SUCCESS! Connection established!")
    print(f"MySQL version: {version[0]}")
    
    # Test creating a table
    print("\nTesting table creation...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_connection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Table creation test passed!")
    
    # Clean up test table
    cursor.execute("DROP TABLE IF EXISTS test_connection")
    print("✅ Cleanup successful!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 50)
    print("All tests passed! STRATO MySQL is ready to use.")
    print("=" * 50)
    sys.exit(0)
    
except mysql.connector.Error as e:
    print(f"\n❌ MySQL Error: {e}")
    print("\nPossible issues:")
    print("- Wrong password")
    print("- IP address needs to be whitelisted")
    print("- Database not activated")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
