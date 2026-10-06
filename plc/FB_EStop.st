(* Zezwolenie ruchu. Po otwarciu obwodu bezpieczenstwa i po wlaczeniu zasilania
   wymagane jest zbocze kasowania. Sam powrot styku bezpieczenstwa nie uruchamia maszyny. *)
FUNCTION_BLOCK FB_EStop
VAR_INPUT
    EStopOk : BOOL;
    Reset : BOOL;
END_VAR
VAR_OUTPUT
    RunEnable : BOOL;
END_VAR
VAR
    NeedReset : BOOL := TRUE;
END_VAR

IF NOT EStopOk THEN
    NeedReset := TRUE;
    RunEnable := FALSE;
ELSIF NeedReset THEN
    RunEnable := FALSE;
    IF Reset THEN
        NeedReset := FALSE;
        RunEnable := TRUE;
    END_IF;
ELSE
    RunEnable := TRUE;
END_IF;

END_FUNCTION_BLOCK
