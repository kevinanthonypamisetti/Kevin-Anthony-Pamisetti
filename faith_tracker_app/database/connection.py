# faith_tracker_app/database/connection.py
import sqlite3
import os

DATABASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(DATABASE_DIR, "faith_tracker.db")

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def initialize_database():
    """Initializes the database with the defined schema if it doesn't exist."""
    # Import schemas here to avoid circular imports if schema.py needs connection
    from .schema import ALL_TABLE_SCHEMAS

    conn = get_db_connection()
    cursor = conn.cursor()
    for schema_query in ALL_TABLE_SCHEMAS:
        cursor.execute(schema_query)
    conn.commit()
    conn.close()
    print(f"Database at {DATABASE_NAME} initialized/verified.")

if __name__ == '__main__':
    # This will create and initialize the DB when this script is run directly
    initialize_database()
