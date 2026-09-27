#!/bin/bash
# pcap.sh [dist=420] [yawOffset=0] [height=140] -> captures the PIE pawn from a camera orbiting it
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
D=$(dirname "$0")
J=$(UE_FULL=1 "$PY" "$D/ue.py" script "$D/s/pawn.py" 2>/dev/null)
read X Y Z P YAW <<< $("$PY" -c "
import json,math,sys
d=json.loads(sys.argv[1])['xf']; l=d['location']; yaw=d['rotation']['yaw']+float(sys.argv[3])
dist=float(sys.argv[2]); h=float(sys.argv[4]); r=math.radians(yaw)
x=l['x']-math.cos(r)*dist; y=l['y']-math.sin(r)*dist; z=l['z']+h
pitch=-math.degrees(math.atan2(h-20,dist))
print(round(x,1),round(y,1),round(z,1),round(pitch,1),round(yaw,1))" "$J" "${1:-420}" "${2:-0}" "${3:-140}")
"$D/cap.sh" $X $Y $Z $P $YAW > /dev/null
ls -t "$D/shots" | head -1
