(* Zezwolenie na podanie, gdy rolka 24 V jest w pasmie.
   Zadanie regulatora to 80 C. Ponizej 70 C start jest martwy.
   Powyzej 95 C to przegrzanie: grzalka odpada, nowy arkusz tez. *)
FUNCTION_BLOCK FB_Warmup
VAR_INPUT
    Enable : BOOL;
    Actual : REAL;
END_VAR
VAR_OUTPUT
    Ready : BOOL;
    Heating : BOOL;
    Overtemp : BOOL;
END_VAR

Overtemp := Enable AND (Actual > 95.0);
Ready := Enable AND (Actual >= 70.0) AND (Actual <= 95.0);
Heating := Enable AND (Actual < 70.0);

END_FUNCTION_BLOCK
