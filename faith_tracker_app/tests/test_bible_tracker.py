# faith_tracker_app/tests/test_bible_tracker.py
import unittest
import sqlite3
import os
import datetime

# Temporarily adjust path to import app modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from faith_tracker_app.bible import bible_tracker
from faith_tracker_app.database import schema
from faith_tracker_app.database.connection import DATABASE_NAME as DEV_DB_NAME

# Use an in-memory SQLite database for testing
TEST_DB_NAME = ":memory:"

class TestBibleTracker(unittest.TestCase):

    def setUp(self):
        """Set up a new in-memory database for each test."""
        # Monkey patch the get_db_connection to use the in-memory DB for tests
        self.original_get_db_connection = bible_tracker.get_db_connection
        bible_tracker.get_db_connection = lambda: self.get_test_db_connection()

        self.conn = self.get_test_db_connection()
        self.cursor = self.conn.cursor()
        self._initialize_schema()

    def get_test_db_connection(self):
        conn = sqlite3.connect(TEST_DB_NAME)
        conn.row_factory = sqlite3.Row # Important for accessing columns by name
        return conn

    def _initialize_schema(self):
        """Initializes the database schema."""
        for table_schema in schema.ALL_TABLE_SCHEMAS:
            self.cursor.execute(table_schema)
        self.conn.commit()

    def tearDown(self):
        """Close the database connection and restore original get_db_connection."""
        self.conn.close()
        bible_tracker.get_db_connection = self.original_get_db_connection


    def test_add_bible_reading(self):
        reading_id = bible_tracker.add_bible_reading("Genesis", 1, 1, 5, "Creation")
        self.assertIsNotNone(reading_id, "Should return an ID on successful insert.")

        # Verify by fetching directly
        self.cursor.execute("SELECT * FROM bible_reading WHERE id = ?", (reading_id,))
        entry = self.cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry["book"], "Genesis")
        self.assertEqual(entry["chapter"], 1)
        self.assertEqual(entry["start_verse"], 1)
        self.assertEqual(entry["end_verse"], 5)
        self.assertEqual(entry["notes"], "Creation")
        # Check date is recent (within a small delta, e.g., 5 seconds)
        try:
            reading_date = datetime.datetime.strptime(entry["reading_date"], "%Y-%m-%d %H:%M:%S")
            self.assertTrue(datetime.datetime.now() - reading_date < datetime.timedelta(seconds=5))
        except ValueError:
            self.fail("reading_date format is incorrect in the database.")


    def test_add_bible_reading_minimal(self):
        reading_id = bible_tracker.add_bible_reading("Psalm", 23)
        self.assertIsNotNone(reading_id)

        self.cursor.execute("SELECT * FROM bible_reading WHERE id = ?", (reading_id,))
        entry = self.cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry["book"], "Psalm")
        self.assertEqual(entry["chapter"], 23)
        self.assertIsNone(entry["start_verse"])
        self.assertIsNone(entry["end_verse"])
        self.assertIsNone(entry["notes"])

    def test_get_all_bible_readings(self):
        bible_tracker.add_bible_reading("John", 1, 1, 10)
        # Adding a slight delay to ensure distinct timestamps for ordering test
        import time
        time.sleep(0.01)
        bible_tracker.add_bible_reading("Acts", 2, 1, 4)

        readings = bible_tracker.get_all_bible_readings()
        self.assertEqual(len(readings), 2)
        # Readings should be ordered by date DESC, so Acts should be first
        self.assertEqual(readings[0]["book"], "Acts")
        self.assertEqual(readings[1]["book"], "John")

    def test_get_all_bible_readings_limit(self):
        bible_tracker.add_bible_reading("1 Corinthians", 13)
        time.sleep(0.01)
        bible_tracker.add_bible_reading("Ephesians", 2)
        time.sleep(0.01)
        bible_tracker.add_bible_reading("Philippians", 4)

        readings = bible_tracker.get_all_bible_readings(limit=2)
        self.assertEqual(len(readings), 2)
        self.assertEqual(readings[0]["book"], "Philippians") # Most recent
        self.assertEqual(readings[1]["book"], "Ephesians")

    def test_get_all_bible_readings_empty(self):
        readings = bible_tracker.get_all_bible_readings()
        self.assertEqual(len(readings), 0)

    def test_format_reading_for_display(self):
        # Full entry
        reading1 = {"id": 1, "reading_date": "2023-01-01 10:00:00", "book": "Genesis", "chapter": 1, "start_verse": 1, "end_verse": 5, "notes": "Creation"}
        self.assertEqual(bible_tracker.format_reading_for_display(reading1), "[1] 2023-01-01 10:00 AM - Genesis 1:1-5 (Notes: Creation)")

        # Chapter only
        reading2 = {"id": 2, "reading_date": "2023-01-02 11:00:00", "book": "Psalm", "chapter": 23, "start_verse": None, "end_verse": None, "notes": None}
        self.assertEqual(bible_tracker.format_reading_for_display(reading2), "[2] 2023-01-02 11:00 AM - Psalm 23")

        # Start verse only
        reading3 = {"id": 3, "reading_date": "2023-01-03 12:00:00", "book": "John", "chapter": 3, "start_verse": 16, "end_verse": None, "notes": "Famous verse"}
        self.assertEqual(bible_tracker.format_reading_for_display(reading3), "[3] 2023-01-03 12:00 PM - John 3:16 (Notes: Famous verse)")

        # Start and end verse same
        reading4 = {"id": 4, "reading_date": "2023-01-04 13:00:00", "book": "Matthew", "chapter": 5, "start_verse": 3, "end_verse": 3, "notes": "Beatitude"}
        self.assertEqual(bible_tracker.format_reading_for_display(reading4), "[4] 2023-01-04 13:00 PM - Matthew 5:3 (Notes: Beatitude)")


if __name__ == '__main__':
    # This is to ensure that if this file is run directly, it can find the modules
    # It's better to run tests using `python -m unittest discover faith_tracker_app.tests`
    unittest.main()
