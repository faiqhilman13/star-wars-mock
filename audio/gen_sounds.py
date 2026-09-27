"""Procedurally synthesizes the saber / Force / blaster sound set as 16-bit mono WAVs.

Run with any Python 3 (no dependencies):  python gen_sounds.py
"""
import math
import os
import random
import struct
import wave

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wav")
random.seed(7)


def write(name, samples, peak=0.9):
    m = max(1e-9, max(abs(s) for s in samples))
    k = peak / m
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * k)) * 32767)) for s in samples))
    print("wrote", name, round(len(samples) / SR, 2), "s")


def lowpass(x, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / SR)
    y, out = 0.0, []
    for s in x:
        y += a * (s - y)
        out.append(y)
    return out


def highpass(x, cutoff):
    lp = lowpass(x, cutoff)
    return [a - b for a, b in zip(x, lp)]


def noise(n):
    return [random.uniform(-1, 1) for _ in range(n)]


def hum_osc(n, pitch_fn=lambda t: 1.0, base=88.0):
    """Saber tone: two detuned buzzy oscillators + faint high whine. pitch_fn(t) scales frequency."""
    out = []
    p1 = p2 = p3 = 0.0
    for i in range(n):
        t = i / SR
        f = pitch_fn(t)
        p1 += 2 * math.pi * base * f / SR
        p2 += 2 * math.pi * (base * 1.028) * f / SR
        p3 += 2 * math.pi * (base * 4.02) * f / SR
        s = 0.0
        for k in range(1, 9):
            s += math.sin(p1 * k) / k
            s += 0.6 * math.sin(p2 * k) / k
        s += 0.12 * math.sin(p3)
        out.append(s)
    return out


def env_adsr(n, a, d, s_level, r):
    out = []
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    for i in range(n):
        if i < A:
            e = i / max(1, A)
        elif i < A + D:
            e = 1 - (1 - s_level) * (i - A) / max(1, D)
        elif i > n - R:
            e = s_level * max(0.0, (n - i) / max(1, R))
        else:
            e = s_level
        out.append(e)
    return out


def crackle(n, density=0.004, decay=0.0015):
    """Sparse electric crackle impulses."""
    out = [0.0] * n
    i = 0
    while i < n:
        if random.random() < density:
            amp = random.uniform(0.3, 1.0) * random.choice((-1, 1))
            L = int(decay * SR * random.uniform(0.5, 2.0))
            for j in range(L):
                if i + j < n:
                    out[i + j] += amp * math.exp(-j / (L / 4 + 1)) * random.uniform(-1, 1)
            i += L
        i += 1
    return out


def mix(*tracks):
    n = max(len(t) for t, _ in tracks)
    out = [0.0] * n
    for t, g in tracks:
        for i, s in enumerate(t):
            out[i] += s * g
    return out


# --- saber hum (2.0 s, seamless loop: all periodic components complete whole cycles) ---
def saber_hum():
    n = SR * 2
    tone = hum_osc(n)
    am = [1 + 0.08 * math.sin(2 * math.pi * 6 * i / SR) for i in range(n)]
    hiss = lowpass(noise(n), 3000)
    # crossfade the hiss loop seam
    return [tone[i] * am[i] + 0.04 * hiss[i] for i in range(n)]


def saber_ignite():
    n = int(SR * 0.9)
    tone = hum_osc(n, lambda t: 0.35 + 0.65 * min(1, t / 0.22) + 0.25 * math.exp(-((t - 0.2) / 0.06) ** 2))
    env = env_adsr(n, 0.01, 0.35, 0.55, 0.3)
    snap = [v * math.exp(-i / (SR * 0.05)) for i, v in enumerate(highpass(noise(n), 1500))]
    return mix(([a * b for a, b in zip(tone, env)], 1.0), (snap, 0.6), (crackle(n, 0.002), 0.25))


def saber_retract():
    n = int(SR * 0.7)
    tone = hum_osc(n, lambda t: max(0.25, 1.0 - 0.75 * t / 0.45))
    env = [max(0.0, 1 - i / n) ** 1.5 for i in range(n)]
    return mix(([a * b for a, b in zip(tone, env)], 1.0), (crackle(n, 0.0015), 0.2))


def saber_swing(variant):
    dur = [0.42, 0.38, 0.55][variant]
    peak = [1.55, 1.7, 1.45][variant]
    n = int(SR * dur)
    mid = dur * [0.45, 0.4, 0.5][variant]
    pitch = lambda t: 1.0 + (peak - 1.0) * math.exp(-((t - mid) / (dur * 0.22)) ** 2)
    tone = hum_osc(n, pitch)
    env = [0.35 + 0.65 * math.exp(-((i / SR - mid) / (dur * 0.25)) ** 2) for i in range(n)]
    whoosh = lowpass(noise(n), 1800)
    wenv = [math.exp(-((i / SR - mid) / (dur * 0.18)) ** 2) for i in range(n)]
    fade = [min(1, i / (SR * 0.02), (n - i) / (SR * 0.05)) for i in range(n)]
    return [(tone[i] * env[i] + 0.8 * whoosh[i] * wenv[i]) * fade[i] for i in range(n)]


def saber_hit():
    n = int(SR * 0.55)
    burst = [v * math.exp(-i / (SR * 0.08)) for i, v in enumerate(highpass(noise(n), 900))]
    sizzle = [v * math.exp(-i / (SR * 0.25)) for i, v in enumerate(crackle(n, 0.02, 0.001))]
    thump = [math.sin(2 * math.pi * 70 * i / SR) * math.exp(-i / (SR * 0.06)) for i in range(n)]
    tone = hum_osc(n, lambda t: 1.4 - 0.4 * min(1, t / 0.2))
    tenv = [math.exp(-i / (SR * 0.15)) for i in range(n)]
    return mix((burst, 0.7), (sizzle, 0.8), (thump, 0.6), ([a * b for a, b in zip(tone, tenv)], 0.5))


def saber_clash():
    n = int(SR * 0.65)
    partials = [(1180, 1.0), (1873, 0.7), (2610, 0.5), (3405, 0.35), (620, 0.6)]
    ring = [sum(g * math.sin(2 * math.pi * f * i / SR) for f, g in partials) * math.exp(-i / (SR * 0.09)) for i in range(n)]
    zap = [v * math.exp(-i / (SR * 0.2)) for i, v in enumerate(crackle(n, 0.03, 0.0012))]
    burst = [v * math.exp(-i / (SR * 0.03)) for i, v in enumerate(noise(n))]
    return mix((ring, 0.5), (zap, 1.0), (burst, 0.6))


def blaster_fire():
    n = int(SR * 0.32)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = 300 + 1700 * math.exp(-t / 0.06)
        ph += 2 * math.pi * f / SR
        s = math.sin(ph) + 0.3 * math.sin(ph * 2.01) + 0.15 * math.sin(ph * 0.5)
        out.append(s * math.exp(-t / 0.1) * min(1, i / 40))
    return mix((out, 1.0), ([v * math.exp(-i / (SR * 0.02)) for i, v in enumerate(noise(n))], 0.25))


def blaster_deflect():
    n = int(SR * 0.35)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = 500 * math.exp(t / 0.12)
        ph += 2 * math.pi * min(f, 4000) / SR
        out.append(math.sin(ph) * math.exp(-t / 0.09))
    return mix((out, 0.7), (saber_clash()[:n], 0.6), (crackle(n, 0.03, 0.001), 0.5))


def force_push():
    n = int(SR * 0.9)
    whump = [math.sin(2 * math.pi * (55 - 20 * i / n) * i / SR) * math.exp(-i / (SR * 0.25)) for i in range(n)]
    air = lowpass(noise(n), 700)
    aenv = [math.exp(-((i / SR - 0.12) / 0.12) ** 2) + 0.4 * math.exp(-i / (SR * 0.4)) for i in range(n)]
    return mix((whump, 1.0), ([a * b for a, b in zip(air, aenv)], 1.4))


def lightning_loop():
    n = SR  # 1 s loop
    c = crackle(n, 0.03, 0.0015)
    buzz = [math.sin(2 * math.pi * 120 * i / SR) * (0.5 + 0.5 * math.sin(2 * math.pi * 30 * i / SR)) for i in range(n)]
    hiss = highpass(noise(n), 2500)
    return mix((c, 1.0), (buzz, 0.15), (hiss, 0.15))


def remote_hum():
    n = SR  # 1 s loop, whole cycles
    return [0.6 * math.sin(2 * math.pi * 220 * i / SR) + 0.3 * math.sin(2 * math.pi * 330 * i / SR) * (0.7 + 0.3 * math.sin(2 * math.pi * 4 * i / SR)) for i in range(n)]


def explosion():
    n = int(SR * 1.0)
    rumble = [v * math.exp(-i / (SR * 0.3)) for i, v in enumerate(lowpass(noise(n), 400))]
    crack = [v * math.exp(-i / (SR * 0.05)) for i, v in enumerate(noise(n))]
    return mix((rumble, 1.6), (crack, 0.5), (crackle(n, 0.01), 0.3))


if __name__ == "__main__":
    write("SW_Saber_Hum_Loop", saber_hum(), 0.6)
    write("SW_Saber_Ignite", saber_ignite())
    write("SW_Saber_Retract", saber_retract())
    for v in range(3):
        write("SW_Saber_Swing%d" % (v + 1), saber_swing(v))
    write("SW_Saber_Hit", saber_hit())
    write("SW_Saber_Clash", saber_clash())
    write("SW_Blaster_Fire", blaster_fire())
    write("SW_Blaster_Deflect", blaster_deflect())
    write("SW_Force_Push", force_push())
    write("SW_Force_Lightning_Loop", lightning_loop(), 0.7)
    write("SW_Remote_Hum_Loop", remote_hum(), 0.4)
    write("SW_Remote_Explode", explosion())
