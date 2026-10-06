"""Rysuje schemat ideowy szafy jako plik KiCad 8.

Uruchomienie z katalogu repozytorium:
    py electrical/build_schematic.py
"""

import uuid
from pathlib import Path

ROOT = uuid.UUID("11111111-1111-4111-8111-111111111111")


def uid(number):
    return f"00000000-0000-4000-8000-{number:012d}"


def text(number, x, y, size, value):
    return f"""  (text "{value}"
    (at {x} {y} 0)
    (effects (font (size {size} {size})))
    (uuid "{uid(number)}")
  )"""


def rect(number, x1, y1, x2, y2):
    return f"""  (rectangle
    (start {x1} {y1})
    (end {x2} {y2})
    (stroke (width 0.4) (type solid))
    (fill (type none))
    (uuid "{uid(number)}")
  )"""


def line(number, points):
    pts = " ".join(f"(xy {x} {y})" for x, y in points)
    return f"""  (polyline
    (pts {pts})
    (stroke (width 0.3) (type solid))
    (uuid "{uid(number)}")
  )"""


def build():
    chunks = [
        "(kicad_sch",
        "  (version 20231120)",
        '  (generator "podajnik-arkuszy")',
        '  (generator_version "8.0")',
        f'  (uuid "{ROOT}")',
        '  (paper "A3")',
        "  (title_block",
        '    (title "Podajnik arkuszy — schemat ideowy szafy")',
        '    (date "2026-10-06")',
        '    (rev "A")',
        '    (company "JarekMaker")',
        '    (comment 1 "Adresy zgodne z plc/MAIN.st i io_map.csv")',
        '    (comment 2 "Obwod bezpieczenstwa rozrywa cewke stycznika K1")',
        "  )",
        "  (lib_symbols)",
    ]
    n = 1
    boxes = [
        (12, 16, 145, 128),
        (155, 16, 292, 168),
        (302, 16, 408, 150),
        (12, 138, 145, 232),
        (155, 178, 292, 232),
        (302, 160, 408, 232),
    ]
    for box in boxes:
        chunks.append(rect(n, *box))
        n += 1

    chunks.append(line(n, [(145, 70), (302, 70)]))
    n += 1

    labels = [
        (1, 18, 26, 3.2, "1  Bezpieczenstwo"),
        (2, 18, 36, 2.2, "S0  grzyb bezpieczenstwa NC"),
        (3, 18, 44, 2.2, "S1  pokrywa  I_CoverClosed %IX0.1"),
        (4, 18, 52, 2.2, "K0  przekaznik bezpieczenstwa"),
        (5, 18, 62, 2.2, "Styk K0 -> I_EstopOk %IX0.0"),
        (6, 18, 74, 2.2, "Linia w prawo tnie cewke K1."),
        (7, 18, 82, 2.2, "Sam powrot S0 nie daje ruchu:"),
        (8, 18, 90, 2.2, "program czeka na RESET %IX1.0"),
        (9, 18, 102, 2.2, "Zasilanie sterowania 24 V DC"),
        (10, 18, 110, 2.2, "Zasilacz za wylacznikiem serwisowym"),
        (11, 160, 26, 3.2, "2  Wejscia PLC"),
        (12, 160, 36, 2.2, "%IX0.2  czujnik wejscia arkusza"),
        (13, 160, 44, 2.2, "%IX0.3  czujnik rejestracji"),
        (14, 160, 52, 2.2, "%IX0.4  czujnik wyjscia"),
        (15, 160, 60, 2.2, "%IX0.5  termik silnika"),
        (16, 160, 68, 2.2, "%IX0.6  START    %IX0.7 STOP"),
        (17, 160, 76, 2.2, "%IX1.0  RESET"),
        (18, 160, 84, 2.2, "%IX1.1  styk pomocniczy K1"),
        (19, 160, 92, 2.2, "%IW2    temperatura 0.1 st. C"),
        (20, 160, 104, 2.2, "Czujniki optyczne jak w trakcie"),
        (21, 160, 112, 2.2, "papieru drukarki: arkusz ma"),
        (22, 160, 120, 2.2, "dojsc do nastepnego w 800 ms."),
        (23, 160, 132, 2.2, "Brak czujnika = zaciecie,"),
        (24, 160, 140, 2.2, "silnik i sprzeglo odpadaja."),
        (25, 308, 26, 3.2, "3  Naped i grzalka"),
        (26, 308, 36, 2.2, "K1  stycznik   %QX0.0"),
        (27, 308, 44, 2.2, "Y1  sprzeglo   %QX0.1"),
        (28, 308, 52, 2.2, "Y2  rejestr    %QX0.2"),
        (29, 308, 60, 2.2, "H1  praca      %QX0.3"),
        (30, 308, 68, 2.2, "H2  awaria     %QX0.4"),
        (31, 308, 76, 2.2, "E1  grzalka 24 V  %QX0.5"),
        (32, 308, 88, 2.2, "Analog grzalki %QW0"),
        (33, 308, 96, 2.2, "0..1000 = 0..100 %"),
        (34, 308, 108, 2.2, "Zadanie PID: 80 st. C"),
        (35, 308, 116, 2.2, "To rolka podgrzewana 24 V,"),
        (36, 308, 124, 2.2, "nie piec lasera na 230 V."),
        (37, 18, 148, 3.2, "4  Sekwencja"),
        (38, 18, 158, 2.2, "ESTOP -> RESET -> READY"),
        (39, 18, 166, 2.2, "START -> FEED (sprzeglo)"),
        (40, 18, 174, 2.2, "czujnik wejscia -> REGISTER"),
        (41, 18, 182, 2.2, "czujnik rejestracji -> RUN"),
        (42, 18, 190, 2.2, "czujnik wyjscia -> licznik"),
        (43, 18, 198, 2.2, "timeout 800 ms -> JAM"),
        (44, 18, 210, 2.2, "Kody %QW1: 1 READY  2 FEED"),
        (45, 18, 218, 2.2, "3 REGISTER  4 RUN  5 JAM"),
        (46, 18, 226, 2.2, "6 FAULT  7 ESTOP  8 COVER"),
        (47, 160, 188, 3.2, "5  Panel Modbus"),
        (48, 160, 198, 2.2, "Holding 0  %QW0  grzalka"),
        (49, 160, 206, 2.2, "Holding 1  %QW1  stan"),
        (50, 160, 214, 2.2, "Holding 2  %QW2  arkusze"),
        (51, 160, 222, 2.2, "Holding 3  %QW3  temperatura"),
        (52, 308, 172, 3.2, "6  Cykl PLC"),
        (53, 308, 182, 2.2, "Zadanie cykliczne 10 ms"),
        (54, 308, 190, 2.2, "Jezyk ST  IEC 61131-3"),
        (55, 308, 198, 2.2, "OpenPLC / CODESYS / SCL"),
        (56, 308, 210, 2.2, "UseFeedback = FALSE"),
        (57, 308, 218, 2.2, "do czasu podpiecia %IX1.1"),
    ]
    for index, (_, x, y, size, value) in enumerate(labels, start=20):
        chunks.append(text(index, x, y, size, value))

    chunks.append("  (sheet_instances")
    chunks.append('    (path "/"')
    chunks.append('      (page "1")')
    chunks.append("    )")
    chunks.append("  )")
    chunks.append(")")
    return "\n".join(chunks) + "\n"


def main():
    here = Path(__file__).resolve().parent
    target = here / "podajnik.kicad_sch"
    target.write_text(build(), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
