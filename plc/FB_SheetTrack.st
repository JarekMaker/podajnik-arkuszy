(* Sciezka arkusza: sprzeglo podaje, czujnik wejscia, rejestracja, czujnik wyjscia.
   Brak czujnika w czasie JamTime (domyslnie 800 ms) = zaciecie.
   Przerwanie cyklu, gdy arkusz jest jeszcze na czujniku, tez jest zacieciem.
   Kasowanie dziala tylko przy pustej sciezce. *)
FUNCTION_BLOCK FB_SheetTrack
VAR_INPUT
    FeedCmd : BOOL;
    SensEntry : BOOL;
    SensRegister : BOOL;
    SensExit : BOOL;
    Reset : BOOL;
    JamTime : TIME := T#800ms;
END_VAR
VAR_OUTPUT
    MotorCmd : BOOL;
    Clutch : BOOL;
    AtRegister : BOOL;
    Jam : BOOL;
    Busy : BOOL;
    SheetCount : INT;
    PhaseOut : INT;
END_VAR
VAR
    Phase : INT := 0; (* 0 postoj, 1 czekam na rejestracje, 2 przejazd, 3 zejscie z czujnika *)
    TonReg : TON;
    TonExit : TON;
    rEntry : R_TRIG;
    rExit : R_TRIG;
END_VAR

rEntry(CLK := SensEntry);
rExit(CLK := SensExit);
TonReg(IN := (Phase = 1) AND NOT Jam, PT := JamTime);
TonExit(IN := (Phase = 2) AND NOT Jam, PT := JamTime);

IF Reset AND NOT SensEntry AND NOT SensRegister AND NOT SensExit THEN
    Jam := FALSE;
    Phase := 0;
END_IF;

IF Jam THEN
    MotorCmd := FALSE;
    Clutch := FALSE;
    AtRegister := FALSE;
ELSIF NOT FeedCmd AND (Phase <> 0) THEN
    IF SensEntry OR SensRegister OR SensExit THEN
        Jam := TRUE;
    ELSE
        Phase := 0;
    END_IF;
    MotorCmd := FALSE;
    Clutch := FALSE;
    AtRegister := FALSE;
ELSIF Phase = 0 THEN
    AtRegister := FALSE;
    IF FeedCmd AND rEntry.Q THEN
        Clutch := FALSE;
        MotorCmd := TRUE;
        Phase := 1;
    ELSIF FeedCmd AND (SensEntry OR SensRegister OR SensExit) THEN
        Jam := TRUE;
        Clutch := FALSE;
        MotorCmd := FALSE;
    ELSIF FeedCmd THEN
        Clutch := TRUE;
        MotorCmd := TRUE;
    ELSE
        Clutch := FALSE;
        MotorCmd := FALSE;
    END_IF;
ELSIF Phase = 1 THEN
    Clutch := FALSE;
    MotorCmd := TRUE;
    AtRegister := FALSE;
    IF SensRegister THEN
        Phase := 2;
        AtRegister := TRUE;
    ELSIF TonReg.Q THEN
        Jam := TRUE;
        Phase := 0;
        MotorCmd := FALSE;
    END_IF;
ELSIF Phase = 2 THEN
    Clutch := FALSE;
    MotorCmd := TRUE;
    AtRegister := TRUE;
    IF rExit.Q THEN
        SheetCount := SheetCount + 1;
        Phase := 3;
        AtRegister := FALSE;
    ELSIF TonExit.Q THEN
        Jam := TRUE;
        Phase := 0;
        MotorCmd := FALSE;
        AtRegister := FALSE;
    END_IF;
ELSE
    Clutch := FALSE;
    AtRegister := FALSE;
    MotorCmd := TRUE;
    IF NOT SensExit AND NOT SensEntry AND NOT SensRegister THEN
        Phase := 0;
        MotorCmd := FALSE;
    END_IF;
END_IF;

IF Jam THEN
    MotorCmd := FALSE;
    Clutch := FALSE;
    AtRegister := FALSE;
END_IF;

Busy := Jam OR (Phase <> 0) OR Clutch;
PhaseOut := Phase;

END_FUNCTION_BLOCK
