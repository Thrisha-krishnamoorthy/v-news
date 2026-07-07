import sqlite3
import os
import sys

# Force output to be displayed immediately
sys.stdout.reconfigure(line_buffering=True)

# Check if database file exists
print(f"Database exists: {os.path.exists('news_app.db')}")
sys.stdout.flush()

# Connect to database
try:
    conn = sqlite3.connect("news_app.db")
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    sys.stdout.flush()
    
    # Check user_interests table structure
    try:
        cursor.execute("PRAGMA table_info(user_interests)")
        columns = cursor.fetchall()
        print(f"user_interests columns: {columns}")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error accessing user_interests table: {e}")
        sys.stdout.flush()
    
    # Check for existing entries
    try:
        cursor.execute("SELECT * FROM user_interests LIMIT 5")
        entries = cursor.fetchall()
        print(f"Sample entries: {entries}")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error fetching entries: {e}")
        sys.stdout.flush()
    
except Exception as e:
    print(f"Database connection error: {e}")
    sys.stdout.flush()
finally:
    if 'conn' in locals():
        conn.close() 