import sqlite3
import bcrypt

DB = "news_app.db"  # Correct database name

def get_connection():
    return sqlite3.connect(DB)

def create_user(username, email, password):
    conn = get_connection()
    c = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
              (username, email, hashed.decode()))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user[3].encode()):
        return {"id": user[0], "username": user[1], "email": user[2]}
    return None

def save_user_interests(user_id, topics, countries):
    """
    Save user interests using a single row per user with comma-separated values
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Convert lists to comma-separated strings
    topics_str = ",".join(topics) if topics else ""
    countries_str = ",".join(countries) if countries else ""
    
    # Delete any existing entries for this user
    c.execute("DELETE FROM user_interests WHERE user_id = ?", (user_id,))
    
    # Insert a single row with all topics and countries
    c.execute("INSERT INTO user_interests (user_id, topics, countries) VALUES (?, ?, ?)",
              (user_id, topics_str, countries_str))
    
    conn.commit()
    conn.close()

# Get user interests as lists
def get_user_interests(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT topics, countries FROM user_interests WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        # Convert comma-separated strings back to lists
        topics = row[0].split(",") if row[0] else []
        countries = row[1].split(",") if row[1] else []
        return {"topics": topics, "countries": countries}
    return None

# def get_user_interests(user_id):
#     conn = sqlite3.connect("news_app.db")
#     c = conn.cursor()
#     c.execute("SELECT topic, country FROM user_interests WHERE user_id = ?", (user_id,))
#     interests = c.fetchone()  # Only one row should exist for each user
#     conn.close()

#     topics = interests[0].split(",") if interests else []
#     countries = interests[1].split(",") if interests else []
#     return {"topics": topics, "countries": countries}
