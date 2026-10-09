"""Licznik fusera: 150 tys. stron, ostrzezenie od 140 tys.

To jest blizniak plc/FB_FuserLife.st. Jeden przyrost SheetCount to jedna strona.
"""

LIMIT = 150_000
WARN_AT = 140_000


class FuserLife:
    def __init__(self):
        self.total = 0
        self.prev = 0
        self.seen = False

    def step(self, sheet_count, reset_service=False):
        if not self.seen:
            self.prev = sheet_count
            self.seen = True
        if reset_service:
            self.total = 0
        elif sheet_count != self.prev:
            self.total += 1
        self.prev = sheet_count
        if self.total > LIMIT:
            self.total = LIMIT
        return self.total

    @property
    def thousands(self):
        return self.total // 1000

    @property
    def warn(self):
        return self.total >= WARN_AT

    @property
    def due(self):
        return self.total >= LIMIT
