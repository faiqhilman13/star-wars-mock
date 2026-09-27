import wave, array, math, sys, glob, os
def load(p):
    w = wave.open(p); n = w.getnframes(); a = array.array('h', w.readframes(n)); w.close(); return a
W = 2205  # 50 ms
for p in sorted(glob.glob(sys.argv[1])):
    a = load(p)
    rms, zcr = [], []
    for i in range(0, len(a) - W, W):
        s = a[i:i+W]
        e = math.sqrt(sum(x*x for x in s) / W) + 1e-9
        rms.append(20*math.log10(e/32768))
        z = sum(1 for k in range(1, W) if (s[k-1] < 0) != (s[k] < 0))
        zcr.append(z * 20 / 2)  # approx Hz
    chars = " .:-=+*#%@"
    line = "".join(chars[max(0, min(9, int((r + 50) / 5)))] for r in rms)
    print(f"{os.path.basename(p):34s} {len(a)/44100:5.2f}s |{line}|")
    zl = "".join("0123456789"[min(9, int(z/800))] for z in zcr)
    print(f"{'  zcr/800Hz':34s}        |{zl}|")
