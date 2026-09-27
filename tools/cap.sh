#!/bin/bash
# cap.sh x y z pitch yaw  -> saves viewport capture
PY="/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe"
"$PY" "$(dirname "$0")/ue.py" t app.CaptureViewport "{\"captureTransform\":{\"location\":{\"x\":$1,\"y\":$2,\"z\":$3},\"rotation\":{\"pitch\":$4,\"yaw\":$5,\"roll\":0},\"scale\":{\"x\":1,\"y\":1,\"z\":1}},\"annotations\":{\"gridSpacing\":0,\"gridExtent\":0,\"gridHeight\":0,\"maxLabelDistance\":0,\"classFilter\":null,\"maxLabels\":0},\"bShowUI\":false}"
