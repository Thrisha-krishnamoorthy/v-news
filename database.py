import sqlite3

def init_db():
    conn = sqlite3.connect("news_app.db")
    c = conn.cursor()

    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password_hash TEXT
        )
    ''')

    # Check if user_interests table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_interests'")
    if c.fetchone():
        # Check if it has the correct columns
        c.execute("PRAGMA table_info(user_interests)")
        columns = [col[1] for col in c.fetchall()]
        if 'topics' not in columns or 'countries' not in columns:
            # Backup and recreate with correct schema
            print("Migrating user_interests table to correct schema...")
            # Get existing data
            try:
                c.execute("SELECT * FROM user_interests")
                existing_data = c.fetchall()
                # Rename the table
                c.execute("ALTER TABLE user_interests RENAME TO user_interests_old")
                # Create the correct table
                c.execute('''
                    CREATE TABLE user_interests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        topics TEXT,  
                        countries TEXT, 
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                # Migrate data if possible
                if existing_data:
                    for row in existing_data:
                        try:
                            user_id = row[1]  # Assuming user_id is always at index 1
                            topics = row[2] if len(row) > 2 else ""
                            countries = row[3] if len(row) > 3 else ""
                            c.execute("INSERT INTO user_interests (user_id, topics, countries) VALUES (?, ?, ?)",
                                      (user_id, topics, countries))
                        except Exception as e:
                            print(f"Error migrating data: {e}")
            except Exception as e:
                print(f"Error during migration: {e}")
    else:
        # User Interests table doesn't exist - create it with correct columns
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topics TEXT,  
                countries TEXT, 
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

    # Saved News
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            url TEXT,
            source TEXT,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Clicks table for tracking user interactions
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            category TEXT,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
