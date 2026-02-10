"""
Script to update web_app.py to use the new database module
This automates the conversion of all database calls
"""
import re

def update_web_app():
    with open('web_app.py', 'r', encoding='utf-8') as f:
        content = f.content()
    
    # Track changes
    changes = 0
    
    # Pattern 1: conn = get_db_connection() followed by c = conn.cursor()
    # Replace with: conn, db_type = get_db_connection() followed by c = db.get_dict_cursor(conn, db_type)
    pattern1 = r'(\s+)conn = get_db_connection\(\)\n(\s+)c = conn\.cursor\(\)'
    replacement1 = r'\1conn, db_type = get_db_connection()\n\2c = db.get_dict_cursor(conn, db_type)'
    content, n = re.subn(pattern1, replacement1, content)
    changes += n
    print(f"Updated {n} connection patterns")
    
    # Pattern 2: c.execute("...
    # Replace with: db.execute_query(c, "..., db_type=db_type)
    # This is tricky because execute can span multiple lines
    
    # Pattern 2a: Single line execute with no parameters
    pattern2a = r'c\.execute\("([^"]+)"\)'
    replacement2a = r'db.execute_query(c, "\1", db_type=db_type)'
    content, n = re.subn(pattern2a, replacement2a, content)
    changes += n
    print(f"Updated {n} execute patterns (no params)")
    
    # Pattern 2b: Single line execute with parameters
    pattern2b = r'c\.execute\("([^"]+)",\s*(\([^)]+\))\)'
    replacement2b = r'db.execute_query(c, "\1", \2, db_type)'
    content, n = re.subn(pattern2b, replacement2b, content)
    changes += n
    print(f"Updated {n} execute patterns (with params)")
    
    # Write back
    with open('web_app_updated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nTotal changes: {changes}")
    print("Updated file saved as: web_app_updated.py")
    print("Review the changes, then rename it to web_app.py")

if __name__ == '__main__':
    update_web_app()
