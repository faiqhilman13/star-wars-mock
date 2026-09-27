#!/bin/bash
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
cd /c/Users/User/PROJECTS/jedi-arena/tools
until "$PY" ue.py t app.IsPIERunning '{}' 2>/dev/null | grep -q false; do sleep 10; done
echo "PIE stopped $(date)"
