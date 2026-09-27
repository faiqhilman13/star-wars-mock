#!/bin/bash
# cmd.sh "console command"  -> types into the editor console box (works during PIE); finds the box's ref automatically
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
D="$(dirname "$0")"
REF=$(UE_FULL=1 "$PY" "$D/ue.py" call call_tool '{"toolset_name":"SlateInspectorToolset.SlateInspectorToolset","tool_name":"Snapshot","arguments":{"ref":"","maxDepth":60,"bIncludeSourceLocations":false}}' | grep -o 'Cmd.\{200\}' | grep -o 'textbox[^]]*\] \[ref=[a-z0-9]*\]' | grep -o 'ref=[a-z0-9]*' | cut -d= -f2)
"$PY" "$D/ue.py" call call_tool "{\"toolset_name\":\"SlateInspectorToolset.SlateInspectorToolset\",\"tool_name\":\"Type\",\"arguments\":{\"ref\":\"${REF:-tb1}\",\"text\":\"$1\",\"submit\":true}}"
