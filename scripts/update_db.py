import sqlite3

def update_schema():
    conn = sqlite3.connect('database/app_data.db')
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(templates);")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'config_json' not in columns:
            print("Adding config_json column to templates table...")
            conn.execute("ALTER TABLE templates ADD COLUMN config_json TEXT;")
            conn.commit()
            print("Schema updated successfully.")
        else:
            print("config_json column already exists.")
            
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema()
