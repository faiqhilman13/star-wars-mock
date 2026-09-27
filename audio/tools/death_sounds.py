"""Original enemy death sounds: Windows-TTS voice takes (tts_lines.ps1) run through ffmpeg character
filters, layered with synthesized mechanical/electrical effects. Output: audio/wav_deaths/SW_Death_*.wav"""
import math, os, random, subprocess, sys, wave, array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_licensed import SR, norm, mix, fade, cut, rate
from synth_hit import crackle

HERE = os.path.dirname(os.path.abspath(__file__))
TTS = os.path.join(HERE, "..", "work", "tts")
TMP = os.path.join(HERE, "..", "work", "tts_fx")
OUT = os.path.join(HERE, "..", "wav_deaths")
FF = r"C:\Users\User\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
os.makedirs(TMP, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
rnd = random.Random(7)

TRIM = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
CHAINS = {
    # nasal, sped-up, ring-modulated battle droid
    "droid": TRIM + ",asetrate=44100*1.25,aresample=44100,atempo=0.88,aeval=val(0)*(0.55+0.45*sin(2*PI*85*t)),"
                    "highpass=f=380,lowpass=f=4200,acrusher=bits=9:mix=0.3,flanger=delay=2:depth=2",
    # helmet comm radio
    "trooper": TRIM + ",asetrate=44100*0.94,aresample=44100,highpass=f=480,lowpass=f=2700,acrusher=bits=11:mix=0.25,"
                      "acompressor=threshold=0.1:ratio=6:attack=5:release=60",
    # panicked falling scream through the comm
    "jet": TRIM + ",vibrato=f=7:d=0.5,highpass=f=420,lowpass=f=3000,acompressor=threshold=0.1:ratio=5",
    # deep, distorted, echoing
    "warden": TRIM + ",asetrate=44100*0.8,aresample=44100,atempo=1.08,lowpass=f=3200,acrusher=bits=10:mix=0.2,aecho=0.7:0.5:45|90:0.35|0.2",
    # tiny panicked droid squeak
    "roller": TRIM + ",asetrate=44100*1.7,aresample=44100,aeval=val(0)*(0.5+0.5*sin(2*PI*210*t)),highpass=f=600",
}


def load_wav(path):
    w = wave.open(path)
    a = array.array('h', w.readframes(w.getnframes()))
    w.close()
    return [x / 32768.0 for x in a]


def save(name, s):
    w = wave.open(os.path.join(OUT, name + ".wav"), "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(array.array('h', (max(-32767, min(32767, int(x * 32767))) for x in s)).tobytes())
    w.close()
    print(f"{name:26s} {len(s) / SR:5.2f}s")


def voice(take, chain):
    src = os.path.join(TTS, take + ".wav")
    dst = os.path.join(TMP, take + "_" + chain + ".wav")
    subprocess.run([FF, "-v", "error", "-y", "-i", src, "-af", CHAINS[chain], "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", dst], check=True)
    return norm(load_wav(dst), -1.0)


# ---------------------------------------------------------------- synthesized layers
def whine_down(dur=0.7, f0=1100.0, f1=90.0, wobble=9.0):
    """Servo/power-cell winding down."""
    out, ph = [], 0.0
    n = int(dur * SR)
    for k in range(n):
        u = k / n
        f = f0 * (f1 / f0) ** u * (1 + 0.04 * math.sin(2 * math.pi * wobble * k / SR))
        ph += 2 * math.pi * f / SR
        s = math.sin(ph) + 0.35 * math.sin(2 * ph) + 0.2 * (1 if math.sin(3 * ph) > 0 else -1)
        out.append(0.45 * s * (1 - u) ** 1.3)
    return fade(out, 0.01, 0.05)


def clatter(dur=0.6, hits=4):
    """Metal limbs hitting the floor: a few inharmonic metallic pings."""
    out = [0.0] * int(dur * SR)
    t = 0.0
    for h in range(hits):
        freqs = [rnd.uniform(700, 1600), rnd.uniform(1900, 3400), rnd.uniform(3800, 6000)]
        amp = 0.6 * (0.7 ** h)
        start = int(t * SR)
        for k in range(int(0.22 * SR)):
            if start + k >= len(out):
                break
            e = math.exp(-k / (0.035 * SR))
            out[start + k] += amp * e * sum(math.sin(2 * math.pi * f * k / SR) / (i + 1) for i, f in enumerate(freqs))
        t += rnd.uniform(0.06, 0.16)
    return out


def thud(dur=0.25, f0=90.0, f1=45.0):
    out, ph = [], 0.0
    n = int(dur * SR)
    for k in range(n):
        u = k / n
        ph += 2 * math.pi * (f0 + (f1 - f0) * u) / SR
        out.append((math.sin(ph) + 0.3 * (rnd.random() * 2 - 1) * math.exp(-k / (0.01 * SR))) * math.exp(-u * 6))
    return out


def squelch(dur=0.09):
    """Radio click-off."""
    n = int(dur * SR)
    return [(rnd.random() * 2 - 1) * (0.5 if k < 0.012 * SR else 0.15 * (1 - k / n)) for k in range(n)]


def sputter(dur=0.9):
    """Jetpack coughing out: noise bursts that get sparser and duller."""
    out = [0.0] * int(dur * SR)
    t, lp = 0.0, 0.0
    while t < dur - 0.05:
        blen = int(rnd.uniform(0.03, 0.07) * SR)
        start = int(t * SR)
        amp = 0.8 * (1 - t / dur)
        for k in range(blen):
            if start + k >= len(out):
                break
            lp += 0.25 * ((rnd.random() * 2 - 1) - lp)
            out[start + k] += amp * lp * math.sin(math.pi * k / blen)
        t += rnd.uniform(0.05, 0.14) * (1 + 2 * t / dur)
    return out


def beeps(n=4, f0=2400.0, step=0.8):
    out = []
    f = f0
    for i in range(n):
        seg = int(0.07 * SR)
        out += [0.5 * (1 if math.sin(2 * math.pi * f * k / SR) > 0 else -1) * min(1, (seg - k) / 200) for k in range(seg)]
        out += [0.0] * int(0.025 * SR)
        f *= step
    return out


def pop(dur=0.35):
    lp, out = 0.0, []
    n = int(dur * SR)
    for k in range(n):
        lp += 0.35 * ((rnd.random() * 2 - 1) - lp)
        out.append(lp * math.exp(-k / (0.07 * SR)))
    return out


def at(s, t):
    return (s, 1.0, t)


# ---------------------------------------------------------------- assemble
for i in range(1, 8):
    v = voice(f"droid_{i}", "droid")
    vl = len(v) / SR
    layers = [at(v, 0.0), (whine_down(0.55 + rnd.random() * 0.3), 0.55, max(0.0, vl - 0.12)),
              (clatter(0.6, rnd.randint(3, 5)), 0.5, vl + 0.18), (crackle(0.3, 900.0, 0.08, 20 + i), 0.35, vl - 0.05)]
    save(f"SW_Death_Droid_{i}", norm(fade(mix(*layers), 0.002, 0.08), -1.0))

for i in range(1, 5):
    v = voice(f"trooper_{i}", "trooper")
    vl = len(v) / SR
    save(f"SW_Death_Trooper_{i}", norm(fade(mix(at(v, 0.04), (thud(), 0.6, 0.0), (squelch(), 0.5, vl + 0.06),
                                                  (clatter(0.35, 2), 0.25, vl + 0.1)), 0.002, 0.06), -1.0))

for i in range(1, 4):
    v = voice(f"jet_{i}", "jet")
    vl = len(v) / SR
    save(f"SW_Death_Jet_{i}", norm(fade(mix(at(v, 0.0), (sputter(vl + 0.4), 0.55, 0.05), (thud(0.3), 0.5, vl + 0.25),
                                              (squelch(), 0.4, vl + 0.1)), 0.002, 0.08), -1.0))

for i in range(1, 3):
    v = voice(f"warden_{i}", "warden")
    vl = len(v) / SR
    save(f"SW_Death_Warden_{i}", norm(fade(mix(at(v, 0.0), (crackle(0.8, 2200.0, 0.25, 40 + i), 0.6, 0.0),
                                                 (thud(0.35, 70.0, 35.0), 0.8, vl * 0.6), (clatter(0.5, 3), 0.3, vl * 0.6 + 0.1)), 0.002, 0.1), -1.0))

sq = voice("roller_1", "roller")
for i in range(1, 4):
    b = beeps(3 + i % 2, 2600.0 - i * 300.0, 0.78)
    bl = len(b) / SR
    save(f"SW_Death_Roller_{i}", norm(fade(mix(at(b, 0.0), (sq, 0.7, bl * 0.4), (pop(), 0.9, bl + 0.05),
                                                (clatter(0.5, 4), 0.45, bl + 0.12)), 0.002, 0.08), -1.0))
