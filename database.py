# ============================================
# DATABASE CONNECTION & SETUP
# Tourist Place Recommendation System (SQLite)
# ============================================

import sqlite3


def get_connection():
    try:
        conn = sqlite3.connect("tourist.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


def get_cursor(conn):
    return conn.cursor()


def close_connection(conn, cursor=None):
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    except:
        pass


# ============================================
# QUERY FUNCTIONS
# ============================================

def get_all_destinations():
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("SELECT * FROM destinations ORDER BY rating DESC")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def get_destination_by_id(dest_id):
    conn = get_connection()
    if not conn:
        return None
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM destinations WHERE id = ?",
            (dest_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        close_connection(conn, cursor)


def get_trending_destinations(limit=6):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            f"SELECT * FROM destinations WHERE is_trending = 1 ORDER BY rating DESC LIMIT {limit}"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def get_top_rated(limit=6):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            f"SELECT * FROM destinations ORDER BY rating DESC LIMIT {limit}"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def get_hidden_gems(limit=6):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            f"SELECT * FROM destinations WHERE is_hidden_gem = 1 ORDER BY rating DESC LIMIT {limit}"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def search_by_name(query):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT id, place_name, state FROM destinations WHERE place_name LIKE ? LIMIT 10",
            (f"%{query}%",)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def increment_view_count(dest_id):
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "UPDATE destinations SET view_count = view_count + 1 WHERE id = ?",
            (dest_id,)
        )
        conn.commit()
    finally:
        close_connection(conn, cursor)


# ============================================
# WISHLIST
# ============================================

def add_to_wishlist(session_id, dest_id):
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT id FROM wishlist WHERE session_id=? AND destination_id=?",
            (session_id, dest_id)
        )
        if cursor.fetchone():
            return 'exists'

        cursor.execute(
            "INSERT INTO wishlist (session_id, destination_id) VALUES (?, ?)",
            (session_id, dest_id)
        )
        conn.commit()
        return True
    finally:
        close_connection(conn, cursor)


def remove_from_wishlist(session_id, dest_id):
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "DELETE FROM wishlist WHERE session_id=? AND destination_id=?",
            (session_id, dest_id)
        )
        conn.commit()
        return True
    finally:
        close_connection(conn, cursor)


def get_wishlist(session_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            SELECT d.*, w.saved_at
            FROM destinations d
            JOIN wishlist w ON d.id = w.destination_id
            WHERE w.session_id = ?
            ORDER BY w.saved_at DESC
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


# ============================================
# SEARCH HISTORY
# ============================================

def save_search_history(session_id, user_input, results_count):
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)

    interests_str = ','.join(
        user_input.get('interests', [])
    ) if user_input.get('interests') else None

    try:
        cursor.execute("""
            INSERT INTO search_history
            (session_id, budget, season, interests, region,
             travel_type, activity_level, trip_purpose,
             duration, crowd, age_group, results_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    finally:
        close_connection(conn, cursor)


def get_search_history(session_id, limit=10):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            f"SELECT * FROM search_history WHERE session_id=? ORDER BY searched_at DESC LIMIT {limit}",
            (session_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


# ============================================
# REVIEWS
# ============================================

def add_review(dest_id, session_id, reviewer_name, rating, comment):
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            INSERT INTO reviews
            (destination_id, session_id, reviewer_name, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (
            dest_id, session_id, reviewer_name, rating, comment
        ))

        cursor.execute("""
            UPDATE destinations
            SET rating = (
                SELECT AVG(rating)
                FROM reviews
                WHERE destination_id = ?
            )
            WHERE id = ?
        """, (dest_id, dest_id))

        conn.commit()
        return True
    finally:
        close_connection(conn, cursor)


def get_reviews(dest_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute(
            "SELECT * FROM reviews WHERE destination_id=? ORDER BY reviewed_at DESC",
            (dest_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


# ============================================
# COMPARE
# ============================================

def get_compare_list(session_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = get_cursor(conn)
    try:
        cursor.execute("""
            SELECT d.*
            FROM destinations d
            JOIN compare_list c
            ON d.id = c.destination_id
            WHERE c.session_id = ?
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        close_connection(conn, cursor)


def add_to_compare(session_id, dest_id):
    conn = get_connection()
    if not conn:
        return False
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM compare_list WHERE session_id=?",
            (session_id,)
        )
        count = cursor.fetchone()[0]

        if count >= 3:
            return 'full'

        cursor.execute(
            "INSERT OR IGNORE INTO compare_list (session_id, destination_id) VALUES (?, ?)",
            (session_id, dest_id)
        )

        conn.commit()
        return True
    finally:
        close_connection(conn, cursor)


def clear_compare(session_id):
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)

    try:
        cursor.execute(
            "DELETE FROM compare_list WHERE session_id=?",
            (session_id,)
        )
        conn.commit()
    finally:
        close_connection(conn, cursor)