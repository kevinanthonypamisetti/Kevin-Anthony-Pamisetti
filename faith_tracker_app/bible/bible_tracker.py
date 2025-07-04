# faith_tracker_app/bible/bible_tracker.py
import datetime
from faith_tracker_app.database.connection import get_db_connection

def add_bible_reading(book: str, chapter: int, start_verse: int = None, end_verse: int = None, notes: str = None):
    """
    Adds a new Bible reading entry to the database.
    Date of reading is automatically set to the current date and time.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    reading_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
            INSERT INTO bible_reading (book, chapter, start_verse, end_verse, reading_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (book, chapter, start_verse, end_verse, reading_date, notes))
        conn.commit()
        print(f"Successfully added reading: {book} {chapter}" +
              (f":{start_verse}" if start_verse else "") +
              (f"-{end_verse}" if end_verse and start_verse else "") +
              (f":{end_verse}" if end_verse and not start_verse else "")
             )
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding Bible reading: {e}")
        return None
    finally:
        conn.close()

def get_all_bible_readings(limit: int = None):
    """
    Retrieves all Bible reading entries, ordered by reading_date descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id, book, chapter, start_verse, end_verse, reading_date, notes FROM bible_reading ORDER BY reading_date DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    try:
        cursor.execute(query)
        readings = cursor.fetchall()
        # Convert sqlite3.Row objects to dictionaries for easier use
        return [dict(row) for row in readings]
    except Exception as e:
        print(f"Error retrieving Bible readings: {e}")
        return []
    finally:
        conn.close()

def format_reading_for_display(reading: dict):
    """Formats a single reading dictionary for display."""
    verse_info = ""
    if reading['start_verse'] and reading['end_verse']:
        if reading['start_verse'] == reading['end_verse']:
            verse_info = f":{reading['start_verse']}"
        else:
            verse_info = f":{reading['start_verse']}-{reading['end_verse']}"
    elif reading['start_verse']:
        verse_info = f":{reading['start_verse']}"
    elif reading['end_verse']: # Unlikely scenario if start_verse is None, but handle
        verse_info = f" (verse {reading['end_verse']})"

    notes_info = f" (Notes: {reading['notes']})" if reading['notes'] else ""
    # Parse date for friendlier format
    try:
        date_obj = datetime.datetime.strptime(reading['reading_date'], "%Y-%m-%d %H:%M:%S")
        formatted_date = date_obj.strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        formatted_date = reading['reading_date'] # Fallback to raw date string

    return f"[{reading['id']}] {formatted_date} - {reading['book']} {reading['chapter']}{verse_info}{notes_info}"

if __name__ == '__main__':
    # This block is for testing the module directly
    # Ensure the database is initialized first by running connection.py or initialize_database()
    from faith_tracker_app.database.connection import initialize_database
    initialize_database() # Make sure tables exist

    print("\n--- Testing Bible Tracker ---")

    # Test adding entries
    add_bible_reading("Genesis", 1, 1, 31, "Creation story")
    add_bible_reading("John", 3, 16, notes="For God so loved the world...")
    add_bible_reading("Psalm", 23)
    add_bible_reading("Matthew", 5, 1, 12) # Sermon on the Mount opening

    # Test retrieving and displaying entries
    print("\nAll Bible Readings (Most Recent First):")
    all_readings = get_all_bible_readings()
    if all_readings:
        for reading in all_readings:
            print(format_reading_for_display(reading))
    else:
        print("No readings found.")

    print("\nTop 2 Bible Readings:")
    top_readings = get_all_bible_readings(limit=2)
    if top_readings:
        for reading in top_readings:
            print(format_reading_for_display(reading))
    else:
        print("No readings found.")

    print("\n--- End Bible Tracker Test ---")
