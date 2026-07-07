import sqlite3

def migrate_database():
    conn = sqlite3.connect("news_app.db")
    cursor = conn.cursor()
    
    try:
        # Check if user_interests table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_interests'")
        if cursor.fetchone():
            print("Backing up existing data...")
            # Get existing data first
            cursor.execute("SELECT * FROM user_interests")
            existing_data = cursor.fetchall()
            print(f"Found {len(existing_data)} records")
            
            # Rename the current table
            cursor.execute("ALTER TABLE user_interests RENAME TO user_interests_old")
            
            # Create the correct table
            cursor.execute('''
                CREATE TABLE user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topics TEXT,
                    countries TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Try to migrate data if exists
            if existing_data:
                try:
                    print("Migrating data...")
                    # Check structure of old table
                    cursor.execute("PRAGMA table_info(user_interests_old)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    print(f"Old table columns: {column_names}")
                    
                    # Check if it had topic/country or topics/countries
                    if 'topic' in column_names and 'country' in column_names:
                        # Old structure with singular column names
                        for row in existing_data:
                            user_id = row[1]  # Assuming user_id is in position 1
                            topic = row[2]    # Assuming topic is in position 2
                            country = row[3]  # Assuming country is in position 3
                            
                            # Insert with new column names
                            cursor.execute(
                                "INSERT INTO user_interests (user_id, topics, countries) VALUES (?, ?, ?)",
                                (user_id, topic, country)
                            )
                    else:
                        # Different structure, do a direct copy
                        print("Unknown old table structure, attempting direct migration...")
                        for row in existing_data:
                            # Insert all fields except ID
                            cursor.execute(
                                "INSERT INTO user_interests (user_id, topics, countries) VALUES (?, ?, ?)",
                                (row[1], row[2], row[3])
                            )
                except Exception as e:
                    print(f"Error during data migration: {e}")
            
            # Commit changes
            conn.commit()
            print("Migration completed successfully!")
        else:
            # If table doesn't exist, create it
            print("user_interests table doesn't exist, creating it...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    topics TEXT,
                    countries TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()
            print("Table created successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 