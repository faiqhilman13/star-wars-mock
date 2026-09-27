#!/bin/bash
# shot.sh frame view
cd /c/Users/User/PROJECTS/jedi-arena/tools
cat > s/anim/_show.py <<PYEOF
def run():
    show($1); return {"h":wpos("hand_r_ik_ctrl",$1)}
PYEOF
s/anim/run.sh s/anim/_show.py >/dev/null; sleep 1
case "$2" in
 back) ./cap.sh -730 400 290 -20 180;;
 back3) ./cap.sh -760 520 300 -22 207;;
 side) ./cap.sh -1000 130 210 -5 90;;
 lside) ./cap.sh -1000 670 210 -5 -90;;
 front) ./cap.sh -1300 400 220 -5 0;;
 front3) ./cap.sh -1260 250 260 -12 30;;
 top) ./cap.sh -1000 400 600 -89 180;;
esac
