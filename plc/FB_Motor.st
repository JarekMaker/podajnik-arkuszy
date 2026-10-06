(* Stycznik silnika. FaultIn przychodzi z termika.
   Gdy UseFeedback = TRUE, brak styku pomocniczego dluzej niz 500 ms jest awaria napedu. *)
FUNCTION_BLOCK FB_Motor
VAR_INPUT
    RunCmd : BOOL;
    Feedback : BOOL;
    UseFeedback : BOOL;
    FaultIn : BOOL;
    Reset : BOOL;
END_VAR
VAR_OUTPUT
    Run : BOOL;
    Fault : BOOL;
END_VAR
VAR
    TonFb : TON;
END_VAR

IF FaultIn THEN
    Fault := TRUE;
END_IF;

IF Reset AND NOT FaultIn THEN
    Fault := FALSE;
END_IF;

IF Fault THEN
    Run := FALSE;
    TonFb(IN := FALSE, PT := T#500ms);
ELSE
    IF UseFeedback THEN
        TonFb(IN := RunCmd AND NOT Feedback, PT := T#500ms);
    ELSE
        TonFb(IN := FALSE, PT := T#500ms);
    END_IF;

    IF TonFb.Q THEN
        Fault := TRUE;
        Run := FALSE;
    ELSE
        Run := RunCmd;
    END_IF;
END_IF;

END_FUNCTION_BLOCK
