"""Lists impact-like events: frames where high-frequency energy (first-difference proxy) jumps sharply."""
import wave, array, math, sys
p = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
w = wave.open(p); a = array.array('h', w.readframes(w.getnframes())); w.close()
SR = 44100; F = 441  # 10 ms
hf, lv = [], []
for i in range(0, len(a) - F, F):
    s = a[i:i + F]
    d = sum((s[k] - s[k - 1]) ** 2 for k in range(1, F)) / F
    e = sum(x * x for x in s) / F
    hf.append(10 * math.log10(d + 1)); lv.append(10 * math.log10(e + 1))
events = []; last = -100
for k in range(10, len(hf)):
    t = k * 0.01
    if t < t0 or t > t1: continue
    base = min(hf[k - 10:k])
    if hf[k] - base > 14 and k - last > 15 and hf[k] >= max(hf[k:k + 3]) - 1:
        # event length: until level falls 25 dB below its peak (max 1.2 s)
        pk = max(lv[k:k + 10]); j = k
        while j < len(lv) - 1 and j - k < 120 and lv[j] > pk - 25: j += 1
        events.append((t, (j - k) * 0.01, hf[k] - base, pk - 90.3)); last = k
for t, L, rise, pk in events:
    print(f"  onset {t:6.2f}s  len {L:4.2f}s  hf-rise {rise:4.1f} dB  peak {pk:5.1f} dBFS")
print(f"  {len(events)} events")
