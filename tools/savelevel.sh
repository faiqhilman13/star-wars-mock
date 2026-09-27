#!/bin/bash
# savelevel.sh -> clicks the level editor's "Save Current Level" button (saves World Partition actor files + deletions)
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
D="$(dirname "$0")"
SNAP=$(UE_FULL=1 "$PY" "$D/ue.py" call call_tool '{"toolset_name":"SlateInspectorToolset.SlateInspectorToolset","tool_name":"Snapshot","arguments":{"ref":"","maxDepth":60,"bIncludeSourceLocations":false}}')
REF=$(printf '%s' "$SNAP" | grep -o 'Save Current Level[^[]*\[pos[^]]*\] \[ref=[a-z0-9]*\]' | head -1 | grep -o 'ref=[a-z0-9]*' | cut -d= -f2)
echo "save button ref: ${REF:-none}"
if [ -n "$REF" ]; then
  "$PY" "$D/ue.py" call call_tool "{\"toolset_name\":\"SlateInspectorToolset.SlateInspectorToolset\",\"tool_name\":\"Click\",\"arguments\":{\"ref\":\"$REF\"}}"
fi
