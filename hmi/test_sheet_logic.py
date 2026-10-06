import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sheet_logic import (
    ST_COVER,
    ST_ESTOP,
    ST_FAULT,
    ST_FEED,
    ST_JAM,
    ST_READY,
    ST_REGISTER,
    ST_RUN,
    Feeder,
    Inputs,
)


def boot(feeder):
    feeder.step(Inputs(reset=True))
    feeder.step(Inputs())
    return feeder


class FeederTest(unittest.TestCase):
    def test_power_up_stays_off_until_reset(self):
        feeder = Feeder()
        feeder.step(Inputs(temp_c=25))
        self.assertEqual(feeder.state, ST_ESTOP)
        self.assertFalse(feeder.run_enable)
        self.assertFalse(feeder.motor)
        self.assertFalse(feeder.heater)

    def test_reset_then_estop_needs_another_reset(self):
        feeder = boot(Feeder())
        self.assertTrue(feeder.run_enable)
        self.assertEqual(feeder.state, ST_READY)
        self.assertTrue(feeder.heater)
        self.assertEqual(feeder.heat_out, 100.0)

        feeder.step(Inputs(estop_ok=False))
        self.assertEqual(feeder.state, ST_ESTOP)
        self.assertFalse(feeder.heater)

        feeder.step(Inputs(estop_ok=True))
        self.assertEqual(feeder.state, ST_ESTOP)

        feeder.step(Inputs(estop_ok=True, reset=True))
        self.assertEqual(feeder.state, ST_READY)

    def test_cover_blocks_start(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(cover_closed=False, start=True))
        self.assertEqual(feeder.state, ST_COVER)
        self.assertFalse(feeder.motor)
        self.assertFalse(feeder.clutch)

    def test_sheet_passes_and_next_one_starts(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(start=True))
        self.assertEqual(feeder.state, ST_FEED)
        self.assertTrue(feeder.clutch)
        self.assertTrue(feeder.motor)

        feeder.step(Inputs(sens_entry=True))
        self.assertEqual(feeder.state, ST_REGISTER)
        self.assertFalse(feeder.clutch)

        feeder.step(Inputs(sens_entry=True, sens_register=True))
        self.assertEqual(feeder.state, ST_RUN)
        self.assertTrue(feeder.gate)

        feeder.step(Inputs(sens_exit=True))
        self.assertEqual(feeder.sheet_count, 1)
        self.assertEqual(feeder.state, ST_RUN)

        feeder.step(Inputs())
        self.assertEqual(feeder.phase, 0)
        self.assertFalse(feeder.clutch)

        feeder.step(Inputs())
        self.assertEqual(feeder.state, ST_FEED)
        self.assertTrue(feeder.clutch)

    def test_timeout_is_a_jam(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(start=True))
        feeder.step(Inputs(sens_entry=True))
        self.assertEqual(feeder.state, ST_REGISTER)
        for _ in range(79):
            feeder.step(Inputs(sens_entry=True))
            self.assertFalse(feeder.jam)
        feeder.step(Inputs(sens_entry=True))
        self.assertTrue(feeder.jam)
        self.assertEqual(feeder.state, ST_JAM)
        self.assertFalse(feeder.motor)
        self.assertFalse(feeder.heater)

    def test_stop_with_sheet_in_path_jams(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(start=True))
        feeder.step(Inputs(sens_entry=True))
        feeder.step(Inputs(stop=True, sens_entry=True))
        self.assertTrue(feeder.jam)
        self.assertFalse(feeder.motor)

    def test_reset_ignored_while_sensor_covered(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(start=True))
        feeder.step(Inputs(sens_entry=True))
        feeder.step(Inputs(stop=True, sens_entry=True))
        feeder.step(Inputs(reset=True, sens_entry=True))
        self.assertTrue(feeder.jam)
        feeder.step(Inputs())
        feeder.step(Inputs(reset=True))
        self.assertFalse(feeder.jam)
        self.assertEqual(feeder.state, ST_READY)

    def test_sheet_already_in_path_jams_on_start(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(sens_entry=True))
        feeder.step(Inputs(start=True, sens_entry=True))
        self.assertTrue(feeder.jam)

    def test_motor_feedback_timeout(self):
        feeder = boot(Feeder())
        feeder.use_feedback = True
        feeder.step(Inputs(start=True, motor_aux=False))
        self.assertTrue(feeder.motor)
        for _ in range(48):
            feeder.step(Inputs(motor_aux=False))
            self.assertFalse(feeder.motor_fault_latched)
        feeder.step(Inputs(motor_aux=False))
        self.assertTrue(feeder.motor_fault_latched)
        self.assertEqual(feeder.state, ST_FAULT)
        self.assertFalse(feeder.motor)

    def test_thermal_fault(self):
        feeder = boot(Feeder())
        feeder.step(Inputs(start=True))
        feeder.step(Inputs(motor_fault=True))
        self.assertEqual(feeder.state, ST_FAULT)
        self.assertFalse(feeder.motor)


if __name__ == "__main__":
    unittest.main()
