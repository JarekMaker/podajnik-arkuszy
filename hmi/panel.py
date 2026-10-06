"""Konsola operatora podajnika.

Demo, bez sterownika:
    py hmi/panel.py

Odczyt stanowiska OpenPLC po Modbus TCP (rejestry z plc/MAIN.st):
    py -m pip install pymodbus
    py hmi/panel.py modbus 127.0.0.1
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sheet_logic import STATE_NAME, Feeder, Inputs


def show(label, feeder):
    print(
        f"{label:<12} stan={STATE_NAME[feeder.state]:<10} "
        f"motor={int(feeder.motor)} sprzeglo={int(feeder.clutch)} "
        f"rejestr={int(feeder.gate)} arkusze={feeder.sheet_count} "
        f"grzalka={feeder.heat_out:5.1f}%"
    )


def demo():
    feeder = Feeder()
    print("Kasowanie po wlaczeniu zasilania")
    show("zasilanie", feeder.step(Inputs()))
    show("RESET", feeder.step(Inputs(reset=True)))
    show("gotowy", feeder.step(Inputs()))

    print("\nArkusz przechodzi")
    show("START", feeder.step(Inputs(start=True)))
    show("wejscie", feeder.step(Inputs(sens_entry=True)))
    show("rejestr", feeder.step(Inputs(sens_entry=True, sens_register=True)))
    show("wyjscie", feeder.step(Inputs(sens_exit=True)))
    show("pusty", feeder.step(Inputs()))
    show("nastepny", feeder.step(Inputs()))

    print("\nBrak czujnika rejestracji")
    show("START", feeder.step(Inputs(start=True)))
    show("wejscie", feeder.step(Inputs(sens_entry=True)))
    last = feeder
    for _ in range(80):
        last = feeder.step(Inputs(sens_entry=True))
    show("timeout", last)


def poll(host, port=502):
    try:
        from pymodbus.client import ModbusTcpClient
    except ImportError:
        print("Brak pymodbus. Zainstaluj: py -m pip install pymodbus")
        return 1

    client = ModbusTcpClient(host, port=port)
    if not client.connect():
        print(f"Brak polaczenia z {host}:{port}")
        return 1

    # OpenPLC: pierwszy rejestr holding to %QW0.
    result = client.read_holding_registers(0, count=4, slave=1)
    client.close()
    if result.isError():
        print(result)
        return 1

    heater, state, sheets, temp_raw = result.registers
    name = STATE_NAME.get(state, str(state))
    print(
        f"stan={name} arkusze={sheets} "
        f"grzalka={heater / 10:.1f}% temperatura={temp_raw / 10:.1f} C"
    )
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "modbus":
        if len(sys.argv) < 3:
            print("Uzycie: py hmi/panel.py modbus ADRES")
            return 1
        return poll(sys.argv[2])
    demo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
