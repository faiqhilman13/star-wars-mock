"""Jet Ghost sounds, all original synthesis (no third-party audio):
  SW_Jetpack_Loop      seamless 2 s jetpack roar (rumble + turbulent flame roar + hiss + combustion crackle)
  SW_Rocket_Launch_1-3 shoulder-rocket launch: ignition thunk, crackle, a whoosh that tears away, sizzle tail
Output: audio/wav_jet/. death_sounds.py reuses jetpack() for the Jet Ghost's sputtering death."""
import math, os, random, sys, wave, array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_licensed import SR, norm, mix, fade, loop_xfade
from synth_hit import crackle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wav_jet")


def save(name, s):
    os.makedirs(OUT, exist_ok=True)
    w = wave.open(os.path.join(OUT, name + ".wav"), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(array.array('h', (max(-32767, min(32767, int(x * 32767))) for x in s)).tobytes())
    w.close()
    print(f"{name:24s} {len(s) / SR:5.2f}s")


class Biquad:
    """RBJ cookbook biquad; kind = lp | hp | bp. Coefficients can be retuned per block for sweeps."""
    def __init__(self, kind, f, q=0.707):
        self.kind = kind; self.x1 = self.x2 = self.y1 = self.y2 = 0.0; self.tune(f, q)

    def tune(self, f, q=0.707):
        w = 2 * math.pi * max(20.0, min(f, SR * 0.45)) / SR
        a = math.sin(w) / (2 * q); c = math.cos(w)
        if self.kind == "lp": b0, b1, b2 = (1 - c) / 2, 1 - c, (1 - c) / 2
        elif self.kind == "hp": b0, b1, b2 = (1 + c) / 2, -(1 + c), (1 + c) / 2
        else: b0, b1, b2 = a, 0.0, -a
        a0 = 1 + a
        self.b = (b0 / a0, b1 / a0, b2 / a0); self.a = (-2 * c / a0, (1 - a) / a0)

    def __call__(self, x):
        b0, b1, b2 = self.b; a1, a2 = self.a
        y = b0 * x + b1 * self.x1 + b2 * self.x2 - a1 * self.y1 - a2 * self.y2
        self.x2, self.x1, self.y2, self.y1 = self.x1, x, self.y1, y
        return y


def smooth_noise(n, rate_hz, rnd):
    """Slowly wandering random control signal in [-1, 1] (cosine-interpolated random points)."""
    step = max(1, int(SR / rate_hz)); pts = [rnd.uniform(-1, 1) for _ in range(n // step + 3)]
    out = []
    for k in range(n):
        i, f = divmod(k, step); f /= step; f = (1 - math.cos(math.pi * f)) / 2
        out.append(pts[i] * (1 - f) + pts[i + 1] * f)
    return out


def jetpack(dur, seed=1, throttle=1.0):
    """Jetpack roar: brown-noise rumble, turbulent band-passed flame roar, top hiss and combustion crackle."""
    rnd = random.Random(seed); n = int(dur * SR)
    lp_rumble = Biquad("lp", 380.0); bp_roar = Biquad("bp", 1100.0, 0.8); bp_roar2 = Biquad("bp", 2300.0, 1.2)
    hp_hiss = Biquad("hp", 5200.0)
    turb = smooth_noise(n, 14.0, rnd); turb2 = smooth_noise(n, 5.0, rnd)
    brown = 0.0; out = []
    for k in range(n):
        w = rnd.uniform(-1, 1)
        brown = 0.985 * brown + 0.15 * w
        pulse = 0.78 + 0.22 * math.sin(2 * math.pi * 23.0 * k / SR + 1.5 * turb2[k])   # combustion pulsing
        rumble = lp_rumble(brown) * 1.6
        roar = bp_roar(w) * (0.75 + 0.35 * turb[k]) * pulse * 2.2
        roar2 = bp_roar2(w) * (0.6 + 0.4 * turb2[k]) * 1.1
        hiss = hp_hiss(w) * 0.25
        out.append(throttle * (rumble + roar + roar2) + hiss * (0.5 + 0.5 * throttle))
    cr = crackle(dur, 90.0, 99.0, seed + 11, 0.8)
    return mix((out, 1.0, 0.0), (cr, 0.22, 0.0))


def rocket(seed, sweep_from, sweep_to, dur=1.0):
    rnd = random.Random(seed); n = int(dur * SR)
    # ignition thunk: a dropping low sine with a noise transient
    thunk, ph = [], 0.0
    for k in range(int(0.16 * SR)):
        u = k / (0.16 * SR); ph += 2 * math.pi * (120.0 - 65.0 * u) / SR
        thunk.append((math.sin(ph) + 0.6 * rnd.uniform(-1, 1) * math.exp(-k / (0.006 * SR))) * math.exp(-u * 5))
    # whoosh tearing away: band-pass noise swept down (Doppler), fast attack, long fade
    bp = Biquad("bp", sweep_from, 1.4); lp = Biquad("lp", 6000.0); whoosh = []
    for k in range(n):
        u = k / n
        if k % 64 == 0:
            bp.tune(sweep_from * (sweep_to / sweep_from) ** (u ** 0.7), 1.4)
        e = min(1.0, k / (0.025 * SR)) * math.exp(-u * 3.2)
        whoosh.append(lp(bp(rnd.uniform(-1, 1))) * e * 3.0)
    roar = jetpack(0.5, seed + 5, 1.2)
    roar = [x * math.exp(-k / (0.12 * SR)) for k, x in enumerate(roar)]
    sizzle = crackle(dur, 700.0, 0.18, seed + 3, 0.9)
    return fade(mix((thunk, 0.9, 0.0), (roar, 0.55, 0.0), (whoosh, 1.0, 0.01), (sizzle, 0.35, 0.02)), 0.001, 0.12)


if __name__ == "__main__":
    loop = jetpack(2.5, 3)
    save("SW_Jetpack_Loop", norm(loop_xfade(loop, 0.5), -3.0))
    for i, (a, b) in enumerate([(3200.0, 520.0), (2700.0, 430.0), (3800.0, 650.0)], 1):
        save(f"SW_Rocket_Launch_{i}", norm(rocket(40 + i, a, b), -1.0))
