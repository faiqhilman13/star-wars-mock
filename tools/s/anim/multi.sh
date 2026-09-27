#!/bin/bash
# multi.sh out.png view f1 f2 ...
cd /c/Users/User/PROJECTS/jedi-arena/tools
out=$1; view=$2; shift 2; args=()
for f in "$@"; do p=$(s/anim/shot.sh $f $view | sed 's/IMAGE: //' | tr -d '\r'); args+=("$f=$p"); done
/c/Users/User/AppData/Local/Programs/Python/Python312/python.exe s/anim/sheet.py "$out" "${args[@]}"
