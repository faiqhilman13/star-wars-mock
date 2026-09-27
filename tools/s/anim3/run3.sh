#!/bin/bash
# run3.sh file.py [more.py...]   (paths relative to s/anim3); prepends lib3+eng3+clips3
D=/c/Users/User/PROJECTS/jedi-arena/tools
files=("$D/s/anim3/lib3.py" "$D/s/anim3/eng3.py" "$D/s/anim3/clips3.py")
for f in "$@"; do files+=("$D/s/anim3/$f"); done
cat "${files[@]}" > $D/s/anim3/_r.py
cd $D
timeout ${TMO:-590} "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" ue.py script s/anim3/_r.py; echo rc=$?
