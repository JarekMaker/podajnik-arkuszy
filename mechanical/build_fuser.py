"""Fuser type 01, 220-240 V, czesc 41X0253.

Serwisowka 7528, Fuser section. Papier idzie poziomo, os X.
Szerokosc kartki to os Y: minus lewo (wybrzuszenie), plus prawo
(waskie medium). Nip jest pod pasem, walek dociskowy od dolu.

    freecadcmd mechanical/build_fuser.py

Wymiary pogladowe, w milimetrach. Serwisowka nie podaje tolerancji.
"""

import os
import sys

BELT_R = 16.0
STRAIGHT = 38.0
BELT_W = 270.0
ROLL_R = 20.0
NIP_X = STRAIGHT / 2.0
Y0 = -BELT_W / 2.0


def main():
    try:
        import FreeCAD
        import Part
    except ImportError:
        sys.stderr.write("Uruchom przez freecadcmd mechanical/build_fuser.py\n")
        return 1

    doc = FreeCAD.newDocument("fuser")

    def put(name, shape):
        if not shape.isValid() or shape.Volume < 1.0:
            raise RuntimeError(name)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        return obj

    def box(name, x, y, z, dx, dy, dz):
        return put(name, Part.makeBox(dx, dy, dz, FreeCAD.Vector(x, y, z)))

    def cyl_y(name, radius, length, x, y, z):
        shape = Part.makeCylinder(
            radius, length, FreeCAD.Vector(x, y, z), FreeCAD.Vector(0, 1, 0)
        )
        return put(name, shape)

    def plate(name, points, y, dy):
        face = Part.Face(Part.makePolygon(points + [points[0]]))
        solid = face.extrude(FreeCAD.Vector(0, dy, 0))
        solid.translate(FreeCAD.Vector(0, y, 0))
        return put(name, solid)

    def belt_loop(y, length, x0, z0, straight, radius, thick):
        def ring(rad):
            right = x0 + straight
            top_l = FreeCAD.Vector(x0, 0, z0 + rad)
            out_l = FreeCAD.Vector(x0 - rad, 0, z0)
            bot_l = FreeCAD.Vector(x0, 0, z0 - rad)
            bot_r = FreeCAD.Vector(right, 0, z0 - rad)
            out_r = FreeCAD.Vector(right + rad, 0, z0)
            top_r = FreeCAD.Vector(right, 0, z0 + rad)
            edges = [
                Part.Arc(top_l, out_l, bot_l).toShape(),
                Part.LineSegment(bot_l, bot_r).toShape(),
                Part.Arc(bot_r, out_r, top_r).toShape(),
                Part.LineSegment(top_r, top_l).toShape(),
            ]
            return Part.Face(Part.Wire(edges))

        wall = ring(radius).cut(ring(radius - thick))
        solid = wall.extrude(FreeCAD.Vector(0, length, 0))
        solid.translate(FreeCAD.Vector(0, y, 0))
        return solid

    def gear(name, radius, width, x, y, z, teeth):
        hub = Part.makeCylinder(radius * 0.45, width, FreeCAD.Vector(x, y, z), FreeCAD.Vector(0, 1, 0))
        rim = Part.makeCylinder(radius - 1.4, width, FreeCAD.Vector(x, y, z), FreeCAD.Vector(0, 1, 0))
        parts = [hub, rim]
        step = 360.0 / teeth
        for index in range(teeth):
            tooth = Part.makeBox(1.8, width, 3.4, FreeCAD.Vector(x - 0.9, y, z + radius - 2.6))
            tooth.rotate(FreeCAD.Vector(x, y, z), FreeCAD.Vector(0, 1, 0), index * step)
            parts.append(tooth)
        return put(name, Part.makeCompound(parts))

    def optical(name, x, y, z):
        body = Part.makeBox(16.0, 14.0, 18.0, FreeCAD.Vector(x, y, z))
        slot = Part.makeBox(10.0, 14.0, 8.0, FreeCAD.Vector(x + 3.0, y, z + 8.0))
        return put(name, body.cut(slot))

    cru = []
    path = []
    drive = []

    cru.append(put("fuser_belt", belt_loop(Y0, BELT_W, 0.0, BELT_R, STRAIGHT, BELT_R, 1.3)))

    housing = Part.makeBox(22.0, BELT_W - 24.0, 18.0, FreeCAD.Vector(8.0, Y0 + 12.0, 6.0))
    for slot_y in (-96.0, -28.0, 40.0):
        housing = housing.cut(Part.makeBox(10.0, 52.0, 16.0, FreeCAD.Vector(13.0, slot_y, 8.0)))
    cru.append(put("heater_housing", housing))

    # Trzy strefy stykaja sie. Prawa jest od strony waskiego medium.
    zones = (("heater_main", -110.0, 73.0), ("heater_middle", -36.0, 72.0), ("heater_secondary", 37.0, 73.0))
    for name, y, dy in zones:
        cru.append(box(name, 13.0, y, 1.25, 12.0, dy, 2.0))
        cru.append(cyl_y("thermistor_" + name.split("_", 1)[1], 2.2, 4.0, 19.0, y + dy / 2.0 - 2.0, 3.3))

    cru.append(cyl_y("thermistor_edge", 2.0, 4.0, 19.0, 104.0, 3.4))
    cru.append(cyl_y("thermistor_belt_contact", 2.0, 5.0, 7.0, -6.0, 2.2))
    cru.append(cyl_y("thermistor_belt_noncontact", 3.2, 6.0, NIP_X, 10.0, 34.2))

    roll_z = 1.0 - ROLL_R
    cru.append(cyl_y("backup_roll", ROLL_R, BELT_W - 36.0, NIP_X, Y0 + 18.0, roll_z))
    cru.append(cyl_y("backup_shaft", 6.0, BELT_W + 40.0, NIP_X, Y0 - 22.0, roll_z))
    cru.append(cyl_y("thermistor_backup", 3.0, 5.0, NIP_X, Y0 - 16.0, roll_z))
    cru.append(cyl_y("thermistor_backup_narrow", 3.0, 5.0, NIP_X, Y0 + BELT_W - 2.0, roll_z))

    for y in (Y0 + 28.0, -Y0 - 36.0):
        rings = []
        for turn in range(7):
            ring = Part.makeTorus(5.2, 0.7)
            ring.translate(FreeCAD.Vector(NIP_X, y, roll_z - 16.0 + turn * 2.4))
            rings.append(ring)
        rod = Part.makeCylinder(1.1, 18.0, FreeCAD.Vector(NIP_X, y, roll_z - 18.0), FreeCAD.Vector(0, 0, 1))
        cru.append(put("spring_left" if y < 0 else "spring_right", Part.makeCompound(rings + [rod])))

    for index, ypos in enumerate((-100.0, -50.0, 0.0, 50.0, 100.0)):
        pts = [
            FreeCAD.Vector(42.0, 0, 0.8),
            FreeCAD.Vector(64.0, 0, 2.4),
            FreeCAD.Vector(64.0, 0, 3.3),
            FreeCAD.Vector(42.0, 0, 1.7),
        ]
        cru.append(plate("stripper_%s" % (index + 1), pts, ypos, 3.2))

    deflector = [
        FreeCAD.Vector(60.0, 0, 2.6),
        FreeCAD.Vector(92.0, 0, 2.6),
        FreeCAD.Vector(92.0, 0, 3.8),
        FreeCAD.Vector(60.0, 0, 3.8),
    ]
    path.append(plate("redrive_deflector", deflector, -120.0, 240.0))

    for name, ypos in (("end_left", Y0 - 6.0), ("end_right", -Y0)):
        plate_s = Part.makeBox(86.0, 6.0, 70.0, FreeCAD.Vector(-20.0, ypos, -32.0))
        window = Part.makeBox(58.0, 6.0, 40.0, FreeCAD.Vector(-6.0, ypos, -4.0))
        cru.append(put(name, plate_s.cut(window)))
        for sx, sz in ((-12.0, 30.0), (58.0, 30.0), (-12.0, -24.0), (58.0, -24.0)):
            cru.append(cyl_y("screw_%s_%d_%d" % (name, int(sx), int(sz)), 2.2, 3.0, sx, ypos - 1.0, sz))

    cru.append(box("fuser_base", -14.0, Y0, -40.0, 78.0, BELT_W, 4.0))
    cover = Part.makeBox(78.0, BELT_W - 8.0, 3.0, FreeCAD.Vector(-14.0, Y0 + 4.0, 33.5))
    cover = cover.cut(Part.makeBox(46.0, 180.0, 3.0, FreeCAD.Vector(2.0, -90.0, 33.5)))
    cru.append(put("top_cover", cover))

    cru.append(box("fuser_lock", 66.0, -Y0 - 2.0, 4.0, 16.0, 8.0, 8.0))
    cru.append(box("lock_lever", 78.0, -Y0 - 1.0, 8.0, 5.0, 6.0, 26.0))

    cru.append(box("connector_cn1", -6.0, Y0 - 14.0, 8.0, 18.0, 10.0, 12.0))
    for index, xpos in enumerate((0.0, 4.0, 8.0, 12.0)):
        cru.append(box("cn1_pin_%s" % (index + 1), xpos, Y0 - 18.0, 12.0, 2.0, 5.0, 2.0))

    # Szyny i prowadnice na jednej wysokosci z arkuszem.
    path.append(box("rail_left", -130.0, -158.0, -48.0, 370.0, 8.0, 8.0))
    path.append(box("rail_right", -130.0, 150.0, -48.0, 370.0, 8.0, 8.0))
    path.append(box("entrance_guide", -120.0, -125.0, -2.2, 96.0, 250.0, 1.6))
    path.append(box("paper_guide", -24.0, -125.0, -2.2, 8.0, 250.0, 1.6))

    path.append(optical("sensor_fuser_buckle", -62.0, -146.0, -16.0))
    path.append(box("buckle_flag", -56.0, -132.0, -2.0, 1.4, 22.0, 12.0))
    path.append(optical("sensor_narrow_media", -62.0, 132.0, -16.0))
    path.append(box("narrow_flag", -56.0, 116.0, -2.0, 1.4, 18.0, 12.0))

    nip = Part.makeBox(8.0, 10.0, 16.0, FreeCAD.Vector(-30.0, -18.0, -2.0))
    nip = nip.fuse(Part.makeBox(8.0, 10.0, 16.0, FreeCAD.Vector(-30.0, 8.0, -2.0)))
    nip = nip.fuse(Part.makeBox(8.0, 36.0, 4.0, FreeCAD.Vector(-30.0, -18.0, 10.0)))
    path.append(put("sensor_fuser_nip", nip.removeSplitter()))

    path.append(optical("sensor_fuser_exit", 66.0, -12.0, 4.0))
    guide = [
        FreeCAD.Vector(70.0, 0, 14.0),
        FreeCAD.Vector(108.0, 0, 14.0),
        FreeCAD.Vector(108.0, 0, 16.0),
        FreeCAD.Vector(70.0, 0, 16.0),
    ]
    path.append(plate("redrive_guide", guide, -120.0, 240.0))
    path.append(optical("sensor_redrive", 86.0, 118.0, -16.0))
    path.append(box("redrive_flag", 90.0, 108.0, -2.0, 1.4, 14.0, 12.0))

    path.append(cyl_y("decurl_lower", 8.0, 240.0, 118.0, -120.0, -7.8))
    path.append(cyl_y("decurl_upper", 8.0, 240.0, 124.0, -120.0, 8.2))
    path.append(optical("sensor_paper_exit", 142.0, 108.0, -16.0))
    path.append(box("exit_flag", 146.0, 100.0, -2.0, 1.4, 12.0, 12.0))

    diverter = [
        FreeCAD.Vector(156.0, 0, 1.2),
        FreeCAD.Vector(184.0, 0, 7.0),
        FreeCAD.Vector(184.0, 0, 8.4),
        FreeCAD.Vector(156.0, 0, 2.6),
    ]
    path.append(plate("diverter", diverter, -115.0, 230.0))
    duplex = [
        FreeCAD.Vector(158.0, 0, -3.0),
        FreeCAD.Vector(196.0, 0, -8.0),
        FreeCAD.Vector(196.0, 0, -9.4),
        FreeCAD.Vector(158.0, 0, -4.4),
    ]
    path.append(plate("duplex_entry", duplex, -115.0, 230.0))

    path.append(cyl_y("exit_roller", 12.0, 250.0, 206.0, -125.0, -11.8))
    path.append(cyl_y("exit_idler", 8.0, 230.0, 206.0, -115.0, 8.3))
    path.append(optical("sensor_bin_full", 224.0, -146.0, 2.0))
    path.append(box("bin_flag", 218.0, -134.0, 6.0, 12.0, 1.4, 14.0))

    path.append(box("arkusz_in", -110.0, -105.0, 0.05, 86.0, 210.0, 0.18))
    path.append(box("arkusz_out", 56.0, -105.0, 0.05, 160.0, 210.0, 0.18))

    drive.append(gear("fuser_drive_gear", 16.0, 8.0, NIP_X, Y0 - 18.0, roll_z, 18))
    drive.append(gear("pinion", 8.0, 8.0, NIP_X, Y0 - 18.0, roll_z + 22.0, 12))
    drive.append(box("motor_fuser", NIP_X - 16.0, Y0 - 78.0, roll_z + 6.0, 32.0, 42.0, 32.0))
    drive.append(cyl_y("motor_shaft", 4.0, 20.0, NIP_X, Y0 - 36.0, roll_z + 22.0))

    fan_y = Y0 - 36.0
    fan_parts = [
        Part.makeCylinder(8.0, 10.0, FreeCAD.Vector(NIP_X, fan_y, BELT_R), FreeCAD.Vector(0, 1, 0)),
        Part.makeCylinder(24.0, 8.0, FreeCAD.Vector(NIP_X, fan_y + 1.0, BELT_R), FreeCAD.Vector(0, 1, 0)).cut(
            Part.makeCylinder(18.0, 8.0, FreeCAD.Vector(NIP_X, fan_y + 1.0, BELT_R), FreeCAD.Vector(0, 1, 0))
        ),
    ]
    for index in range(7):
        blade = Part.makeBox(2.2, 2.0, 14.0, FreeCAD.Vector(NIP_X - 1.1, fan_y + 4.0, BELT_R + 6.0))
        blade.rotate(FreeCAD.Vector(NIP_X, fan_y + 5.0, BELT_R), FreeCAD.Vector(0, 1, 0), index * (360.0 / 7.0))
        fan_parts.append(blade)
    drive.append(put("fuser_fan", Part.makeCompound(fan_parts)))

    try:
        import Draft

        tag = Draft.makeShapeString("41X0253  type 01  220-240 V", "C:/Windows/Fonts/arial.ttf", 6.5)
        tag.Placement = FreeCAD.Placement(FreeCAD.Vector(-8.0, -70.0, 37.2), FreeCAD.Rotation())
        tag.Label = "oznaczenie_41X0253"
    except Exception as exc:
        sys.stderr.write("napis pominiety: %s\n" % exc)

    def pack(name, objects):
        group = doc.addObject("App::DocumentObjectGroup", name)
        group.Group = objects
        return group

    pack("fuser_41X0253", cru)
    pack("naped", drive)
    pack("sciezka_papieru", path)

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
