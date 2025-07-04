# faith_tracker_app/ui/cli.py

from faith_tracker_app.bible import bible_tracker
from faith_tracker_app.rosary import rosary_tracker
from faith_tracker_app.sins import sins_tracker
from faith_tracker_app.database import connection as db_connection

def get_user_input(prompt, default_value=None):
    """Gets user input, allowing for a default value if input is empty."""
    user_input = input(f"{prompt}: ").strip()
    if not user_input and default_value is not None:
        return default_value
    return user_input

def get_int_input(prompt, allow_empty=False):
    """Gets integer input from the user, ensuring it's a valid integer."""
    while True:
        user_input = input(f"{prompt}: ").strip()
        if not user_input and allow_empty:
            return None
        try:
            return int(user_input)
        except ValueError:
            print("Invalid input. Please enter a whole number.")

def get_date_input(prompt, allow_empty=False):
    """Gets date input from the user in YYYY-MM-DD format."""
    import datetime
    while True:
        date_str = input(f"{prompt} (YYYY-MM-DD, leave empty for today/none): ").strip()
        if not date_str and allow_empty:
            return None
        if not date_str and not allow_empty: # Default to today if not allowing empty and user presses enter
             return datetime.date.today().strftime("%Y-%m-%d")
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def bible_menu():
    while True:
        print("\n--- Bible Reading Tracker ---")
        print("1. Add New Bible Reading")
        print("2. View All Bible Readings")
        print("3. View Latest Bible Readings (specify N)")
        print("0. Back to Main Menu")
        choice = get_user_input("Choose an option")

        if choice == '1':
            print("\n-- Add New Bible Reading --")
            book = get_user_input("Book")
            chapter = get_int_input("Chapter")
            start_verse = get_int_input("Start Verse (optional, press Enter to skip)", allow_empty=True)
            end_verse = get_int_input("End Verse (optional, press Enter to skip)", allow_empty=True)
            notes = get_user_input("Notes (optional)")
            if book and chapter is not None: # Chapter can be 0, so check for None
                bible_tracker.add_bible_reading(book, chapter, start_verse, end_verse, notes)
            else:
                print("Book and Chapter are required.")
        elif choice == '2':
            print("\n-- All Bible Readings --")
            readings = bible_tracker.get_all_bible_readings()
            if readings:
                for r in readings:
                    print(bible_tracker.format_reading_for_display(r))
            else:
                print("No Bible readings found.")
        elif choice == '3':
            print("\n-- Latest Bible Readings --")
            num = get_int_input("How many latest readings to show?")
            if num is not None and num > 0:
                readings = bible_tracker.get_all_bible_readings(limit=num)
                if readings:
                    for r in readings:
                        print(bible_tracker.format_reading_for_display(r))
                else:
                    print("No Bible readings found.")
            elif num == 0:
                print("Showing 0 readings.")
            else:
                print("Invalid number.")
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def rosary_menu():
    while True:
        print("\n--- Rosary Prayer Tracker ---")
        print("1. Log Rosary Prayer")
        print("2. View Rosary Prayer History")
        print("3. View Latest Rosary Prayers (specify N)")
        print("0. Back to Main Menu")
        choice = get_user_input("Choose an option")

        if choice == '1':
            print("\n-- Log Rosary Prayer --")
            prayer_date = get_date_input("Date of prayer (YYYY-MM-DD, leave empty for today)", allow_empty=True)
            if not prayer_date: # If user left empty, default to today
                import datetime
                prayer_date = datetime.date.today().strftime("%Y-%m-%d")

            mysteries = get_user_input("Mysteries (e.g., Joyful, Sorrowful, optional)")
            notes = get_user_input("Notes (optional)")
            rosary_tracker.log_rosary_prayer(prayer_date=prayer_date if prayer_date else None, mysteries=mysteries if mysteries else None, notes=notes if notes else None)
        elif choice == '2':
            print("\n-- Rosary Prayer History --")
            prayers = rosary_tracker.get_rosary_prayer_history()
            if prayers:
                for p in prayers:
                    print(rosary_tracker.format_rosary_log_for_display(p))
            else:
                print("No Rosary prayers logged.")
        elif choice == '3':
            print("\n-- Latest Rosary Prayers --")
            num = get_int_input("How many latest prayer logs to show?")
            if num is not None and num > 0:
                prayers = rosary_tracker.get_rosary_prayer_history(limit=num)
                if prayers:
                    for p in prayers:
                        print(rosary_tracker.format_rosary_log_for_display(p))
                else:
                    print("No Rosary prayers logged.")
            elif num == 0:
                print("Showing 0 prayer logs.")
            else:
                print("Invalid number.")
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")

def sins_menu():
    while True:
        print("\n--- Sin Log & Confession Tracker ---")
        print("1. Add New Sin Entry")
        print("2. Mark Sin as Confessed")
        print("3. View All Sin Entries")
        print("4. View Unconfessed Sin Entries")
        print("5. View Confessed Sin Entries")
        print("0. Back to Main Menu")
        choice = get_user_input("Choose an option")

        if choice == '1':
            print("\n-- Add New Sin Entry --")
            description = get_user_input("Sin Description")
            if not description:
                print("Description cannot be empty.")
                continue
            occurrence_date = get_date_input("Occurrence Date (YYYY-MM-DD, optional, press Enter to skip)", allow_empty=True)
            notes = get_user_input("Notes (optional)")
            sins_tracker.add_sin_entry(description, occurrence_date=occurrence_date if occurrence_date else None, notes=notes if notes else None)
        elif choice == '2':
            print("\n-- Mark Sin as Confessed --")
            entry_id = get_int_input("Enter ID of sin entry to mark as confessed")
            if entry_id is not None:
                confession_date = get_date_input("Confession Date (YYYY-MM-DD, leave empty for today)", allow_empty=True)
                sins_tracker.mark_sin_as_confessed(entry_id, confession_date=confession_date if confession_date else None)
            else:
                print("Invalid ID.")
        elif choice == '3': # View All
            print("\n-- All Sin Entries --")
            entries = sins_tracker.get_sin_log(show_all=True)
            if entries:
                for e in entries:
                    print(sins_tracker.format_sin_entry_for_display(e))
            else:
                print("No sin entries found.")
        elif choice == '4': # View Unconfessed
            print("\n-- Unconfessed Sin Entries --")
            entries = sins_tracker.get_sin_log(show_all=False, show_confessed=False)
            if entries:
                for e in entries:
                    print(sins_tracker.format_sin_entry_for_display(e))
            else:
                print("No unconfessed sin entries found.")
        elif choice == '5': # View Confessed
            print("\n-- Confessed Sin Entries --")
            entries = sins_tracker.get_sin_log(show_all=False, show_confessed=True)
            if entries:
                for e in entries:
                    print(sins_tracker.format_sin_entry_for_display(e))
            else:
                print("No confessed sin entries found.")
        elif choice == '0':
            break
        else:
            print("Invalid option. Please try again.")


def main_menu():
    # Initialize database on startup
    print("Initializing database...")
    db_connection.initialize_database()
    print("Welcome to the Faith Tracker App!")

    while True:
        print("\n--- Main Menu ---")
        print("1. Bible Reading Tracker")
        print("2. Rosary Prayer Tracker")
        print("3. Sin Log & Confession Tracker")
        print("0. Exit")

        choice = get_user_input("Choose an option")

        if choice == '1':
            bible_menu()
        elif choice == '2':
            rosary_menu()
        elif choice == '3':
            sins_menu()
        elif choice == '0':
            print("Exiting Faith Tracker App. God bless!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == '__main__':
    # This allows running the CLI directly for testing if needed,
    # though the main entry point will be app.py
    main_menu()
