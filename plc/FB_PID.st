(* Regulator grzalki 24 V. Wyjscie 0..100 procent.
   Pierwszy cykl po wlaczeniu nie daje kopa od czlonu D. *)
FUNCTION_BLOCK FB_PID
VAR_INPUT
    Enable : BOOL;
    Setpoint : REAL;
    Actual : REAL;
    Kp : REAL;
    Ki : REAL;
    Kd : REAL;
    OutMin : REAL;
    OutMax : REAL;
    Cycle : REAL; (* okres obiegu w sekundach, przy cyklu 10 ms wpisz 0.01 *)
END_VAR
VAR_OUTPUT
    Out : REAL;
END_VAR
VAR
    Integral : REAL := 0.0;
    PrevError : REAL := 0.0;
    Armed : BOOL := FALSE;
    Error : REAL;
    Deriv : REAL;
    Raw : REAL;
END_VAR

IF NOT Enable OR (Cycle <= 0.0) THEN
    Integral := 0.0;
    PrevError := 0.0;
    Armed := FALSE;
    Out := 0.0;
ELSE
    Error := Setpoint - Actual;
    IF NOT Armed THEN
        PrevError := Error;
        Integral := 0.0;
        Armed := TRUE;
    END_IF;

    Integral := Integral + (Error * Cycle);
    Deriv := (Error - PrevError) / Cycle;
    PrevError := Error;
    Raw := (Kp * Error) + (Ki * Integral) + (Kd * Deriv);

    IF Raw > OutMax THEN
        Raw := OutMax;
        Integral := Integral - (Error * Cycle);
    ELSIF Raw < OutMin THEN
        Raw := OutMin;
        Integral := Integral - (Error * Cycle);
    END_IF;

    Out := Raw;
END_IF;

END_FUNCTION_BLOCK
