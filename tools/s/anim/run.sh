#!/bin/bash
# run.sh file.py [timeout]
cd /c/Users/User/PROJECTS/jedi-arena/tools
cat s/anim/lib.py "$1" > s/anim/_r.py
timeout ${2:-110} "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" ue.py script s/anim/_r.py; echo rc=$?
