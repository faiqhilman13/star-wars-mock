#!/bin/bash
# run.sh file.py [more.py...]   (paths relative to s/anim2)
D=/c/Users/User/PROJECTS/jedi-arena/tools
files=("$D/s/anim2/lib2.py")
for f in "$@"; do files+=("$D/s/anim2/$f"); done
cat "${files[@]}" > $D/s/anim2/_r.py
cd $D
timeout ${TMO:-590} "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" ue.py script s/anim2/_r.py; echo rc=$?
