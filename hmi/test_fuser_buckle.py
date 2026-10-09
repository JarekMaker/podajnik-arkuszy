import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fuser_buckle import FuserBuckle


class FuserBuckleTest(unittest.TestCase):
    def test_stopped_when_disabled(self):
        belt = FuserBuckle()
        belt.step(False, nip=True, buckle_high=True)
        self.assertEqual(belt.speed, 0)
        self.assertFalse(belt.heater)
        self.assertFalse(belt.jam)

    def test_wrap_kills_drive_and_heater(self):
        belt = FuserBuckle()
        belt.step(True, nip=True, wrap=True)
        self.assertEqual(belt.speed, 0)
        self.assertFalse(belt.heater)
        self.assertTrue(belt.jam)

    def test_high_buckle_speeds_up_only_in_the_nip(self):
        belt = FuserBuckle()
        belt.step(True, buckle_high=True)
        self.assertEqual(belt.speed, 100)
        belt.step(True, nip=True, buckle_high=True)
        self.assertEqual(belt.speed, 130)

    def test_low_buckle_slows_down(self):
        belt = FuserBuckle()
        belt.step(True, nip=True, buckle_low=True)
        self.assertEqual(belt.speed, 70)
        self.assertTrue(belt.heater)

    def test_narrow_media_caps_the_fast_speed(self):
        belt = FuserBuckle()
        belt.step(True, nip=True, buckle_high=True, narrow=True)
        self.assertEqual(belt.speed, 80)

    def test_narrow_media_does_not_raise_the_slow_speed(self):
        belt = FuserBuckle()
        belt.step(True, nip=True, buckle_low=True, narrow=True)
        self.assertEqual(belt.speed, 70)


if __name__ == "__main__":
    unittest.main()
