"""Fuser paskowy, tak jak w kolorowym laserze tego typu.

Pas kreci sie wokol plaskiej grzalki ceramicznej. Walek dociskowy
dopycha pas do grzalki i tam jest nip: cieplo topi toner, docisk wprasowuje go w papier.
Palce oddzielajace zdejmuja arkusz z pasa, zeby nie zawinal sie wokol niego.
Termistor siedzi na ceramice i trzyma temperature.

    freecadcmd mechanical/build_fuser.py

Wymiary w milimetrach. Os wzdluz X to szerokosc kartki.
"""

import os
import sys

LENGTH = 300.0


def main():
    try:
        import FreeCAD
        import Part
    except ImportError:
        sys.stderr.write("Uruchom przez freecadcmd mechanical/build_fuser.py\n")
        return 1

    doc = FreeCAD.newDocument("fuser")

    def put(name, shape):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        return obj

    def along_x(name, radius, length, x, y, z):
        shape = Part.makeCylinder(
            radius, length, FreeCAD.Vector(x, y, z), FreeCAD.Vector(1, 0, 0)
        )
        return put(name, shape)

    def box(name, x, y, z, dx, dy, dz):
        return put(name, Part.makeBox(dx, dy, dz, FreeCAD.Vector(x, y, z)))

    def belt_loop(x0, length, y0, z0, straight, radius, thick):
        def ring(rad):
            left = FreeCAD.Vector(0, y0, z0)
            right_y = y0 + straight
            top_l = FreeCAD.Vector(0, y0, z0 + rad)
            out_l = FreeCAD.Vector(0, y0 - rad, z0)
            bot_l = FreeCAD.Vector(0, y0, z0 - rad)
            bot_r = FreeCAD.Vector(0, right_y, z0 - rad)
            out_r = FreeCAD.Vector(0, right_y + rad, z0)
            top_r = FreeCAD.Vector(0, right_y, z0 + rad)
            edges = [
                Part.Arc(top_l, out_l, bot_l).toShape(),
                Part.LineSegment(bot_l, bot_r).toShape(),
                Part.Arc(bot_r, out_r, top_r).toShape(),
                Part.LineSegment(top_r, top_l).toShape(),
            ]
            return Part.Face(Part.Wire(edges))

        wall = ring(radius).cut(ring(radius - thick))
        solid = wall.extrude(FreeCAD.Vector(length, 0, 0))
        solid.translate(FreeCAD.Vector(x0, 0, 0))
        return solid

    x0 = -LENGTH / 2.0
    belt_r = 22.0
    belt_straight = 28.0
    belt_y = 0.0
    belt_z = 46.0
    # Nip jest na prawym luczku pasa. Docisk stoi tuz za nim.
    nip_y = belt_y + belt_straight + belt_r
    press_r = 28.0
    press_y = nip_y + press_r - 3.0

    put(
        "fuser_belt",
        belt_loop(x0 + 8, LENGTH - 16, belt_y, belt_z, belt_straight, belt_r, 1.6),
    )
    # Ceramika wewnatrz pasa, przy plaszczyznie nipu.
    box(
        "ceramic_heater",
        x0 + 18,
        nip_y - belt_r - 4,
        belt_z - 8,
        LENGTH - 36,
        5,
        16,
    )
    box("thermistor", x0 + LENGTH / 2, nip_y - belt_r - 2, belt_z + 6, 8, 6, 5)
    along_x("pressure_roller", press_r, LENGTH - 24, x0 + 12, press_y, belt_z)
    along_x("gear", 16, 12, x0 + LENGTH - 12, press_y, belt_z)

    # Palce oddzielajace za nipem, pochylone w strone wyjscia.
    for index, xpos in enumerate((-80, -20, 40, 100)):
        finger = Part.makeBox(6, 2.2, 22, FreeCAD.Vector(xpos, nip_y + 6, belt_z + 4))
        finger.rotate(FreeCAD.Vector(xpos, nip_y + 6, belt_z + 4), FreeCAD.Vector(1, 0, 0), -40)
        put(f"stripper_{index + 1}", finger)

    along_x("decurl_upper", 11, LENGTH - 50, x0 + 25, press_y + 46, belt_z + 6)
    along_x("decurl_lower", 11, LENGTH - 50, x0 + 25, press_y + 46, belt_z - 18)
    along_x("exit_roller", 13, LENGTH - 50, x0 + 25, press_y + 86, belt_z - 4)

    box("end_left", x0 - 8, belt_y - belt_r - 8, 8, 8, press_y + 40, 84)
    box("end_right", x0 + LENGTH, belt_y - belt_r - 8, 8, 8, press_y + 40, 84)
    box("entrance_guide", x0 + 20, belt_y - belt_r - 36, belt_z - 28, LENGTH - 40, 28, 3)

    # Przed nipem: wybrzuszenie i waskie medium (to drugie przy krawedzi).
    box("sensor_buckle", -12, belt_y - belt_r - 30, belt_z - 24, 16, 14, 20)
    box("sensor_narrow", x0 + LENGTH - 36, belt_y - belt_r - 30, belt_z - 18, 12, 14, 14)
    box("sensor_nip", 8, nip_y - 6, belt_z + belt_r + 2, 14, 12, 10)
    box("sensor_exit", -6, nip_y + 18, belt_z + 16, 14, 12, 16)

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "fuser.FCStd")
    doc.recompute()
    doc.saveAs(out)
    print(out)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
elif "FreeCAD" in sys.modules:
    main()
