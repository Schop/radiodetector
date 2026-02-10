"""
Automated script to update all remaining database calls in web_app.py
Run this script to complete the MySQL migration
"""

with open('web_app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

output = []
i = 0
updates = 0

while i < len(lines):
    line = lines[i]
    
    # Pattern 1: conn = get_db_connection() followed by c = conn.cursor()
    if 'conn = get_db_connection()' in line and i + 1 < len(lines):
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        
        # Check next line for c = conn.cursor()
        if i + 1 < len(lines) and 'c = conn.cursor()' in lines[i + 1]:
            output.append(f"{spaces}conn, db_type = get_db_connection()\n")
            output.append(f"{spaces}c = db.get_dict_cursor(conn, db_type)\n")
            i += 2  # Skip both lines
            updates += 1
            continue
    
    # Pattern 2: c.execute with no parameters
    if 'c.execute(' in line and ', (' not in line and not line.strip().endswith(','):
        # Extract the SQL query
        if 'c.execute("' in line:
            indent = len(line) - len(line.lstrip())
            spaces = ' ' * indent
            start = line.find('c.execute("')
            end = line.rfind('")')
            if start != -1 and end != -1:
                sql = line[start+11:end+1]  # Get the SQL string including quotes
                output.append(f"{spaces}db.execute_query(c, {sql}, db_type=db_type)\n")
                i += 1
                updates += 1
                continue
    
    # Pattern 3: c.execute with parameters (single line)
    if 'c.execute("' in line and ', (' in line:
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        # Extract SQL and params
        start = line.find('c.execute("')
        if start != -1:
            # Get everything after c.execute(
            rest = line[start+10:]
            # Find the closing of execute()
            if rest.count('(') >= 2:  # Has SQL params tuple
                # Find the SQL string
                sql_end = rest.find('",')
                if sql_end != -1:
                    sql = rest[:sql_end+1]  # Include the closing quote
                    # Find the params tuple
                    params_start = rest.find(', (')
                    params_end = rest.rfind(')')
                    if params_start != -1 and params_end != -1:
                        params = rest[params_start+2:params_end+1]
                        output.append(f"{spaces}db.execute_query(c, {sql}, {params}, db_type)\n")
                        i += 1
                        updates += 1
                        continue
    
    # Default: Keep the line as-is
    output.append(line)
    i += 1

# Write the updated file
with open('web_app.py', 'w', encoding='utf-8') as f:
    f.writelines(output)

print(f"✓ Updated {updates} database call patterns in web_app.py")
print("✓ File has been updated successfully")
