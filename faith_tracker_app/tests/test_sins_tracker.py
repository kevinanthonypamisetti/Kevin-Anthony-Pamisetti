# faith_tracker_app/tests/test_sins_tracker.py
import unittest
import sqlite3
import os
import datetime

# Temporarily adjust path to import app modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from faith_tracker_app.sins import sins_tracker
from faith_tracker_app.database import schema

TEST_DB_NAME = ":memory:"

class TestSinsTracker(unittest.TestCase):

    def setUp(self):
        self.original_get_db_connection = sins_tracker.get_db_connection
        sins_tracker.get_db_connection = lambda: self.get_test_db_connection()

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
        sins_tracker.get_db_connection = self.original_get_db_connection

    def test_add_sin_entry(self):
        entry_id = sins_tracker.add_sin_entry("Test sin", occurrence_date="2023-04-01", notes="A note")
        self.assertIsNotNone(entry_id)

        self.cursor.execute("SELECT * FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertIsNotNone(entry)
        self.assertEqual(entry["sin_description"], "Test sin")
        self.assertEqual(entry["occurrence_date"], "2023-04-01")
        self.assertEqual(entry["notes"], "A note")
        self.assertFalse(entry["confessed"])
        self.assertIsNone(entry["confession_date"])

    def test_add_sin_entry_minimal(self):
        entry_id = sins_tracker.add_sin_entry("Another sin")
        self.assertIsNotNone(entry_id)
        self.cursor.execute("SELECT * FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertEqual(entry["sin_description"], "Another sin")
        self.assertIsNone(entry["occurrence_date"])
        self.assertIsNone(entry["notes"])
        self.assertFalse(entry["confessed"])

    def test_add_sin_entry_invalid_date(self):
        entry_id = sins_tracker.add_sin_entry("Sin with bad date", occurrence_date="bad-date-format")
        self.assertIsNone(entry_id)
        self.cursor.execute("SELECT COUNT(*) FROM sins_confession_log WHERE sin_description = 'Sin with bad date'")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)


    def test_mark_sin_as_confessed_default_date(self):
        entry_id = sins_tracker.add_sin_entry("To be confessed")
        self.assertTrue(sins_tracker.mark_sin_as_confessed(entry_id))

        self.cursor.execute("SELECT * FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertTrue(entry["confessed"])
        self.assertEqual(entry["confession_date"], datetime.date.today().strftime("%Y-%m-%d"))

    def test_mark_sin_as_confessed_specific_date(self):
        entry_id = sins_tracker.add_sin_entry("Another to confess")
        confession_d = "2023-05-10"
        self.assertTrue(sins_tracker.mark_sin_as_confessed(entry_id, confession_date=confession_d))

        self.cursor.execute("SELECT * FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertTrue(entry["confessed"])
        self.assertEqual(entry["confession_date"], confession_d)

    def test_mark_sin_as_confessed_invalid_date(self):
        entry_id = sins_tracker.add_sin_entry("Confession bad date")
        self.assertFalse(sins_tracker.mark_sin_as_confessed(entry_id, confession_date="not-a-date"))
        self.cursor.execute("SELECT confessed FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertFalse(entry["confessed"])


    def test_mark_sin_as_confessed_already_confessed(self):
        entry_id = sins_tracker.add_sin_entry("Already done")
        sins_tracker.mark_sin_as_confessed(entry_id, "2023-01-01")
        # Try to mark again
        self.assertFalse(sins_tracker.mark_sin_as_confessed(entry_id, "2023-01-02"))

        self.cursor.execute("SELECT confession_date FROM sins_confession_log WHERE id = ?", (entry_id,))
        entry = self.cursor.fetchone()
        self.assertEqual(entry["confession_date"], "2023-01-01") # Should retain original date

    def test_mark_sin_as_confessed_non_existent_id(self):
        self.assertFalse(sins_tracker.mark_sin_as_confessed(999)) # Non-existent ID

    def test_get_sin_log_all(self):
        sins_tracker.add_sin_entry("Sin 1", occurrence_date="2023-10-01")
        id2 = sins_tracker.add_sin_entry("Sin 2", occurrence_date="2023-10-02")
        sins_tracker.mark_sin_as_confessed(id2, "2023-10-03")

        log = sins_tracker.get_sin_log(show_all=True)
        self.assertEqual(len(log), 2)
        # Ordered by created_at DESC, so Sin 2 (id2) should be first
        self.assertEqual(log[0]["sin_description"], "Sin 2")
        self.assertEqual(log[1]["sin_description"], "Sin 1")


    def test_get_sin_log_unconfessed(self):
        sins_tracker.add_sin_entry("Unconfessed 1")
        id_conf = sins_tracker.add_sin_entry("Confessed 1")
        sins_tracker.mark_sin_as_confessed(id_conf)
        sins_tracker.add_sin_entry("Unconfessed 2")

        log = sins_tracker.get_sin_log(show_all=False, show_confessed=False)
        self.assertEqual(len(log), 2)
        self.assertTrue(all(not entry["confessed"] for entry in log))
        self.assertEqual(log[0]["sin_description"], "Unconfessed 2") # Most recent unconfessed
        self.assertEqual(log[1]["sin_description"], "Unconfessed 1")

    def test_get_sin_log_confessed(self):
        sins_tracker.add_sin_entry("Unconfessed A")
        id_conf1 = sins_tracker.add_sin_entry("Confessed B")
        sins_tracker.mark_sin_as_confessed(id_conf1, "2023-10-01")
        id_conf2 = sins_tracker.add_sin_entry("Confessed C")
        sins_tracker.mark_sin_as_confessed(id_conf2, "2023-10-02")


        log = sins_tracker.get_sin_log(show_all=False, show_confessed=True)
        self.assertEqual(len(log), 2)
        self.assertTrue(all(entry["confessed"] for entry in log))
        self.assertEqual(log[0]["sin_description"], "Confessed C") # Most recent confessed by creation time
        self.assertEqual(log[1]["sin_description"], "Confessed B")

    def test_get_sin_log_limit(self):
        sins_tracker.add_sin_entry("S1")
        import time; time.sleep(0.01)
        sins_tracker.add_sin_entry("S2")
        import time; time.sleep(0.01)
        sins_tracker.add_sin_entry("S3")

        log = sins_tracker.get_sin_log(show_all=True, limit=2)
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0]["sin_description"], "S3")
        self.assertEqual(log[1]["sin_description"], "S2")

    def test_get_sin_log_empty(self):
        log = sins_tracker.get_sin_log()
        self.assertEqual(len(log), 0)

    def test_format_sin_entry_for_display(self):
        entry1 = {"id":1, "confessed":False, "sin_description":"Lazy", "occurrence_date":"2023-01-01", "confession_date":None, "notes":"Morning", "created_at":"2023-01-01 10:00:00"}
        self.assertEqual(sins_tracker.format_sin_entry_for_display(entry1), "[1] Not Confessed - \"Lazy\" (Occurred: 2023-01-01) - Notes: Morning (Logged: 2023-01-01)")

        entry2 = {"id":2, "confessed":True, "sin_description":"Angry", "occurrence_date":None, "confession_date":"2023-01-03", "notes":None, "created_at":"2023-01-02 11:00:00"}
        self.assertEqual(sins_tracker.format_sin_entry_for_display(entry2), "[2] Confessed - \"Angry\" (Confessed on: 2023-01-03) (Logged: 2023-01-02)")

if __name__ == '__main__':
    unittest.main()
