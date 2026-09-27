"""Physically-modelled 'guy-wire' blaster (the technique behind the classic film sound: a hammer
strike on a long tensioned wire). Bending waves in a stiff wire are dispersive: group velocity grows
with sqrt(f), so a listener at distance L hears arrival time t ~ L/sqrt(f), i.e. f(t) = (k/t)^2 --
the falling 'pew'. Echo paths up and down the wire arrive later and sweep slower, giving the
metallic chorus. A little saturation adds the grit of the old tape recordings.
Writes into audio/wav_licensed/ (original synthesis; no third-party audio except the clash layer)."""
import math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_licensed import SR, save, norm, mix, fade, cut, load, rate

def wire_chirp(t0, f_hi=9000.0, f_lo=240.0, paths=((1.0, 1.0), (1.45, 0.5), (2.1, 0.25)),
               tilt=0.3, seed=1):
    rnd = random.Random(seed)
    k = t0 * math.sqrt(f_hi)                       # f(t0) = f_hi on the direct path
    end = max(m for m, g in paths) * k / math.sqrt(f_lo)
    out = [0.0] * int(end * SR + SR * 0.02)
    for m, g in paths:
        ph = rnd.random() * 6.28
        start = int(m * t0 * SR); stop = int(m * k / math.sqrt(f_lo) * SR)
        for n in range(start, stop):
            t = n / SR
            f = (m * k / t) ** 2
            ph += 2 * math.pi * f / SR
            u = (n - start) / max(1, stop - start)
            amp = g * (f / f_hi) ** tilt * min(1.0, (n - start) / (0.0015 * SR)) * (1 - u) ** 1.5
            out[n] += amp * (math.sin(ph) + 0.18 * math.sin(2 * ph))
    return out

def tick(dur=0.004, seed=3):
    rnd = random.Random(seed); n = int(dur * SR)
    return [(rnd.random() * 2 - 1) * (1 - i / n) ** 2 for i in range(n)]

def saturate(s, drive=2.2):
    return [math.tanh(x * drive) for x in s]

def room(s, taps=((0.031, 0.22), (0.067, 0.12), (0.113, 0.06))):
    return mix((s, 1.0, 0), *[(s, g, d) for d, g in taps])

if __name__ == "__main__":
    pew = saturate(norm(mix((wire_chirp(0.030), 1.0, 0), (tick(), 0.35, 0.028)), -1.0))
    fire = norm(fade(room(pew), 0.0005, 0.06), -1.0)
    save("SW_Blaster_Fire", fire)
    # Deflect: bright saber crack + a quicker, higher ricochet pew.
    pack = load("pixabay_montogoronto_energy_weapon_pack")
    clash = cut(pack, 14.326, 14.9)   # recorded saber clash (see extract_clash.py)
    ric = saturate(norm(wire_chirp(0.018, f_hi=11000.0, f_lo=260.0, seed=7), -1.0), 1.8)
    save("SW_Blaster_Deflect", norm(fade(mix((fade(cut(clash, 0, 0.22), 0.0005, 0.1), 0.9, 0), (room(ric), 0.9, 0.01)), 0.0005, 0.05), -1.0))
