import sqlite3
import os

def add_tone_column():
    db_path = os.path.join("data", "client_finder.db")
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. The app will create it later with the updated schema.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN tone TEXT")
        print("Successfully added tone column to messages table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'tone' already exists.")
        elif "no such table" in str(e).lower():
            print("Table 'messages' does not exist yet. Will be created with tone column.")
        else:
            print(f"Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_tone_column()
