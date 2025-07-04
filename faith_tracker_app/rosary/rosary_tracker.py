# faith_tracker_app/rosary/rosary_tracker.py
import datetime
from faith_tracker_app.database.connection import get_db_connection

def log_rosary_prayer(prayer_date: str = None, mysteries: str = None, notes: str = None):
    """
    Logs a Rosary prayer session.
    If prayer_date is None, the current date is used.
    prayer_date should be in 'YYYY-MM-DD' format if provided.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if prayer_date is None:
        prayer_date = datetime.date.today().strftime("%Y-%m-%d")
    else:
        # Validate date format
        try:
            datetime.datetime.strptime(prayer_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid prayer_date format. Please use YYYY-MM-DD.")
            conn.close()
            return None

    try:
        cursor.execute("""
            INSERT INTO rosary_prayers (prayer_date, mysteries, notes)
            VALUES (?, ?, ?)
        """, (prayer_date, mysteries, notes))
        conn.commit()
        print(f"Successfully logged Rosary prayer for {prayer_date}" +
              (f" (Mysteries: {mysteries})" if mysteries else "") +
              (f" - Notes: {notes}" if notes else "")
             )
        return cursor.lastrowid
    except Exception as e:
        print(f"Error logging Rosary prayer: {e}")
        return None
    finally:
        conn.close()

def get_rosary_prayer_history(limit: int = None):
    """
    Retrieves all Rosary prayer entries, ordered by prayer_date descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id, prayer_date, mysteries, notes, created_at FROM rosary_prayers ORDER BY prayer_date DESC, created_at DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    try:
        cursor.execute(query)
        prayers = cursor.fetchall()
        return [dict(row) for row in prayers]
    except Exception as e:
        print(f"Error retrieving Rosary prayer history: {e}")
        return []
    finally:
        conn.close()

def format_rosary_log_for_display(log_entry: dict):
    """Formats a single rosary log entry dictionary for display."""
    mysteries_info = f" - Mysteries: {log_entry['mysteries']}" if log_entry['mysteries'] else ""
    notes_info = f" - Notes: {log_entry['notes']}" if log_entry['notes'] else ""

    # Parse date for friendlier format if needed, though it's already YYYY-MM-DD
    # For consistency, let's ensure it's just the date part
    try:
        date_obj = datetime.datetime.strptime(log_entry['prayer_date'], "%Y-%m-%d")
        formatted_date = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        formatted_date = log_entry['prayer_date'] # Fallback

    return f"[{log_entry['id']}] {formatted_date}{mysteries_info}{notes_info}"

if __name__ == '__main__':
    # This block is for testing the module directly
    from faith_tracker_app.database.connection import initialize_database
    initialize_database() # Make sure tables exist

    print("\n--- Testing Rosary Tracker ---")

    # Test logging prayers
    log_rosary_prayer(mysteries="Joyful", notes="Morning prayer")
    log_rosary_prayer(prayer_date="2023-10-25", mysteries="Sorrowful")
    log_rosary_prayer(prayer_date="2023-10-20", notes="Evening Rosary")
    log_rosary_prayer(mysteries="Glorious")

    # Test retrieving and displaying history
    print("\nRosary Prayer History (Most Recent First):")
    all_prayers = get_rosary_prayer_history()
    if all_prayers:
        for prayer in all_prayers:
            print(format_rosary_log_for_display(prayer))
    else:
        print("No Rosary prayers logged yet.")

    print("\nTop 2 Rosary Prayers:")
    top_prayers = get_rosary_prayer_history(limit=2)
    if top_prayers:
        for prayer in top_prayers:
            print(format_rosary_log_for_display(prayer))
    else:
        print("No Rosary prayers logged yet.")

    # Test invalid date format
    print("\nTesting invalid date format:")
    log_rosary_prayer(prayer_date="26-10-2023")

    print("\n--- End Rosary Tracker Test ---")
