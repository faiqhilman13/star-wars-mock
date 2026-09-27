"""Builds the game's SW_* sounds from the free-licensed clips in audio/work (mono 44.1 kHz s16).
Sources and licences: audio/licensed/sources.txt. Output: audio/wav_licensed/."""
import wave, array, math, os

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
OUT = os.path.join(HERE, "..", "wav_licensed")

def load(name):
    w = wave.open(os.path.join(WORK, name + ".wav"))
    a = array.array('h', w.readframes(w.getnframes())); w.close()
    return [x / 32768.0 for x in a]

def save(name, s):
    os.makedirs(OUT, exist_ok=True)
    w = wave.open(os.path.join(OUT, name + ".wav"), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(array.array('h', (max(-32767, min(32767, int(x * 32767))) for x in s)).tobytes()); w.close()
    print(f"{name:26s} {len(s)/SR:5.2f}s")

def cut(s, t0, t1=None):
    return s[int(t0 * SR): None if t1 is None else int(t1 * SR)]

def fade(s, fin=0.005, fout=0.02):
    s = list(s); n = len(s); a = int(fin * SR); b = int(fout * SR)
    for i in range(min(a, n)): s[i] *= i / a
    for i in range(min(b, n)): s[n - 1 - i] *= i / b
    return s

def norm(s, peak_db=-1.0):
    p = max(abs(x) for x in s) or 1.0
    g = 10 ** (peak_db / 20) / p
    return [x * g for x in s]

def rate(s, r):
    """Plays s back r times faster (pitch and speed), linear interpolation."""
    out = []; t = 0.0; n = len(s) - 1
    while t < n:
        i = int(t); f = t - i
        out.append(s[i] * (1 - f) + s[i + 1] * f); t += r
    return out

def trim_lead(s, thresh=0.02):
    for i, x in enumerate(s):
        if abs(x) > thresh: return s[max(0, i - 200):]
    return s

def sweep_down(s, dur, r0=1.0, r1=0.45):
    """Plays s with the rate gliding r0 -> r1 over dur seconds and a decaying level (power-down whine)."""
    out = []; t = 0.0; n = int(dur * SR)
    for k in range(n):
        u = k / n; i = int(t)
        if i + 1 >= len(s): break
        f = t - i; out.append((s[i] * (1 - f) + s[i + 1] * f) * (1 - u) ** 2)
        t += r0 + (r1 - r0) * u
    return out

def mix(*layers):
    """layers: (samples, gain, offset_seconds)"""
    n = max(len(s) + int(o * SR) for s, g, o in layers)
    out = [0.0] * n
    for s, g, o in layers:
        o = int(o * SR)
        for i, x in enumerate(s): out[o + i] += x * g
    return out

def dc_block(s, r=0.995):
    out = []; px = py = 0.0
    for x in s:
        y = x - px + r * py; out.append(y); px, py = x, y
    return out

def loop_xfade(s, xf):
    """Seamless loop: the head is equal-power crossfaded with the material just past the loop end."""
    x = int(xf * SR); L = len(s) - x
    out = s[:L]
    for i in range(x):
        t = i / x
        out[i] = s[i] * math.sin(t * math.pi / 2) + s[L + i] * math.cos(t * math.pi / 2)
    return out

if __name__ == "__main__":
    hum = dc_block(load("pixabay_saber_hum"))
    ignite = load("mixkit_lightsaber_turn_on")
    swoosh = load("mixkit_lightsaber_swoosh")
    hiss = load("mixkit_lightsaber_hiss")
    ls3 = load("pixabay_lightsaber3")
    ls4 = load("pixabay_lightsaber4")
    clash = load("pixabay_lightsaber_clash")
    blstr = load("pixabay_blstr_1")
    boom = load("pixabay_blaster_2")

    save("SW_Saber_Hum_Loop", norm(loop_xfade(cut(hum, 47.3, 47.3 + 3.5 + 0.4), 0.4), -3.0))
    ign = cut(ignite, 0.0, 1.2)
    save("SW_Saber_Ignite", norm(fade(ign, 0.002, 0.15)))
    rev = fade(rate(trim_lead(ign[::-1]), 1.15), 0.08, 0.04)
    save("SW_Saber_Retract", norm(mix((rev, 0.8, 0), (sweep_down(cut(hum, 47.3, 49.0), 0.5), 0.9, len(rev) / SR - 0.06)), -2.0))

    sw1 = cut(ls3, 0.08, 1.40); sw2 = cut(ls4, 0.20, 0.95); sw3 = cut(swoosh, 0.05, 1.42)
    save("SW_Saber_Swing1", norm(fade(sw1, 0.01, 0.25)))
    save("SW_Saber_Swing2", norm(fade(sw2, 0.01, 0.20)))
    save("SW_Saber_Swing3", norm(fade(sw3, 0.01, 0.30)))
    save("SW_Saber_Swing4", norm(fade(rate(sw1, 1.22), 0.01, 0.2)))   # quicker, brighter slash
    save("SW_Saber_Swing5", norm(fade(rate(sw3, 0.86), 0.01, 0.3)))   # heavier spin

    cl = cut(clash, 0.0, 1.1)
    save("SW_Saber_Clash", norm(fade(cl, 0.002, 0.35)))
    save("SW_Saber_Hit", norm(mix((fade(cut(clash, 0, 0.45), 0.002, 0.2), 1.0, 0), (fade(cut(hiss, 0, 0.62), 0.002, 0.25), 0.7, 0.01))))

    # blaster_2 is the classic descending "pew" sweep; its long drone tail is cut. blstr_1 adds a little noisy body.
    pew = fade(cut(boom, 0.0, 0.42), 0.001, 0.22)
    save("SW_Blaster_Fire", norm(mix((pew, 1.0, 0), (fade(cut(blstr, 0.0, 0.3), 0.002, 0.15), 0.25, 0))))
    save("SW_Blaster_Deflect", norm(mix((fade(cut(clash, 0, 0.35), 0.002, 0.18), 0.9, 0), (rate(pew, 1.35), 0.75, 0.015))))
    save("SW_Remote_Explode", norm(mix((fade(rate(cut(blstr, 0.0, 0.72), 0.7), 0.002, 0.3), 1.0, 0), (fade(rate(cut(boom, 0.0, 0.3), 0.6), 0.002, 0.25), 0.6, 0))))

    # Saber-on-body: sharp crack + burning sizzle + a low thump for weight. Short and front-loaded so it
    # cuts through the hum and swing whoosh on every connecting blow.
    def thump(dur=0.16, f0=110.0, f1=45.0):
        out = []; ph = 0.0; n = int(dur * SR)
        for k in range(n):
            u = k / n; f = f0 + (f1 - f0) * u; ph += 2 * math.pi * f / SR
            out.append(math.sin(ph) * math.exp(-u * 5.0))
        return out
    crack = fade(cut(clash, 0.0, 0.09), 0.0005, 0.05)
    sizzle = fade(cut(hiss, 0.0, 0.40), 0.002, 0.22)
    zap = fade(rate(cut(boom, 0.0, 0.12), 1.8), 0.0005, 0.04)  # tiny bright chirp on the attack
    save("SW_Saber_HitBody", norm(mix((crack, 1.0, 0), (sizzle, 0.9, 0.005), (thump(), 0.8, 0), (zap, 0.35, 0)), -0.3))
