# podajnik-arkuszy

![Podajnik arkuszy, widok z boku](mechanical/podajnik.svg)

Podgląd w przeglądarce: [hmi/podglad.html](hmi/podglad.html). Najpierw Reset, potem Start.

Fuser, ścieżka po transferze: [hmi/fuser.html](hmi/fuser.html).

Wirtualna stacja podawania arkusza. Program PLC prowadzi arkusz po czujnikach, schemat opisuje szafę, model opisuje mechanikę, a panel czyta stan maszyny. Logika jest ta sama co w trakcie papieru drukarki: czujnik ma zadziałać w czasie, inaczej jest zacięcie i napęd odpada.

## Co gdzie leży

| Folder | Narzędzie | Zawartość |
|---|---|---|
| `plc/` | OpenPLC, CODESYS albo SCL w TIA Portal | IEC 61131-3, język ST. Bloki `FB_EStop`, `FB_Motor`, `FB_SheetTrack`, `FB_PID` i program `Main` |
| `electrical/` | KiCad 8 | schemat ideowy szafy i lista wejść/wyjść |
| `mechanical/` | FreeCAD | parametryczny model ramy i rolek, podgląd SVG |
| `hmi/` | Python 3 | podgląd, testy, konsola i mapa Modbus |

Adresy `%IX`, `%QX`, `%IW`, `%QW` są wspólne dla `plc/MAIN.st`, `electrical/io_map.csv` i schematu.

Papiery obok kodu: [sekwencja](plc/sekwencja.md), [alarmy](electrical/alarmy.csv), [Modbus](hmi/modbus.csv), [operator](hmi/operator.md), [odbiór](electrical/odbior.md).

## Sekwencja

Po włączeniu zasilania maszyna stoi w `ESTOP`, dopóki operator nie skasuje obwodu. Sam powrót grzyba nie daje ruchu.

`START` włącza sprzęgło. Arkusz ma dojść do czujnika wejścia, potem do rejestracji, potem do wyjścia. Na każdy odcinek jest 800 ms. Brak czujnika, arkusz już leżący na ścieżce albo STOP w trakcie przejazdu dają `JAM`. Kasowanie zacięcia działa tylko przy pustej ścieżce. Otwarta pokrywa zrzuca bieg.

Kody stanu na `%QW1`:

| Kod | Stan |
|---|---|
| 1 | READY |
| 2 | FEED |
| 3 | REGISTER |
| 4 | RUN |
| 5 | JAM |
| 6 | FAULT |
| 7 | ESTOP |
| 8 | COVER |

Grzałka to rolka 24 V z zadaniem 80 °C, nie piec lasera. Regulator jest w `FB_PID`. Wyjście analogowe `%QW0` ma zakres 0..1000, czyli 0,0..100,0 %.

`UseFeedback` w `Main` jest ustawione na FALSE. Na prawdziwej szafie przestaw je na TRUE i podepnij styk pomocniczy stycznika pod `%IX1.1`. Brak styku przez 500 ms jest awarią napędu.

## Test logiki

Python nie wymaga bibliotek.

```bat
py hmi\test_sheet_logic.py
py hmi\panel.py
```

`panel.py` wypisuje przejście arkusza i zacięcie po czasie. To jest materiał do krótkiego nagrania.

## OpenPLC

1. Zainstaluj [OpenPLC Editor](https://autonomylogic.com/).
2. Załóż projekt z programem `Main` i czterema blokami funkcyjnymi.
3. Wklej pliki z `plc/`. Nazwy bloków muszą zostać: `FB_EStop`, `FB_Motor`, `FB_SheetTrack`, `FB_PID`.
4. Ustaw cykl zadania na 10 ms.
5. Wgraj program na runtime i włącz serwer Modbus TCP.

W OpenPLC pierwszy rejestr holding to `%QW0`.

```bat
py -m pip install pymodbus
py hmi\panel.py modbus 127.0.0.1
```

Te same pliki ST wkleja się do CODESYS. W TIA Portal odpowiadają im bloki SCL: składnia przypisania i wywołań bloków jest ta sama.

## KiCad

Otwieraj `electrical/podajnik.kicad_pro`, nie sam plik schematu. Schemat jest rysowany z listy adresów skryptem:

```bat
py electrical\build_schematic.py
```

## FreeCAD

Podgląd z boku jest w `mechanical/podajnik.svg`. Model 3D:

```bat
freecadcmd mechanical\build_model.py
```

Wymiary ramy, rolek i rozstawu są na górze `mechanical/build_model.py`. Zmiana `LENGTH` przebudowuje ramę. Plik `podajnik.FCStd` powstaje obok skryptu i nie wchodzi do gita.
