import sqlite3

def upgrade():
    # Make sure this points to your actual database file name
    conn = sqlite3.connect("riftdrop.db") 
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE stores ADD COLUMN latitude FLOAT;")
        cursor.execute("ALTER TABLE stores ADD COLUMN longitude FLOAT;")
        print("✅ SUCCESS: GPS columns added to the stores table!")
    except Exception as e:
        print(f"Error (You might have already added them): {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade()