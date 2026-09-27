import wave, array, math
w = wave.open("pixabay_saber_hum.wav"); a = array.array('h', w.readframes(w.getnframes())); w.close()
W = 4410
r = []
for i in range(0, len(a) - W, W):
    s = a[i:i+W]; r.append(20*math.log10(math.sqrt(sum(x*x for x in s)/W)/32768+1e-9))
best = []
L = 35  # 3.5 s
for st in range(0, len(r) - L):
    seg = r[st:st+L]; m = sum(seg)/L; sd = math.sqrt(sum((x-m)**2 for x in seg)/L)
    best.append((sd, st/10, m))
best.sort()
for b in best[:8]: print(f"sd {b[0]:.2f} dB at {b[1]:.1f}s mean {b[2]:.1f}")
chars = " .:-=+*#%@"
print("".join(chars[max(0,min(9,int((x+30)/2)))] for x in r))
