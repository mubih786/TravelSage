# ============================================
# DATABASE CONNECTION & SETUP
# Tourist Place Recommendation System
# ============================================

import mysql.connector
from mysql.connector import Error

# ---- Database Configuration ----
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',          # Change to your MySQL username
    'password': 'root',  # Change to your MySQL password
    'database': 'tourist_recommender',
    'charset': 'utf8mb4'
}

def get_connection():
    """Create and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None

def get_cursor(conn):
    """Return a dictionary cursor."""
    return conn.cursor(dictionary=True)

def close_connection(conn, cursor=None):
    """Safely close cursor and connection."""
    try:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    except Error:
        pass

# ============================================
# QUERY FUNCTIONS
# ============================================

def get_all_destinations():
    """Fetch all destinations from database."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("SELECT * FROM destinations ORDER BY rating DESC")
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def get_destination_by_id(dest_id):
    """Fetch a single destination by ID."""
    conn = get_connection()
    if not conn:
        return None
    cursor = get_cursor(conn)
    try:
        cursor.execute("SELECT * FROM destinations WHERE id = %s", (dest_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        close_connection(conn, cursor)

def get_trending_destinations(limit=6):
    """Fetch trending destinations for homepage."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM destinations WHERE is_trending = TRUE ORDER BY rating DESC LIMIT %s",
            (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def get_top_rated(limit=6):
    """Fetch top-rated destinations."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM destinations ORDER BY rating DESC LIMIT %s", (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def get_hidden_gems(limit=6):
    """Fetch hidden gem destinations."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM destinations WHERE is_hidden_gem = TRUE ORDER BY rating DESC LIMIT %s",
            (limit,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def get_destinations_by_region(region):
    """Fetch destinations by region."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM destinations WHERE region = %s ORDER BY rating DESC", (region,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def search_by_name(query):
    """Search destinations by name (autocomplete)."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT id, place_name, state FROM destinations WHERE place_name LIKE %s LIMIT 10",
            (f"%{query}%",)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def increment_view_count(dest_id):
    """Increment view count when a destination detail page is visited."""
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "UPDATE destinations SET view_count = view_count + 1 WHERE id = %s", (dest_id,)
        )
        conn.commit()
    except Error as e:
        print(f"[DB ERROR] {e}")
    finally:
        close_connection(conn, cursor)

# ============================================
# WISHLIST FUNCTIONS
# ============================================

def add_to_wishlist(session_id, dest_id):
    """Add destination to wishlist."""
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        # Check if already exists
        cursor.execute(
            "SELECT id FROM wishlist WHERE session_id=%s AND destination_id=%s",
            (session_id, dest_id)
        )
        if cursor.fetchone():
            return 'exists'
        cursor.execute(
            "INSERT INTO wishlist (session_id, destination_id) VALUES (%s, %s)",
            (session_id, dest_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        close_connection(conn, cursor)

def remove_from_wishlist(session_id, dest_id):
    """Remove destination from wishlist."""
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "DELETE FROM wishlist WHERE session_id=%s AND destination_id=%s",
            (session_id, dest_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        close_connection(conn, cursor)

def get_wishlist(session_id):
    """Get all wishlist items for a session."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            SELECT d.*, w.saved_at
            FROM destinations d
            JOIN wishlist w ON d.id = w.destination_id
            WHERE w.session_id = %s
            ORDER BY w.saved_at DESC
        """, (session_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

# ============================================
# SEARCH HISTORY FUNCTIONS
# ============================================

def save_search_history(session_id, user_input, results_count):
    """Save user search to history."""
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)
    try:
        interests_str = ','.join(user_input.get('interests', [])) if user_input.get('interests') else None
        cursor.execute("""
            INSERT INTO search_history
            (session_id, budget, season, interests, region, travel_type,
             activity_level, trip_purpose, duration, crowd, age_group, results_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session_id,
            user_input.get('budget'),
            user_input.get('season'),
            interests_str,
            user_input.get('region'),
            user_input.get('travel_type'),
            user_input.get('activity_level'),
            user_input.get('trip_purpose'),
            user_input.get('duration'),
            user_input.get('crowd'),
            user_input.get('age_group'),
            results_count
        ))
        conn.commit()
    except Error as e:
        print(f"[DB ERROR] {e}")
    finally:
        close_connection(conn, cursor)

def get_search_history(session_id, limit=10):
    """Get user search history."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM search_history WHERE session_id=%s ORDER BY searched_at DESC LIMIT %s",
            (session_id, limit)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

# ============================================
# REVIEW FUNCTIONS
# ============================================

def add_review(dest_id, session_id, reviewer_name, rating, comment):
    """Add a user review."""
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            INSERT INTO reviews (destination_id, session_id, reviewer_name, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (dest_id, session_id, reviewer_name, rating, comment))
        # Update average rating
        cursor.execute("""
            UPDATE destinations SET rating = (
                SELECT AVG(rating) FROM reviews WHERE destination_id = %s
            ) WHERE id = %s
        """, (dest_id, dest_id))
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        close_connection(conn, cursor)

def get_reviews(dest_id):
    """Get reviews for a destination."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM reviews WHERE destination_id=%s ORDER BY reviewed_at DESC",
            (dest_id,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

# ============================================
# COMPARE FUNCTIONS
# ============================================

def get_compare_list(session_id):
    """Get compare list for session."""
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            SELECT d.* FROM destinations d
            JOIN compare_list c ON d.id = c.destination_id
            WHERE c.session_id = %s
        """, (session_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)

def add_to_compare(session_id, dest_id):
    """Add to compare list (max 3)."""
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM compare_list WHERE session_id=%s", (session_id,))
        count = cursor.fetchone()['cnt']
        if count >= 3:
            return 'full'
        cursor.execute(
            "INSERT IGNORE INTO compare_list (session_id, destination_id) VALUES (%s, %s)",
            (session_id, dest_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        close_connection(conn, cursor)

def clear_compare(session_id):
    """Clear compare list."""
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)
    try:
        cursor.execute("DELETE FROM compare_list WHERE session_id=%s", (session_id,))
        conn.commit()
    except Error as e:
        print(f"[DB ERROR] {e}")
    finally:
        close_connection(conn, cursor)
