(* Predkosc silnika fusera od czujnika wybrzuszenia przed nipem.
   Za duze wybrzuszenie: przyspiesz, zeby nie zgniesc arkusza.
   Za male: zwolnij, zeby nie rozmazac toneru na pasie.
   Waskie medium obcina predkosc. Zawiniecie na pasie zatrzymuje naped. *)
FUNCTION_BLOCK FB_FuserBuckle
VAR_INPUT
    Enable : BOOL;
    Nip : BOOL;
    BuckleHigh : BOOL;
    BuckleLow : BOOL;
    NarrowMedia : BOOL;
    Wrap : BOOL;
END_VAR
VAR_OUTPUT
    SpeedPct : INT;
    HeaterOn : BOOL;
    Jam : BOOL;
END_VAR

IF NOT Enable OR Wrap THEN
    SpeedPct := 0;
    HeaterOn := FALSE;
    Jam := Wrap;
ELSE
    Jam := FALSE;
    HeaterOn := TRUE; (* ceramika w pasie *)
    SpeedPct := 100;

    IF Nip AND BuckleHigh THEN
        SpeedPct := 130;
    ELSIF Nip AND BuckleLow THEN
        SpeedPct := 70;
    END_IF;

    IF NarrowMedia AND (SpeedPct > 80) THEN
        SpeedPct := 80;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
