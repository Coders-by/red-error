# 用 macOS say 为每句台词合成语音，并按角色做音色处理
import json, subprocess, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
scenes = json.loads(subprocess.check_output(["node", "-e",
    "console.log(JSON.stringify(require('./web/scenes.js').SCENES))"], cwd=ROOT))
V = lambda n: f"{n} (中文（中国大陆）)"
# voice, rate(wpm), pitch factor, extra filter
VOICE = {
  "老亚":   (V("Reed"), 150, 0.90, "lowshelf=f=180:g=4,equalizer=f=3000:t=q:w=1:g=2"),
  "达总":   (V("Rocko"), 158, 0.93, "lowshelf=f=150:g=3"),
  "马迭代": (V("Eddy"), 170, 1.02, ""),
  "米卡":   (V("Rocko"), 172, 1.06, "highpass=f=220,equalizer=f=1800:t=q:w=1:g=4"),
  "萨姐":   (V("Shelley"), 168, 0.96, ""),
  "米尔顿": (V("Grandpa"), 150, 1.0, "equalizer=f=4000:t=q:w=1:g=3,aecho=0.8:0.5:40:0.12"),
  "HR":     ("Tingting", 165, 1.0, "highpass=f=150"),
  "孩子":   (V("Sandy"), 160, 1.16, ""),
}
out = os.path.join(ROOT, "audio/tts"); os.makedirs(out, exist_ok=True)
durs = {}
for s in scenes:
    for i, ln in enumerate(s.get("lines", [])):
        key = f"{s['id']}_{i+1}"
        wav = os.path.join(out, key + ".wav")
        voice, rate, p, fx = VOICE[ln["who"]]
        if not os.path.exists(wav):
            txt = ln["t"].replace("……", "，").replace("HR", "")
            aiff = f"/tmp/tts_{key}.aiff"
            subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff, txt], check=True)
            chain = [f"asetrate=22050*{p}", "aresample=48000", f"atempo={1/p:.4f}"]
            if fx: chain.append(fx)
            if ln.get("vo"): chain.append("aecho=0.85:0.6:60|110:0.18|0.10")
            chain += ["silenceremove=start_periods=1:start_threshold=-50dB",
                      "areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                      "loudnorm=I=-16:TP=-1.5", "aresample=48000"]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", aiff, "-af", ",".join(chain),
                            "-ac", "1", "-ar", "48000", wav], check=True)
            os.remove(aiff)
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "csv=p=0", wav]).strip())
        durs[key] = round(d, 3)
json.dump(durs, open(os.path.join(ROOT, "audio/tts/durations.json"), "w"), ensure_ascii=False, indent=1)
print(len(durs), "lines, total", round(sum(durs.values()), 1), "s")
