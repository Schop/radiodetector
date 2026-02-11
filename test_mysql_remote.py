#!/usr/bin/env python3
"""
Quick test script to check MySQL connection to FreeSQLDatabase
Run this on your Raspberry Pi to test if the connection works from there
"""

import mysql.connector
import sys

# Database credentials
config = {
    'host': 'sql7.freesqldatabase.com',
    'database': 'sql7816777',
    'user': 'sql7816777',
    'password': 'EusbhwFIKb',
    'port': 3306,
    'connect_timeout': 15
}

print("Testing MySQL connection to FreeSQLDatabase...")
print(f"Host: {config['host']}")
print(f"Database: {config['database']}")
print(f"User: {config['user']}")
print("-" * 50)

try:
    print("Attempting connection...")
    conn = mysql.connector.connect(**config)
    
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
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 50)
    print("All tests passed! Database is ready to use.")
    print("=" * 50)
    sys.exit(0)
    
except mysql.connector.Error as e:
    print(f"\n❌ MySQL Error: {e}")
    print("\nPossible issues:")
    print("- Firewall blocking port 3306")
    print("- IP address needs to be whitelisted")
    print("- Database not activated")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
