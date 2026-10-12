import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from warmup import Warmup


class WarmupTest(unittest.TestCase):
    def test_cold_roller_is_not_ready(self):
        heat = Warmup()
        heat.step(True, 25.0)
        self.assertTrue(heat.heating)
        self.assertFalse(heat.ready)
        self.assertFalse(heat.overtemp)

    def test_band_from_70_to_95_allows_feed(self):
        heat = Warmup()
        for actual in (70.0, 80.0, 95.0):
            heat.step(True, actual)
            self.assertTrue(heat.ready, actual)
            self.assertFalse(heat.heating)

    def test_over_95_is_a_fault(self):
        heat = Warmup()
        heat.step(True, 95.1)
        self.assertTrue(heat.overtemp)
        self.assertFalse(heat.ready)
        self.assertFalse(heat.heating)

    def test_disabled_circuit_does_not_alarm(self):
        heat = Warmup()
        heat.step(False, 120.0)
        self.assertFalse(heat.overtemp)
        self.assertFalse(heat.ready)
        self.assertFalse(heat.heating)


if __name__ == "__main__":
    unittest.main()
