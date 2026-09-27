import wave, array, math
w = wave.open("pixabay_saber_hum.wav"); a = array.array('h', w.readframes(w.getnframes())); w.close()
S = 44100
out = []
for i in range(0, len(a) - S, S):
    s = a[i:i+S]; e = math.sqrt(sum(x*x for x in s) / S)
    out.append(f"{i//S}:{20*math.log10(e/32768+1e-9):.1f}")
print(" ".join(out))
