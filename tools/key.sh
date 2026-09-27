#!/bin/bash
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
"$PY" "$(dirname "$0")/ue.py" call call_tool "{\"toolset_name\":\"SlateInspectorToolset.SlateInspectorToolset\",\"tool_name\":\"PressKey\",\"arguments\":{\"key\":\"$1\"}}" >/dev/null
