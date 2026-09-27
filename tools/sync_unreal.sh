#!/bin/bash
# sync_unreal.sh -> mirrors the Unreal project's source, config and content into unreal/JediArena
# so they are versioned with the rest of this repo. Run it before committing.
# (Binaries, Intermediate, Saved and DerivedDataCache are build/cache output and are not copied.)
SRC="/c/Users/User/Documents/Unreal Projects/JediArena"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="$ROOT/unreal/JediArena"
case "$DST" in
  */jedi-arena/unreal/JediArena) ;;
  *) echo "refusing to mirror into unexpected path: $DST"; exit 1 ;;
esac
mkdir -p "$DST"
for d in Source Config Content ArtSource; do
  MSYS_NO_PATHCONV=1 robocopy "$(cygpath -w "$SRC/$d")" "$(cygpath -w "$DST/$d")" /MIR /NFL /NDL /NJH /NJS /NP > /dev/null
  rc=$?
  if [ $rc -ge 8 ]; then echo "robocopy failed for $d (exit $rc)"; exit 1; fi
done
cp "$SRC/JediArena.uproject" "$DST/"
echo "synced $SRC -> $DST"
