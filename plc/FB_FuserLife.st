(* Licznik fusera. W XC4140 komplet type 01 (41X0253) wymienia sie po 150 000 stron.
   Ostrzezenie od 140 000. Kasowanie jest osobne od resetu zaciecia.
   Na panel idzie liczba tysiecy: rejestr 16-bit nie zmiesci 150000. *)
FUNCTION_BLOCK FB_FuserLife
VAR_INPUT
    SheetCount : INT;
    ResetService : BOOL;
END_VAR
VAR_OUTPUT
    Thousands : INT;
    Warn : BOOL;
    Due : BOOL;
END_VAR
VAR
    Total : DINT := 0;
    Prev : INT := 0;
    Seen : BOOL := FALSE;
END_VAR

IF NOT Seen THEN
    Prev := SheetCount;
    Seen := TRUE;
END_IF;

IF ResetService THEN
    Total := 0;
ELSIF SheetCount <> Prev THEN
    Total := Total + 1;
END_IF;
Prev := SheetCount;

IF Total > 150000 THEN
    Total := 150000;
END_IF;

Thousands := DINT_TO_INT(Total / 1000);
Warn := Total >= 140000;
Due := Total >= 150000;

END_FUNCTION_BLOCK
