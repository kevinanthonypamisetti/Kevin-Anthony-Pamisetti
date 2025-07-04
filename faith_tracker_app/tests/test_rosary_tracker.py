# faith_tracker_app/tests/test_rosary_tracker.py
import unittest
import sqlite3
import os
import datetime

# Temporarily adjust path to import app modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from faith_tracker_app.rosary import rosary_tracker
from faith_tracker_app.database import schema

TEST_DB_NAME = ":memory:"

class TestRosaryTracker(unittest.TestCase):

    def setUp(self):
        """Set up a new in-memory database for each test."""
        self.original_get_db_connection = rosary_tracker.get_db_connection
        rosary_tracker.get_db_connection = lambda: self.get_test_db_connection()

        self.conn = self.get_test_db_connection()
        self.cursor = self.conn.cursor()
        self._initialize_schema()

    def get_test_db_connection(self):
        conn = sqlite3.connect(TEST_DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self):
        for table_schema in schema.ALL_TABLE_SCHEMAS:
            self.cursor.execute(table_schema)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        rosary_tracker.get_db_connection = self.original_get_db_connection

    def test_log_rosary_prayer_today_default_date(self):
        log_id = rosary_tracker.log_rosary_prayer(mysteries="Joyful", notes="Morning")
        self.assertIsNotNone(log_id)

        self.cursor.execute("SELECT * FROM rosary_prayers WHERE id = ?", (log_id,))
        entry = self.cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry["prayer_date"], datetime.date.today().strftime("%Y-%m-%d"))
        self.assertEqual(entry["mysteries"], "Joyful")
        self.assertEqual(entry["notes"], "Morning")

    def test_log_rosary_prayer_specific_date(self):
        test_date = "2023-03-15"
        log_id = rosary_tracker.log_rosary_prayer(prayer_date=test_date, mysteries="Sorrowful")
        self.assertIsNotNone(log_id)

        self.cursor.execute("SELECT * FROM rosary_prayers WHERE id = ?", (log_id,))
        entry = self.cursor.fetchone()
        self.assertEqual(entry["prayer_date"], test_date)
        self.assertEqual(entry["mysteries"], "Sorrowful")

    def test_log_rosary_prayer_invalid_date_format(self):
        log_id = rosary_tracker.log_rosary_prayer(prayer_date="15-03-2023")
        self.assertIsNone(log_id, "Should return None for invalid date format.")
        # Also check that nothing was inserted
        self.cursor.execute("SELECT COUNT(*) FROM rosary_prayers WHERE prayer_date = '15-03-2023'")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)


    def test_get_rosary_prayer_history(self):
        rosary_tracker.log_rosary_prayer(prayer_date="2023-10-01", mysteries="Joyful")
        import time; time.sleep(0.01) # Ensure created_at is different for ordering
        rosary_tracker.log_rosary_prayer(prayer_date="2023-10-03", mysteries="Glorious")
        import time; time.sleep(0.01)
        rosary_tracker.log_rosary_prayer(prayer_date="2023-10-02", mysteries="Sorrowful")

        history = rosary_tracker.get_rosary_prayer_history()
        self.assertEqual(len(history), 3)
        # Ordered by prayer_date DESC, then created_at DESC
        self.assertEqual(history[0]["mysteries"], "Glorious") # 2023-10-03
        self.assertEqual(history[1]["mysteries"], "Sorrowful") # 2023-10-02
        self.assertEqual(history[2]["mysteries"], "Joyful")    # 2023-10-01

    def test_get_rosary_prayer_history_same_date_ordering(self):
        # Log two entries for the same date, ensure created_at ordering
        today = datetime.date.today().strftime("%Y-%m-%d")
        rosary_tracker.log_rosary_prayer(prayer_date=today, mysteries="First")
        import time; time.sleep(0.02) # Ensure distinct created_at
        rosary_tracker.log_rosary_prayer(prayer_date=today, mysteries="Second")

        history = rosary_tracker.get_rosary_prayer_history(limit=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["mysteries"], "Second") # Logged later
        self.assertEqual(history[1]["mysteries"], "First")  # Logged earlier


    def test_get_rosary_prayer_history_limit(self):
        rosary_tracker.log_rosary_prayer(prayer_date="2023-09-01")
        import time; time.sleep(0.01)
        rosary_tracker.log_rosary_prayer(prayer_date="2023-09-03")
        import time; time.sleep(0.01)
        rosary_tracker.log_rosary_prayer(prayer_date="2023-09-02")

        history = rosary_tracker.get_rosary_prayer_history(limit=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["prayer_date"], "2023-09-03")
        self.assertEqual(history[1]["prayer_date"], "2023-09-02")

    def test_get_rosary_prayer_history_empty(self):
        history = rosary_tracker.get_rosary_prayer_history()
        self.assertEqual(len(history), 0)

    def test_format_rosary_log_for_display(self):
        log1 = {"id": 1, "prayer_date": "2023-01-01", "mysteries": "Joyful", "notes": "With family", "created_at": "2023-01-01 10:00:00"}
        self.assertEqual(rosary_tracker.format_rosary_log_for_display(log1), "[1] 2023-01-01 - Mysteries: Joyful - Notes: With family")

        log2 = {"id": 2, "prayer_date": "2023-01-02", "mysteries": None, "notes": "Quick one", "created_at": "2023-01-02 11:00:00"}
        self.assertEqual(rosary_tracker.format_rosary_log_for_display(log2), "[2] 2023-01-02 - Notes: Quick one")

        log3 = {"id": 3, "prayer_date": "2023-01-03", "mysteries": "Luminous", "notes": None, "created_at": "2023-01-03 12:00:00"}
        self.assertEqual(rosary_tracker.format_rosary_log_for_display(log3), "[3] 2023-01-03 - Mysteries: Luminous")

        log4 = {"id": 4, "prayer_date": "2023-01-04", "mysteries": None, "notes": None, "created_at": "2023-01-04 13:00:00"}
        self.assertEqual(rosary_tracker.format_rosary_log_for_display(log4), "[4] 2023-01-04")


if __name__ == '__main__':
    unittest.main()
