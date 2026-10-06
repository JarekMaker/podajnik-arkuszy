"""Model 3D podajnika. Jednostki: milimetry.

    freecadcmd mechanical/build_model.py

Skrypt zapisuje mechanical/podajnik.FCStd obok siebie.
Wymiary na gorze pliku sa parametrami: zmiana LENGTH przebudowuje rame.
"""

import os
import sys

LENGTH = 400.0
WIDTH = 180.0
RAIL = 20.0
ROLLER_D = 40.0
ROLLER_GAP = 220.0


def main():
    try:
        import FreeCAD
        import Part
    except ImportError:
        sys.stderr.write("Uruchom przez freecadcmd mechanical/build_model.py\n")
        return 1

    doc = FreeCAD.newDocument("podajnik")

    def add(name, shape):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        return obj

    def box(name, x, y, z, dx, dy, dz):
        return add(name, Part.makeBox(dx, dy, dz, FreeCAD.Vector(x, y, z)))

    box("rail_front", 0, 0, 0, LENGTH, RAIL, RAIL)
    box("rail_back", 0, WIDTH - RAIL, 0, LENGTH, RAIL, RAIL)
    box("leg_left", 0, 0, 0, RAIL, WIDTH, RAIL)
    box("leg_right", LENGTH - RAIL, 0, 0, RAIL, WIDTH, RAIL)

    radius = ROLLER_D / 2.0
    x_first = 80.0
    for index, x in enumerate((x_first, x_first + ROLLER_GAP)):
        roller = Part.makeCylinder(
            radius,
            WIDTH - 2 * RAIL,
            FreeCAD.Vector(x, RAIL, RAIL + radius),
            FreeCAD.Vector(0, 1, 0),
        )
        add(f"roller_{index + 1}", roller)

    # Krotszy krotki krazownik czujnika nad pierwszym rolkiem.
    box("sensor_bracket", x_first - 8, WIDTH / 2 - 10, RAIL + ROLLER_D, 16, 20, 25)

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "podajnik.FCStd")
    doc.recompute()
    doc.saveAs(out)
    print(out)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
elif "FreeCAD" in sys.modules:
    main()
