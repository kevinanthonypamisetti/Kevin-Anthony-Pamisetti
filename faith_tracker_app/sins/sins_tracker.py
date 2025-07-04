# faith_tracker_app/sins/sins_tracker.py
import datetime
from faith_tracker_app.database.connection import get_db_connection

def add_sin_entry(sin_description: str, occurrence_date: str = None, notes: str = None):
    """
    Adds a new sin entry to the log.
    occurrence_date should be in 'YYYY-MM-DD' format if provided.
    Sins are initially marked as not confessed.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if occurrence_date:
        try:
            datetime.datetime.strptime(occurrence_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid occurrence_date format. Please use YYYY-MM-DD.")
            conn.close()
            return None

    try:
        cursor.execute("""
            INSERT INTO sins_confession_log (sin_description, occurrence_date, confessed, notes)
            VALUES (?, ?, FALSE, ?)
        """, (sin_description, occurrence_date, notes))
        conn.commit()
        print(f"Successfully added sin entry: '{sin_description}'")
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding sin entry: {e}")
        return None
    finally:
        conn.close()

def mark_sin_as_confessed(entry_id: int, confession_date: str = None):
    """
    Marks a specific sin entry as confessed.
    confession_date should be in 'YYYY-MM-DD' format. If None, current date is used.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if confession_date is None:
        confession_date = datetime.date.today().strftime("%Y-%m-%d")
    else:
        try:
            datetime.datetime.strptime(confession_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid confession_date format. Please use YYYY-MM-DD.")
            conn.close()
            return False

    try:
        cursor.execute("""
            UPDATE sins_confession_log
            SET confessed = TRUE, confession_date = ?
            WHERE id = ? AND confessed = FALSE
        """, (confession_date, entry_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Sin entry ID {entry_id} marked as confessed on {confession_date}.")
            return True
        else:
            # Could be ID not found, or already confessed
            cursor.execute("SELECT confessed FROM sins_confession_log WHERE id = ?", (entry_id,))
            result = cursor.fetchone()
            if result and result['confessed']:
                print(f"Sin entry ID {entry_id} was already marked as confessed.")
            else:
                print(f"Sin entry ID {entry_id} not found or could not be updated.")
            return False
    except Exception as e:
        print(f"Error marking sin as confessed: {e}")
        return False
    finally:
        conn.close()

def get_sin_log(show_all: bool = True, show_confessed: bool = True, limit: int = None):
    """
    Retrieves sin entries.
    - show_all: If True, ignores show_confessed and returns all.
    - show_confessed: If False and show_all is False, only shows unconfessed sins.
                      If True and show_all is False, only shows confessed sins.
    Ordered by created_at descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = "SELECT id, sin_description, occurrence_date, confessed, confession_date, notes, created_at FROM sins_confession_log"
    filters = []
    params = []

    if not show_all:
        if show_confessed:
            filters.append("confessed = TRUE")
        else:
            filters.append("confessed = FALSE")

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY created_at DESC"

    if limit:
        base_query += f" LIMIT {int(limit)}"

    try:
        cursor.execute(base_query, tuple(params))
        entries = cursor.fetchall()
        return [dict(row) for row in entries]
    except Exception as e:
        print(f"Error retrieving sin log: {e}")
        return []
    finally:
        conn.close()

def format_sin_entry_for_display(entry: dict):
    """Formats a single sin entry dictionary for display."""
    status = "Confessed" if entry['confessed'] else "Not Confessed"
    occurrence_info = f" (Occurred: {entry['occurrence_date']})" if entry['occurrence_date'] else ""
    confession_info = f" (Confessed on: {entry['confession_date']})" if entry['confessed'] and entry['confession_date'] else ""
    notes_info = f" - Notes: {entry['notes']}" if entry['notes'] else ""

    return (f"[{entry['id']}] {status} - \"{entry['sin_description']}\""
            f"{occurrence_info}{confession_info}{notes_info}"
            f" (Logged: {entry['created_at'][:10]})")


if __name__ == '__main__':
    from faith_tracker_app.database.connection import initialize_database
    initialize_database()

    print("\n--- Testing Sins Tracker ---")

    # Add entries
    id1 = add_sin_entry("Lied about finishing chores", occurrence_date="2023-10-25", notes="To avoid trouble")
    id2 = add_sin_entry("Skipped morning prayer", notes="Felt lazy")
    id3 = add_sin_entry("Had an uncharitable thought", occurrence_date="2023-10-26")

    print("\n--- Current Sin Log (All - Most Recent First) ---")
    all_sins = get_sin_log()
    for sin in all_sins:
        print(format_sin_entry_for_display(sin))

    if id1:
        mark_sin_as_confessed(id1, "2023-10-27")
    if id2: # Try marking already confessed (or non-existent if id1 failed)
        mark_sin_as_confessed(id1, "2023-10-28") # Try to mark id1 again

    if id3: # Mark with default date
        mark_sin_as_confessed(id3)


    print("\n--- Unconfessed Sins ---")
    unconfessed_sins = get_sin_log(show_all=False, show_confessed=False)
    for sin in unconfessed_sins:
        print(format_sin_entry_for_display(sin))

    print("\n--- Confessed Sins ---")
    confessed_sins = get_sin_log(show_all=False, show_confessed=True)
    for sin in confessed_sins:
        print(format_sin_entry_for_display(sin))

    print("\n--- Testing invalid date ---")
    add_sin_entry("Test with bad date", occurrence_date="bad-date")
    if id2:
        mark_sin_as_confessed(id2, confession_date="another-bad-date")


    print("\n--- End Sins Tracker Test ---")
