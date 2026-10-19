"""Small dependency-free smoke tests for HunarSikka's SQLite persistence."""
import tempfile
import unittest
from pathlib import Path

import database


class DatabaseSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_path = database.DB_PATH
        database.DB_PATH = Path(self.tempdir.name) / "test.db"
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self.original_path
        self.tempdir.cleanup()

    def test_admin_is_seeded_and_password_is_hashed(self):
        admin = database.get_user_by_email("admin@hunarsikka.local")
        self.assertIsNotNone(admin)
        self.assertTrue(database.verify_password("ChangeMe123!", admin["password_hash"]))
        self.assertNotEqual("ChangeMe123!", admin["password_hash"])

    def test_student_records_persist(self):
        database.create_user("Demo Student", "student@example.com", "ExamplePass123", "student")
        student = database.get_user_by_email("student@example.com")
        lesson_id = database.rows("SELECT id FROM lessons LIMIT 1")[0]["id"]
        database.execute("INSERT INTO completions(user_id,lesson_id) VALUES(?,?)", (student["id"], lesson_id))
        database.execute("INSERT INTO projects(user_id,title,pathway,description) VALUES(?,?,?,?)", (student["id"], "My poster", "Graphic Design", "A school event poster"))
        database.execute("INSERT INTO budget_runs(user_id,allowance,needs,wants,savings) VALUES(?,?,?,?,?)", (student["id"], 1000, 500, 200, 200))
        self.assertEqual(1, database.one("SELECT COUNT(*) n FROM completions WHERE user_id=?", (student["id"],))["n"])
        self.assertEqual(1, database.one("SELECT COUNT(*) n FROM projects WHERE user_id=?", (student["id"],))["n"])
        self.assertEqual(1, database.one("SELECT COUNT(*) n FROM budget_runs WHERE user_id=?", (student["id"],))["n"])

    def test_teacher_requires_approval(self):
        database.create_user("Demo Teacher", "teacher@example.com", "ExamplePass123", "teacher")
        teacher = database.get_user_by_email("teacher@example.com")
        self.assertEqual(0, teacher["approved"])
        database.execute("UPDATE users SET approved=1 WHERE id=?", (teacher["id"],))
        self.assertEqual(1, database.get_user_by_email("teacher@example.com")["approved"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
