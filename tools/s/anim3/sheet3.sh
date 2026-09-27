#!/bin/bash
# sheet3.sh out.png view absframe1 absframe2 ...
D=/c/Users/User/PROJECTS/jedi-arena/tools
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
out=$1; view=$2; shift 2; args=()
cat $D/s/anim3/lib3.py $D/s/anim3/hidebb.py > $D/s/anim3/_h.py; (cd $D && "$PY" ue.py script s/anim3/_h.py >/dev/null 2>&1)
for f in "$@"; do
  cat $D/s/anim3/lib3.py > $D/s/anim3/_s.py
  printf 'def run():\n    guard(); show(%s); w=getw("hand_r_ik_ctrl",%s); show(%s); return {"h":w["location"]}\n' $f $f $f >> $D/s/anim3/_s.py
  (cd $D && "$PY" ue.py script s/anim3/_s.py >/dev/null)
  case "$view" in
   back) c="-640 400 250 -8 180";;
   back3) c="-700 200 270 -12 146";;
   side) c="-1000 40 190 0 90";;
   lside) c="-1000 760 190 0 -90";;
   front) c="-1360 400 200 -2 0";;
   front3) c="-1300 200 230 -6 34";;
   top) c="-1000 400 700 -89 180";;
   *) c="$view";;
  esac
  p=$(cd $D && ./cap.sh $c | sed 's/IMAGE: //' | tr -d '\r')
  args+=("$f=$p")
done
/c/Users/User/AppData/Local/Programs/Python/Python312/python.exe $D/s/anim2/sheet.py "$out" "${args[@]}"
