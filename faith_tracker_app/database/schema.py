# faith_tracker_app/database/schema.py

BIBLE_READING_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS bible_reading (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    start_verse INTEGER,
    end_verse INTEGER,
    reading_date TEXT NOT NULL, -- ISO format YYYY-MM-DD HH:MM:SS
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

ROSARY_PRAYERS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS rosary_prayers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prayer_date TEXT NOT NULL, -- ISO format YYYY-MM-DD
    mysteries TEXT, -- Joyful, Sorrowful, Glorious, Luminous (optional)
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

SINS_CONFESSION_LOG_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS sins_confession_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sin_description TEXT NOT NULL,
    occurrence_date TEXT, -- ISO format YYYY-MM-DD (optional)
    confessed BOOLEAN DEFAULT FALSE,
    confession_date TEXT, -- ISO format YYYY-MM-DD (optional, if confessed)
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

# List of all schemas to be created
ALL_TABLE_SCHEMAS = [
    BIBLE_READING_TABLE_SCHEMA,
    ROSARY_PRAYERS_TABLE_SCHEMA,
    SINS_CONFESSION_LOG_TABLE_SCHEMA,
]

if __name__ == "__main__":
    # This part is for testing or manual setup if needed
    # It won't be directly run by the main application normally
    import sqlite3
    DB_NAME = "faith_tracker.db"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for schema in ALL_TABLE_SCHEMAS:
        cursor.execute(schema)
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized with tables.")
