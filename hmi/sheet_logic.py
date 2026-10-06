"""Ta sama sekwencja co plc/FB_SheetTrack.st i plc/MAIN.st. Jeden krok to 10 ms."""

ST_READY = 1
ST_FEED = 2
ST_REGISTER = 3
ST_RUN = 4
ST_JAM = 5
ST_FAULT = 6
ST_ESTOP = 7
ST_COVER = 8

STATE_NAME = {
    ST_READY: "READY",
    ST_FEED: "FEED",
    ST_REGISTER: "REGISTER",
    ST_RUN: "RUN",
    ST_JAM: "JAM",
    ST_FAULT: "FAULT",
    ST_ESTOP: "ESTOP",
    ST_COVER: "COVER",
}

SETPOINT_C = 80.0


class Inputs:
    def __init__(
        self,
        estop_ok=True,
        cover_closed=True,
        sens_entry=False,
        sens_register=False,
        sens_exit=False,
        motor_fault=False,
        start=False,
        stop=False,
        reset=False,
        temp_c=25.0,
        motor_aux=False,
    ):
        self.estop_ok = estop_ok
        self.cover_closed = cover_closed
        self.sens_entry = sens_entry
        self.sens_register = sens_register
        self.sens_exit = sens_exit
        self.motor_fault = motor_fault
        self.start = start
        self.stop = stop
        self.reset = reset
        self.temp_c = temp_c
        self.motor_aux = motor_aux


class Feeder:
    CYCLE_MS = 10
    JAM_MS = 800
    FB_TIMEOUT_MS = 500

    def __init__(self):
        self.need_reset = True
        self.run_enable = False
        self.run_request = False
        self.jam = False
        self.phase = 0
        self.timer_ms = 0
        self.sheet_count = 0
        self.motor_fault_latched = False
        self.fb_timer = 0
        self.use_feedback = False
        self._prev = {}
        self.integral = 0.0
        self.prev_error = 0.0
        self.heat_armed = False
        self.heat_out = 0.0
        self.motor = False
        self.clutch = False
        self.gate = False
        self.lamp_run = False
        self.lamp_fault = False
        self.heater = False
        self.busy = False
        self.state = ST_ESTOP

    def rise(self, name, value):
        value = bool(value)
        prev = self._prev.get(name, False)
        self._prev[name] = value
        return value and not prev

    def step(self, inp):
        r_reset = self.rise("reset", inp.reset)
        r_start = self.rise("start", inp.start)
        r_stop = self.rise("stop", inp.stop)
        r_entry = self.rise("entry", inp.sens_entry)
        r_exit = self.rise("exit", inp.sens_exit)

        if not inp.estop_ok:
            self.need_reset = True
            self.run_enable = False
        elif self.need_reset:
            self.run_enable = False
            if r_reset:
                self.need_reset = False
                self.run_enable = True
        else:
            self.run_enable = True

        if inp.motor_fault:
            self.motor_fault_latched = True
        if r_reset and not inp.motor_fault:
            self.motor_fault_latched = False

        if (
            r_reset
            and self.jam
            and not inp.sens_entry
            and not inp.sens_register
            and not inp.sens_exit
        ):
            self.jam = False
            self.phase = 0
            self.timer_ms = 0

        if r_stop or not self.run_enable or inp.motor_fault or not inp.cover_closed:
            self.run_request = False

        motion_ok = (
            self.run_enable
            and inp.cover_closed
            and not self.motor_fault_latched
            and not self.jam
        )
        if r_start and motion_ok and not self.busy:
            self.run_request = True

        feed_cmd = self.run_request and motion_ok
        self._track(feed_cmd, inp, r_entry, r_exit)

        motor_cmd = self.motor and motion_ok and not self.jam
        if self.motor_fault_latched:
            motor_cmd = False
            self.fb_timer = 0
        elif self.use_feedback and motor_cmd:
            if not inp.motor_aux:
                self.fb_timer += self.CYCLE_MS
                if self.fb_timer >= self.FB_TIMEOUT_MS:
                    self.motor_fault_latched = True
                    motor_cmd = False
            else:
                self.fb_timer = 0
        else:
            self.fb_timer = 0

        self.motor = motor_cmd
        if self.jam or not motion_ok:
            self.clutch = False
            self.gate = False

        self._heat(inp)
        self.lamp_run = self.motor
        self.lamp_fault = self.jam or self.motor_fault_latched or not self.run_enable
        self.busy = self.jam or self.phase != 0 or self.clutch
        self.state = self._state(inp)
        return self

    def _track(self, feed_cmd, inp, r_entry, r_exit):
        path_busy = inp.sens_entry or inp.sens_register or inp.sens_exit
        if self.jam:
            self.motor = False
            self.clutch = False
            self.gate = False
            self.timer_ms = 0
            return

        if not feed_cmd and self.phase != 0:
            if path_busy:
                self.jam = True
            else:
                self.phase = 0
                self.timer_ms = 0
            self.motor = False
            self.clutch = False
            self.gate = False
            return

        if self.phase == 0:
            self.gate = False
            self.timer_ms = 0
            if feed_cmd and r_entry:
                self.clutch = False
                self.motor = True
                self.phase = 1
            elif feed_cmd and path_busy:
                self.jam = True
                self.clutch = False
                self.motor = False
            elif feed_cmd:
                self.clutch = True
                self.motor = True
            else:
                self.clutch = False
                self.motor = False
        elif self.phase == 1:
            self.clutch = False
            self.motor = True
            self.gate = False
            self.timer_ms += self.CYCLE_MS
            if inp.sens_register:
                self.phase = 2
                self.timer_ms = 0
                self.gate = True
            elif self.timer_ms >= self.JAM_MS:
                self.jam = True
                self.phase = 0
                self.motor = False
        elif self.phase == 2:
            self.clutch = False
            self.motor = True
            self.gate = True
            self.timer_ms += self.CYCLE_MS
            if r_exit:
                self.sheet_count += 1
                self.phase = 3
                self.timer_ms = 0
                self.gate = False
            elif self.timer_ms >= self.JAM_MS:
                self.jam = True
                self.phase = 0
                self.motor = False
                self.gate = False
        else:
            self.clutch = False
            self.gate = False
            self.motor = True
            if not path_busy:
                self.phase = 0
                self.motor = False

        if self.jam:
            self.motor = False
            self.clutch = False
            self.gate = False

    def _heat(self, inp):
        heat_ok = (
            self.run_enable
            and inp.cover_closed
            and not self.jam
            and not self.motor_fault_latched
        )
        if not heat_ok:
            self.heat_armed = False
            self.integral = 0.0
            self.prev_error = 0.0
            self.heat_out = 0.0
            self.heater = False
            return

        error = SETPOINT_C - inp.temp_c
        if not self.heat_armed:
            self.prev_error = error
            self.integral = 0.0
            self.heat_armed = True
        self.integral += error * 0.01
        deriv = (error - self.prev_error) / 0.01
        self.prev_error = error
        raw = 4.0 * error + 0.8 * self.integral + 0.1 * deriv
        if raw > 100.0:
            raw = 100.0
            self.integral -= error * 0.01
        elif raw < 0.0:
            raw = 0.0
            self.integral -= error * 0.01
        self.heat_out = raw
        self.heater = self.heat_out > 1.0

    def _state(self, inp):
        if not self.run_enable:
            return ST_ESTOP
        if self.motor_fault_latched:
            return ST_FAULT
        if self.jam:
            return ST_JAM
        if not inp.cover_closed:
            return ST_COVER
        if self.phase == 1:
            return ST_REGISTER
        if self.phase in (2, 3):
            return ST_RUN
        if self.clutch:
            return ST_FEED
        return ST_READY
