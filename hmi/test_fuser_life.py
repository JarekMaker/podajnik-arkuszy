import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fuser_life import FuserLife


class FuserLifeTest(unittest.TestCase):
    def test_first_scan_does_not_count(self):
        life = FuserLife()
        life.step(0)
        self.assertEqual(life.total, 0)
        self.assertFalse(life.warn)

    def test_each_new_sheet_counts_once(self):
        life = FuserLife()
        life.step(0)
        life.step(1)
        life.step(1)
        life.step(2)
        self.assertEqual(life.total, 2)

    def test_warn_at_140k_and_due_at_150k(self):
        life = FuserLife()
        life.step(0)
        life.total = 139_999
        life.step(1)
        self.assertTrue(life.warn)
        self.assertFalse(life.due)
        self.assertEqual(life.thousands, 140)
        life.total = 149_999
        life.step(2)
        self.assertTrue(life.due)
        self.assertEqual(life.thousands, 150)

    def test_service_reset_clears_the_counter(self):
        life = FuserLife()
        life.step(0)
        life.total = 150_000
        life.step(4, reset_service=True)
        self.assertEqual(life.total, 0)
        self.assertFalse(life.due)

    def test_counter_stops_at_the_service_limit(self):
        life = FuserLife()
        life.step(0)
        life.total = 150_000
        life.step(1)
        self.assertEqual(life.total, 150_000)


if __name__ == "__main__":
    unittest.main()
