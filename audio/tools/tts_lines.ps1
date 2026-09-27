# Generates raw death-line voice takes with the built-in Windows voices (processed later by death_sounds.py).
Add-Type -AssemblyName System.Speech
$out = "C:\Users\User\PROJECTS\jedi-arena\audio\work\tts"
New-Item -ItemType Directory -Force $out | Out-Null
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(44100, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
# name | voice | rate | text
$lines = @(
  "droid_1|David|3|Ow!",
  "droid_2|David|3|Uh oh.",
  "droid_3|David|2|Oh nooo!",
  "droid_4|David|3|Not again!",
  "droid_5|David|4|Aw, scrap!",
  "droid_6|Zira|3|Ouchie!",
  "droid_7|David|3|I regret nothing!",
  "trooper_1|David|1|Argh!",
  "trooper_2|David|2|Ugh!",
  "trooper_3|David|3|Man down!",
  "trooper_4|David|0|Aaagh!",
  "jet_1|David|2|Mayday! Mayday!",
  "jet_2|David|3|I'm hit! I'm hit!",
  "jet_3|David|2|Going down!",
  "warden_1|David|-5|Nooooo...",
  "warden_2|David|-4|Impossible...",
  "roller_1|Zira|8|Eek!"
)
foreach ($l in $lines) {
  $p = $l.Split("|")
  $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $s.SelectVoice("Microsoft " + $p[1] + " Desktop")
  $s.Rate = [int]$p[2]
  $s.SetOutputToWaveFile((Join-Path $out ($p[0] + ".wav")), $fmt)
  $s.Speak($p[3])
  $s.Dispose()
}
Get-ChildItem $out | Select-Object Name, Length
