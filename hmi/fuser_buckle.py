"""Predkosc silnika fusera. Blizniak plc/FB_FuserBuckle.st.

Za duze wybrzuszenie przy nipie: 130%. Za male: 70%.
Waskie medium obcina do 80%. Zawiniecie gasi naped i grzalke.
"""


class FuserBuckle:
    def __init__(self):
        self.speed = 0
        self.heater = False
        self.jam = False

    def step(self, enable, nip=False, buckle_high=False, buckle_low=False, narrow=False, wrap=False):
        if not enable or wrap:
            self.speed = 0
            self.heater = False
            self.jam = bool(wrap)
            return self.speed
        self.jam = False
        self.heater = True
        self.speed = 100
        if nip and buckle_high:
            self.speed = 130
        elif nip and buckle_low:
            self.speed = 70
        if narrow and self.speed > 80:
            self.speed = 80
        return self.speed
