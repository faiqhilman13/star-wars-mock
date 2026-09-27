#!/bin/bash
# sheet.sh out.png view absframe1 absframe2 ...
D=/c/Users/User/PROJECTS/jedi-arena/tools
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
out=$1; view=$2; shift 2; args=()
for f in "$@"; do
  cat $D/s/anim2/lib2.py > $D/s/anim2/_s.py
  printf 'def run():\n    guard(); show(%s); w=getw("hand_r_ik_ctrl",%s); show(%s); return {"h":w["location"]}\n' $f $f $f >> $D/s/anim2/_s.py
  (cd $D && "$PY" ue.py script s/anim2/_s.py >/dev/null)
  sleep 0.5
  case "$view" in
   back) c="-760 400 270 -18 180";;
   close) c="-800 440 230 -15 190";;
   side2) c="-1000 180 170 -5 90";;
   sidew) c="-1000 60 200 -8 90";;
   backhi) c="-640 400 380 -30 180";;
   back3) c="-760 560 300 -22 214";;
   side) c="-1000 110 190 -5 90";;
   lside) c="-1000 690 190 -5 -90";;
   front) c="-1320 400 210 -5 0";;
   front3) c="-1260 230 250 -12 33";;
   top) c="-1000 400 650 -89 180";;
  esac
  p=$(cd $D && ./cap.sh $c | sed 's/IMAGE: //' | tr -d '\r')
  args+=("$f=$p")
done
/c/Users/User/AppData/Local/Programs/Python/Python312/python.exe $D/s/anim2/sheet.py "$out" "${args[@]}"
