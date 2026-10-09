(* Podajnik arkuszy.
   OpenPLC Editor albo CODESYS: wklej FB_*.st jako bloki funkcyjne, a ten plik jako program.
   Cykl zadania: 10 ms.
   Adresy sa zgodne z electrical/io_map.csv.
   UseFeedback ustaw na TRUE dopiero po podpieciu styku pomocniczego stycznika pod I_MotorAux. *)
PROGRAM Main
VAR
    I_EstopOk AT %IX0.0 : BOOL;
    I_CoverClosed AT %IX0.1 : BOOL;
    I_SensEntry AT %IX0.2 : BOOL;
    I_SensRegister AT %IX0.3 : BOOL;
    I_SensExit AT %IX0.4 : BOOL;
    I_MotorFault AT %IX0.5 : BOOL;
    I_Start AT %IX0.6 : BOOL;
    I_Stop AT %IX0.7 : BOOL;
    I_Reset AT %IX1.0 : BOOL;
    I_MotorAux AT %IX1.1 : BOOL;
    I_FuserReset AT %IX1.2 : BOOL;
    I_Nip AT %IX1.3 : BOOL;
    I_BuckleHigh AT %IX1.4 : BOOL;
    I_BuckleLow AT %IX1.5 : BOOL;
    I_NarrowMedia AT %IX1.6 : BOOL;
    I_FuserWrap AT %IX1.7 : BOOL;
    IW_TempRaw AT %IW2 : INT;

    Q_Motor AT %QX0.0 : BOOL;
    Q_Clutch AT %QX0.1 : BOOL;
    Q_Gate AT %QX0.2 : BOOL;
    Q_LampRun AT %QX0.3 : BOOL;
    Q_LampFault AT %QX0.4 : BOOL;
    Q_Heater AT %QX0.5 : BOOL;
    Q_FuserMotor AT %QX0.6 : BOOL;

    QW_Heater AT %QW0 : INT; (* 0..1000 = 0.0..100.0 % *)
    QW_State AT %QW1 : INT;
    QW_Sheets AT %QW2 : INT;
    QW_Temp AT %QW3 : INT;
    QW_FuserK AT %QW4 : INT; (* tysiace stron od resetu fusera *)
    QW_FuserSvc AT %QW5 : INT; (* 0 ok, 1 ostrzezenie, 2 wymiana *)
    QW_FuserSpeed AT %QW6 : INT; (* procent predkosci silnika fusera *)

    EStop : FB_EStop;
    Drive : FB_Motor;
    Track : FB_SheetTrack;
    Heat : FB_PID;
    FuserLife : FB_FuserLife;
    Buckle : FB_FuserBuckle;
    rStart : R_TRIG;
    rStop : R_TRIG;
    rReset : R_TRIG;
    RunRequest : BOOL := FALSE;
    UseFeedback : BOOL := FALSE;
    MotionOk : BOOL;
    TempC : REAL;
    State : INT;
END_VAR

rStart(CLK := I_Start);
rStop(CLK := I_Stop);
rReset(CLK := I_Reset);

EStop(EStopOk := I_EstopOk, Reset := rReset.Q);

IF rStop.Q OR (NOT EStop.RunEnable) OR I_MotorFault OR (NOT I_CoverClosed) THEN
    RunRequest := FALSE;
END_IF;

MotionOk := EStop.RunEnable AND I_CoverClosed AND NOT I_MotorFault AND NOT Track.Jam;

FuserLife(SheetCount := Track.SheetCount, ResetService := I_FuserReset);
Buckle(
    Enable := EStop.RunEnable AND I_CoverClosed AND NOT FuserLife.Due,
    Nip := I_Nip,
    BuckleHigh := I_BuckleHigh,
    BuckleLow := I_BuckleLow,
    NarrowMedia := I_NarrowMedia,
    Wrap := I_FuserWrap
);

IF rStart.Q AND MotionOk AND NOT Track.Busy AND NOT FuserLife.Due AND NOT Buckle.Jam THEN
    RunRequest := TRUE;
END_IF;

Track(
    FeedCmd := RunRequest AND MotionOk,
    SensEntry := I_SensEntry,
    SensRegister := I_SensRegister,
    SensExit := I_SensExit,
    Reset := rReset.Q,
    JamTime := T#800ms
);

Drive(
    RunCmd := Track.MotorCmd AND MotionOk,
    Feedback := I_MotorAux,
    UseFeedback := UseFeedback,
    FaultIn := I_MotorFault,
    Reset := rReset.Q
);

TempC := INT_TO_REAL(IW_TempRaw) / 10.0;
Heat(
    Enable := EStop.RunEnable AND I_CoverClosed AND NOT Track.Jam AND NOT Drive.Fault,
    Setpoint := 80.0,
    Actual := TempC,
    Kp := 4.0,
    Ki := 0.8,
    Kd := 0.1,
    OutMin := 0.0,
    OutMax := 100.0,
    Cycle := 0.01
);

IF NOT EStop.RunEnable THEN
    State := 7;
ELSIF Drive.Fault OR I_MotorFault THEN
    State := 6;
ELSIF Buckle.Jam OR Track.Jam THEN
    State := 5;
ELSIF NOT I_CoverClosed THEN
    State := 8;
ELSIF Track.PhaseOut = 1 THEN
    State := 3;
ELSIF (Track.PhaseOut = 2) OR (Track.PhaseOut = 3) THEN
    State := 4;
ELSIF Track.Clutch THEN
    State := 2;
ELSE
    State := 1;
END_IF;

Q_Motor := Drive.Run AND EStop.RunEnable;
Q_Clutch := Track.Clutch AND EStop.RunEnable AND I_CoverClosed AND NOT Track.Jam;
Q_Gate := Track.AtRegister AND EStop.RunEnable AND I_CoverClosed AND NOT Track.Jam;
Q_LampRun := Q_Motor;
Q_LampFault := Track.Jam OR Drive.Fault OR NOT EStop.RunEnable OR FuserLife.Due OR Buckle.Jam;
Q_Heater := (Heat.Out > 1.0) AND Buckle.HeaterOn;
Q_FuserMotor := Buckle.SpeedPct > 0;

QW_Heater := REAL_TO_INT(Heat.Out * 10.0);
QW_State := State;
QW_Sheets := Track.SheetCount;
QW_Temp := IW_TempRaw;
QW_FuserK := FuserLife.Thousands;
IF FuserLife.Due THEN
    QW_FuserSvc := 2;
ELSIF FuserLife.Warn THEN
    QW_FuserSvc := 1;
ELSE
    QW_FuserSvc := 0;
END_IF;
QW_FuserSpeed := Buckle.SpeedPct;

END_PROGRAM
