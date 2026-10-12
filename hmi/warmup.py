"""Pasmо temperatury rolki. Blizniak plc/FB_Warmup.st.

Start arkusza od 70 C. Powyzej 95 C grzalka ma odpasć.
"""


class Warmup:
    def step(self, enable, actual):
        self.overtemp = bool(enable and actual > 95.0)
        self.ready = bool(enable and 70.0 <= actual <= 95.0)
        self.heating = bool(enable and actual < 70.0)
        return self.ready
