"""Cuts real recorded lightsaber clashes out of the Montogoronto energy-weapon pack (Pixabay Content
License, see audio/licensed/sources.txt). Clashes keep their full crackling tail; body hits are the
same impacts cut short and slightly lower for a heavier, burnt-in feel."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_licensed import SR, save, norm, fade, cut, load, rate

pack = load("pixabay_montogoronto_energy_weapon_pack")
CLASHES = [14.33, 15.85, 17.90, 36.46]      # sharp broadband crack + hum flare + crackle tail
HITS = [16.78, 27.62, 31.59]
for i, t in enumerate(CLASHES, 1):
    save("SW_Saber_Clash_Rec%d" % i, norm(fade(cut(pack, t - 0.004, t + 0.70), 0.001, 0.28), -1.0))
for i, t in enumerate(HITS, 1):
    save("SW_Saber_Hit_Rec%d" % i, norm(fade(rate(cut(pack, t - 0.004, t + 0.40), 0.93), 0.001, 0.16), -1.0))
