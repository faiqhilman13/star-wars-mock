#!/bin/bash
# zoom3.sh out.png "dx dy dz" ctrl absframe...   camera = ctrl_world + (dx,dy,dz) (world), looking at the ctrl
D=/c/Users/User/PROJECTS/jedi-arena/tools
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
out=$1; off=$2; ctrl=$3; shift 3; args=()
cat $D/s/anim3/lib3.py $D/s/anim3/hidebb.py > $D/s/anim3/_h.py; (cd $D && "$PY" ue.py script s/anim3/_h.py >/dev/null 2>&1)
read DX DY DZ <<< "$off"
for f in "$@"; do
  cat $D/s/anim3/lib3.py > $D/s/anim3/_s.py
  printf 'def run():\n    guard(); show(%s); w=getw("%s",%s); import time; time.sleep(0.3); return {"l":w["location"]}\n' $f $ctrl $f >> $D/s/anim3/_s.py
  J=$(cd $D && "$PY" ue.py script s/anim3/_s.py)
  c=$("$PY" -c "
import json,math,sys
d=json.loads(sys.argv[1])['l']; dx,dy,dz=[float(x) for x in sys.argv[2:5]]
x,y,z=d['x']+dx,d['y']+dy,d['z']+dz
yaw=math.degrees(math.atan2(-dy,-dx)); pit=math.degrees(math.atan2(-dz,math.hypot(dx,dy)))
print(round(x,1),round(y,1),round(z,1),round(pit,1),round(yaw,1))" "$J" $DX $DY $DZ)
  p=$(cd $D && ./cap.sh $c | sed 's/IMAGE: //' | tr -d '\r')
  args+=("$f=$p")
done
/c/Users/User/AppData/Local/Programs/Python/Python312/python.exe $D/s/anim2/sheet.py "$out" "${args[@]}"
