"""Lightsaber impacts built from the blade's own hum, the way the film hits/clashes read: the hum
flares (sudden surge, pitch spike that drops back), distorts into an electric buzz, and throws off
crackling sparks that fade into a sizzle. Source: pixabay_saber_hum (see audio/licensed/sources.txt)."""
import math, random, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_licensed import SR, save, norm, mix, fade, cut, load, dc_block

def glide(s, dur, r_start, r_end, glide_t):
    """Read s with the playback rate gliding r_start -> r_end over glide_t, then holding."""
    out = []; t = 0.0
    for k in range(int(dur * SR)):
        u = min(1.0, k / (glide_t * SR))
        r = r_start + (r_end - r_start) * (1 - (1 - u) ** 2)
        i = int(t)
        if i + 1 >= len(s): break
        f = t - i; out.append(s[i] * (1 - f) + s[i + 1] * f); t += r
    return out

def env(n, attack, tau, hold=0.0):
    a = int(attack * SR); h = int(hold * SR)
    return [(k / a if k < a else 1.0 if k < a + h else math.exp(-(k - a - h) / (tau * SR))) for k in range(n)]

def crackle(dur, density, tau, seed, bright=0.85):
    """Sparks: sparse random clicks (short high-passed noise bursts) whose rate decays over time."""
    rnd = random.Random(seed); n = int(dur * SR); out = [0.0] * n
    k = 0
    while k < n:
        rate = density * math.exp(-k / (tau * SR)) + 8.0
        k += int(rnd.expovariate(rate) * SR) + 1
        if k >= n: break
        amp = (0.4 + 0.6 * rnd.random()) * math.exp(-k / (tau * 1.6 * SR))
        blen = int((0.0006 + 0.0022 * rnd.random()) * SR)
        for j in range(blen):
            if k + j < n: out[k + j] += amp * (rnd.random() * 2 - 1) * (1 - j / blen)
    # one-pole high-pass so the sparks are crisp, not thuddy
    y = 0.0; px = 0.0; hp = []
    for x in out:
        y = bright * (y + x - px); px = x; hp.append(y)
    return hp

def buzz(s, drive):
    return [math.tanh(x * drive) for x in s]

def flutter(s, seed, depth=0.35):
    """Irregular electric amplitude flutter (~40-90 Hz)."""
    rnd = random.Random(seed); out = []; ph = 0.0; f = 60.0
    for k, x in enumerate(s):
        if k % 441 == 0: f = 40 + 50 * rnd.random()
        ph += 2 * math.pi * f / SR
        out.append(x * (1 - depth + depth * (0.5 + 0.5 * math.sin(ph))))
    return out

def impact(hum, start, dur, r0, r1, glide_t, drive, tau, spark_density, spark_tau, seed, tail_hiss=None):
    src = cut(hum, start, start + dur * 2)
    surge = buzz(norm(glide(src, dur, r0, r1, glide_t), -3.0), drive)
    surge = flutter(surge, seed)
    e = env(len(surge), 0.002, tau, hold=0.03)
    surge = [x * g for x, g in zip(surge, e)]
    sparks = norm(crackle(dur, spark_density, spark_tau, seed + 11), -1.0)
    rnd = random.Random(seed + 23)
    burst = [(rnd.random() * 2 - 1) * math.exp(-k / (0.006 * SR)) for k in range(int(0.03 * SR))]
    y = 0.0; px = 0.0; crack = []
    for x in burst:
        y = 0.9 * (y + x - px); px = x; crack.append(y)
    crack = norm(crack, -1.0)
    rms = lambda a, n: math.sqrt(sum(v * v for v in a[:n]) / max(1, min(n, len(a))))
    n = int(0.1 * SR)
    print("  attack RMS  surge %.3f  sparks %.3f  crack %.3f" % (rms(surge, n), rms(sparks, n) * 0.7, rms(crack, n) * 0.8))
    layers = [(surge, 1.0, 0.0), (sparks, 1.0, 0.0), (crack, 0.8, 0.0)]
    if tail_hiss:
        layers.append(tail_hiss)
    return norm(fade(mix(*layers), 0.0005, 0.06), -1.0)

if __name__ == "__main__":
    hum = dc_block(load("pixabay_saber_hum"))
    # Blade into a body: a short, hot flare and burn sizzle.
    save("SW_Saber_HitBody_V2", impact(hum, 12.5, 0.42, 1.8, 0.9, 0.10, 4.5, 0.13, 1400.0, 0.10, 3))
    # Blade on blade: brighter, harder flare, more sparks, longer crackling tail.
    save("SW_Saber_Clash_V2", impact(hum, 47.3, 0.75, 2.2, 1.0, 0.09, 7.0, 0.22, 2600.0, 0.20, 5))
