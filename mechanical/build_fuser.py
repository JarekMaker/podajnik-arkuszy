"""Fuser type 01, 220-240 V, czesc 41X0253.

Zrodlo: serwisowka 7528 (CX725, XC4140 i ta sama rodzina).
Rozdzial Theory of operation, Fuser section, plus katalog czesci
i kody 121.5x grzalek. Wymiary grzalki z opisu konstrukcji pasa
Lexmarka: panel okolo 230 mm, nip na dole pasa, walek dociskowy
pod pasem.

Pas kreci sie wokol korpusu z grzalka. Walek dociskowy (backup roll)
dopycha pas od dolu: tam jest nip, cieplo i nacisk wtapiaja toner.
Za nipem palce redrive sciagaja arkusz z pasa, zeby nie nawinal sie
na pas. Czujnik wyjsciowy fuser exit pilnuje tego samego.

Os X to kierunek papieru. Os Y to szerokosc kartki: minus to lewa
strona (czujnik wybrzuszenia), plus to prawa (czujnik waskiego
medium). Tak jest w instrukcji zdejmowania tych dwoch czujnikow.

    freecadcmd mechanical/build_fuser.py

Wymiary w milimetrach. To model pogladowy sekcji, nie rysunek
warsztatowy: serwisowka nie podaje tolerancji.
"""

import os
import sys

HEATER_LEN = 230.0
BELT_WIDTH = 270.0
ROLL_R = 18.0
BELT_R = 16.0
BELT_STRAIGHT = 40.0
NIP_X = BELT_STRAIGHT / 2.0


def main():
    try:
        import FreeCAD
        import Part
    except ImportError:
        sys.stderr.write("Uruchom przez freecadcmd mechanical/build_fuser.py\n")
        return 1

    doc = FreeCAD.newDocument("fuser")
    colors = {}
    transparent = {}

    def put(name, shape, color, alpha=None):
        if not shape.isValid() or shape.Volume < 1.0:
            raise RuntimeError(name)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        colors[name] = color
        if alpha is not None:
            transparent[name] = alpha
        return obj

    def along_y(name, radius, length, x, y, z, color):
        shape = Part.makeCylinder(
            radius, length, FreeCAD.Vector(x, y, z), FreeCAD.Vector(0, 1, 0)
        )
        return put(name, shape, color)

    def box(name, x, y, z, dx, dy, dz, color, alpha=None):
        return put(name, Part.makeBox(dx, dy, dz, FreeCAD.Vector(x, y, z)), color, alpha)

    def fuse(name, shapes, color):
        solid = shapes[0]
        for other in shapes[1:]:
            solid = solid.fuse(other)
        return put(name, solid.removeSplitter(), color)

    def plate_xz(name, points, y0, dy, color):
        wire = Part.makePolygon(points + [points[0]])
        solid = Part.Face(wire).extrude(FreeCAD.Vector(0, dy, 0))
        solid.translate(FreeCAD.Vector(0, y0, 0))
        return put(name, solid, color)

    def belt_loop(y0, length, x0, z0, straight, radius, thick):
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
        solid.translate(FreeCAD.Vector(0, y0, 0))
        return solid

    y_belt = -BELT_WIDTH / 2.0
    belt_z = BELT_R
    roll_y = y_belt + 12.0
    roll_len = BELT_WIDTH - 28.0
    roll_z = 1.6 - ROLL_R

    cru = []
    cru.append(
        put(
            "fuser_belt",
            belt_loop(y_belt, BELT_WIDTH, 0.0, belt_z, BELT_STRAIGHT, BELT_R, 1.4),
            (0.16, 0.13, 0.11),
        )
    )
    housing = Part.makeBox(24.0, BELT_WIDTH - 20.0, 20.0, FreeCAD.Vector(8.0, y_belt + 10.0, 5.5))
    # Okna w korpusie, zeby z gory bylo widac trzy strefy grzalki.
    for slot_y, slot_dy in ((-107.0, 60.0), (-30.0, 60.0), (47.0, 60.0)):
        housing = housing.cut(Part.makeBox(12.0, slot_dy, 24.0, FreeCAD.Vector(13.0, slot_y, 3.7)))
    cru.append(put("heater_housing", housing, (0.45, 0.46, 0.48)))

    # Trzy odcinki grzalki stykaja sie ze soba. Prawa strefa jest od strony
    # czujnika waskiego medium: waski arkusz jej nie zakrywa.
    zones = [
        ("heater_main", -115.0, 76.0, (0.93, 0.84, 0.64)),
        ("heater_middle", -38.0, 76.0, (0.86, 0.62, 0.32)),
        ("heater_secondary", 39.0, 76.0, (0.72, 0.38, 0.18)),
    ]
    for name, y, dy, color in zones:
        cru.append(box(name, 12.5, y, 1.45, 15.0, dy, 2.2, color))
        cru.append(
            box(
                "thermistor_" + name.split("_", 1)[1],
                16.0,
                y + dy / 2.0 - 4.0,
                3.65,
                7.0,
                8.0,
                5.0,
                (0.85, 0.28, 0.12),
            )
        )

    cru.append(box("thermistor_edge", 16.0, 100.0, 3.65, 7.0, 8.0, 5.0, (0.85, 0.28, 0.12)))
    cru.append(box("thermistor_belt_contact", 6.0, -8.0, 1.6, 5.0, 7.0, 2.2, (0.85, 0.28, 0.12)))
    cru.append(box("thermistor_belt_noncontact", 16.0, 18.0, 34.5, 8.0, 10.0, 6.0, (0.25, 0.25, 0.28)))

    cru.append(along_y("backup_roll", ROLL_R, roll_len, NIP_X, roll_y, roll_z, (0.10, 0.10, 0.11)))
    cru.append(along_y("backup_shaft", 6.0, BELT_WIDTH + 36.0, NIP_X, y_belt - 28.0, roll_z, (0.72, 0.73, 0.75)))
    cru.append(box("thermistor_backup", NIP_X - 4.0, y_belt - 24.0, roll_z - 4.0, 8.0, 8.0, 8.0, (0.85, 0.28, 0.12)))
    cru.append(box("thermistor_backup_narrow", NIP_X - 4.0, y_belt + BELT_WIDTH - 4.0, roll_z - 4.0, 8.0, 8.0, 8.0, (0.85, 0.28, 0.12)))

    # Redrive deflector: palce za nipem, zdejmuja arkusz z pasa.
    for index, ypos in enumerate((-80.0, -40.0, 0.0, 40.0, 80.0)):
        pts = [
            FreeCAD.Vector(36.0, 0, 1.0),
            FreeCAD.Vector(54.0, 0, 8.0),
            FreeCAD.Vector(54.0, 0, 9.4),
            FreeCAD.Vector(36.0, 0, 2.2),
        ]
        cru.append(plate_xz(f"stripper_{index + 1}", pts, ypos, 4.0, (0.78, 0.79, 0.80)))

    cheek_color = (0.55, 0.57, 0.60)
    for name, ypos in (("end_left", y_belt - 8.0), ("end_right", y_belt + BELT_WIDTH)):
        plate = Part.makeBox(78.0, 7.0, 62.0, FreeCAD.Vector(-16.0, ypos, -28.0))
        window = Part.makeBox(52.0, 7.0, 36.0, FreeCAD.Vector(-2.0, ypos, -2.0))
        cru.append(put(name, plate.cut(window), cheek_color))

    cru.append(box("fuser_base", -8.0, y_belt, -36.0, 56.0, BELT_WIDTH, 4.0, cheek_color))
    cru.append(box("fuser_lock", 62.0, y_belt + BELT_WIDTH - 2.0, 8.0, 22.0, 8.0, 8.0, (0.72, 0.14, 0.12)))
    cru.append(box("lock_lever", 76.0, y_belt + BELT_WIDTH - 1.0, 16.0, 6.0, 6.0, 28.0, (0.72, 0.14, 0.12)))

    # CN1: AC Common i trzy wyjscia grzalek.
    cru.append(box("connector_cn1", -4.0, y_belt - 16.0, 6.0, 16.0, 12.0, 14.0, (0.12, 0.12, 0.13)))
    for index, xpos in enumerate((0.0, 4.0, 8.0, 12.0)):
        cru.append(
            box(f"cn1_pin_{index + 1}", xpos, y_belt - 20.0, 10.0, 2.2, 6.0, 2.2, (0.74, 0.60, 0.30))
        )

    path = []
    ramp = [
        FreeCAD.Vector(-98.0, 0, -24.0),
        FreeCAD.Vector(-64.0, 0, 0.0),
        FreeCAD.Vector(-64.0, 0, -1.6),
        FreeCAD.Vector(-98.0, 0, -25.6),
    ]
    path.append(plate_xz("entrance_guide", ramp, -120.0, 240.0, (0.70, 0.71, 0.73)))
    path.append(box("paper_guide", -66.0, -130.0, -3.0, 40.0, 260.0, 1.6, (0.70, 0.71, 0.73)))

    # Lewy czujnik to wybrzuszenie, prawy to waskie medium.
    path.append(box("sensor_fuser_buckle", -58.0, -148.0, -6.0, 18.0, 22.0, 16.0, (0.16, 0.38, 0.78)))
    path.append(box("buckle_flag", -50.0, -128.0, -1.0, 2.0, 16.0, 10.0, (0.16, 0.38, 0.78)))
    path.append(box("sensor_narrow_media", -58.0, 126.0, -6.0, 18.0, 22.0, 16.0, (0.16, 0.38, 0.78)))
    path.append(box("narrow_flag", -50.0, 112.0, -1.0, 2.0, 16.0, 10.0, (0.16, 0.38, 0.78)))

    # Czujnik nip stoi przed pasem i patrzy, czy walek trzyma arkusz.
    nip_sensor = Part.makeBox(12.0, 8.0, 18.0, FreeCAD.Vector(-40.0, -22.0, 0.0))
    nip_sensor = nip_sensor.fuse(Part.makeBox(12.0, 8.0, 18.0, FreeCAD.Vector(-40.0, 14.0, 0.0)))
    nip_sensor = nip_sensor.fuse(Part.makeBox(12.0, 44.0, 5.0, FreeCAD.Vector(-40.0, -22.0, 13.0)))
    path.append(put("sensor_fuser_nip", nip_sensor.removeSplitter(), (0.95, 0.78, 0.15)))

    path.append(box("sensor_fuser_exit", 58.0, -10.0, 10.0, 14.0, 20.0, 12.0, (0.16, 0.38, 0.78)))

    guide = [
        FreeCAD.Vector(60.0, 0, 16.0),
        FreeCAD.Vector(96.0, 0, 20.0),
        FreeCAD.Vector(96.0, 0, 22.0),
        FreeCAD.Vector(58.0, 0, 18.0),
    ]
    path.append(plate_xz("redrive_guide", guide, -125.0, 250.0, (0.62, 0.66, 0.70)))

    path.append(along_y("decurl_lower", 9.0, 230.0, 112.0, -115.0, -5.0, (0.55, 0.56, 0.58)))
    path.append(along_y("decurl_upper", 9.0, 230.0, 120.0, -115.0, 9.0, (0.55, 0.56, 0.58)))
    path.append(box("sensor_paper_exit", 136.0, 96.0, 2.0, 12.0, 16.0, 14.0, (0.16, 0.38, 0.78)))

    diverter = [
        FreeCAD.Vector(148.0, 0, 6.0),
        FreeCAD.Vector(176.0, 0, 24.0),
        FreeCAD.Vector(176.0, 0, 26.0),
        FreeCAD.Vector(148.0, 0, 8.0),
    ]
    path.append(plate_xz("diverter", diverter, -110.0, 220.0, (0.40, 0.42, 0.45)))
    duplex = [
        FreeCAD.Vector(150.0, 0, -2.0),
        FreeCAD.Vector(186.0, 0, -16.0),
        FreeCAD.Vector(186.0, 0, -18.0),
        FreeCAD.Vector(150.0, 0, -4.0),
    ]
    path.append(plate_xz("duplex_entry", duplex, -110.0, 220.0, (0.40, 0.42, 0.45)))

    path.append(along_y("exit_roller", 13.0, 240.0, 188.0, -120.0, 4.0, (0.32, 0.33, 0.35)))
    path.append(along_y("exit_idler", 8.0, 220.0, 188.0, -110.0, 22.0, (0.62, 0.63, 0.65)))
    path.append(box("sensor_bin_full", 214.0, -130.0, 24.0, 16.0, 18.0, 12.0, (0.16, 0.38, 0.78)))
    path.append(box("bin_flag", 206.0, -116.0, 20.0, 10.0, 2.0, 16.0, (0.16, 0.38, 0.78)))

    path.append(box("arkusz_in", -62.0, -105.0, 0.15, 24.0, 210.0, 0.25, (0.96, 0.94, 0.84), 35))
    path.append(box("arkusz_out", 48.0, -105.0, 0.15, 150.0, 210.0, 0.25, (0.96, 0.94, 0.84), 35))

    drive = []
    drive.append(along_y("fuser_drive_gear", 22.0, 10.0, NIP_X, y_belt - 26.0, roll_z, (0.72, 0.73, 0.75)))
    drive.append(along_y("pinion", 10.0, 16.0, NIP_X, y_belt - 36.0, roll_z + 30.0, (0.72, 0.73, 0.75)))
    drive.append(
        box(
            "motor_fuser",
            NIP_X - 16.0,
            y_belt - 78.0,
            roll_z + 14.0,
            32.0,
            42.0,
            32.0,
            (0.14, 0.14, 0.15),
        )
    )

    try:
        import Draft

        tag = Draft.makeShapeString(
            "41X0253  type 01  220-240 V",
            "C:/Windows/Fonts/arial.ttf",
            7.0,
        )
        tag.Placement = FreeCAD.Placement(
            FreeCAD.Vector(-2.0, -78.0, 40.0), FreeCAD.Rotation()
        )
        tag.Label = "oznaczenie_41X0253"
        colors[tag.Name] = (0.05, 0.05, 0.05)
        cru.append(tag)
    except Exception as exc:
        sys.stderr.write(f"napis pominiety: {exc}\n")

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
