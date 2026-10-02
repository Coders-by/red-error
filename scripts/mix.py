# 默片混音：音效 + 环境声 + BGM → out/mix.wav
# 全片无配音；唯一例外是标 voice 的那一句，若存在 audio/voice/<key>.wav 就放进去（真人录音）
import argparse, json, subprocess, numpy as np, os
from scipy.signal import fftconvolve
R = 48000
ROOT = os.path.join(os.path.dirname(__file__), "..")
parser = argparse.ArgumentParser(description="Mix the film audio without rendering video")
parser.add_argument("--output", default=os.path.join(ROOT, "out", "mix.wav"))
args = parser.parse_args()
TL = json.loads(open(os.path.join(ROOT, "web/timeline.js")).read().split("=", 1)[1].rstrip().rstrip(";"))
TOTAL = TL["TOTAL"]; N = int((TOTAL + 1) * R)

def load(p):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(R), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def put(bus, x, t, g=1.0):
    i = int(t * R)
    if i >= N: return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), N - i); bus[i:i + n] += x[:n] * g

def env(n, fin, fout):
    e = np.ones(n, np.float32)
    a = min(n, int(fin * R)); b = min(n, int(fout * R))
    if a: e[:a] = np.linspace(0, 1, a) ** 1.5
    if b: e[-b:] *= np.linspace(1, 0, b) ** 1.5
    return e[:, None]

voice = np.zeros((N, 2), np.float32); sfx = np.zeros_like(voice); amb = np.zeros_like(voice); bgm = np.zeros_like(voice)

# 旁白加一点房间混响
ir = np.random.default_rng(3).standard_normal(int(.9 * R)).astype(np.float32) * np.exp(-np.linspace(0, 7, int(.9 * R)))
ir /= np.abs(ir).sum() / 6

cache = {}
def sf(name):
    if name not in cache: cache[name] = load(f"{ROOT}/audio/sfx/{name}.wav")
    return cache[name]

for s in TL["scenes"]:
    t0 = s["t0"]
    for ln in s["lines"]:
        vp = f"{ROOT}/audio/voice/{ln['key']}.wav"
        if not ln.get("voice") or not os.path.exists(vp): continue
        print("voice", ln["key"]); x = load(vp)
        if ln.get("vo"):
            wet = np.stack([fftconvolve(x[:, c], ir)[:len(x) + R // 2] for c in range(2)], 1)
            y = np.zeros_like(wet); y[:len(x)] = x; x = y + wet * .18
        put(voice, x, t0 + ln["st"], 1.0)
    for e in s["sfx"]:
        x = sf(e["name"])
        if e.get("dur"):
            d = int(e["dur"] * R)
            x = np.tile(x, (d // len(x) + 1, 1))[:d] * env(d, .02, .3)
        put(sfx, x, t0 + e["at"], e.get("vol", 1.0) * .8)
    # 环境声：按场景铺，边界淡入淡出
    if s.get("amb") and s["amb"] != "none":
        a = sf("amb_" + s["amb"]); d = int((s["dur"] + 1.2) * R)
        x = np.tile(a, (d // len(a) + 1, 1))[:d] * env(d, 1.0, 1.2)
        put(amb, x, t0 - .3, s.get("ambVol", .5) * .55)

from scipy.signal import stft, istft
from scipy.ndimage import minimum_filter1d as _minf, uniform_filter1d as _unif
def dehum(x, fmax=1500, thr=0.55):
    """去掉曲中贯穿始终的持续音（嗡鸣）：统计每个频点在多少帧里处于显著位置，
    超过 thr 的频点视为持续铺底音，整段深度衰减；其余频点再减去 6 秒滑动最小值（稳态残留）"""
    out = np.zeros_like(x)
    mono = x.mean(1)
    f, _, M = stft(mono, R, nperseg=8192, noverlap=6144)
    mdb = 20 * np.log10(np.abs(M) + 1e-9)
    pres = ((mdb > mdb.max(0) - 18) & (mdb > -75)).mean(1)
    pk = (pres > thr) & (f > 40) & (f < fmax) & (pres >= np.roll(pres, 1)) & (pres >= np.roll(pres, -1))
    drone = np.convolve(pk.astype(float), np.ones(3), "same") > 0          # 峰值频点 ±1 bin（约 ±6 Hz）
    print("  drone bins:", sorted(set(int(round(v)) for v in f[drone]))[:40])
    for c in range(x.shape[1]):
        f, _, Z = stft(x[:, c], R, nperseg=8192, noverlap=6144)
        m = np.abs(Z); w = max(3, int(6.0 * R / 2048))
        fl = _unif(_minf(m, w, axis=1), w, axis=1)
        g = np.clip(1 - 1.3 * fl / (m + 1e-9), 0.05, 1); g[f > 2500] = 1
        g[drone] = 0.02
        g = _unif(g, 5, axis=1)
        y = istft(Z * g, R, nperseg=8192, noverlap=6144)[1]
        out[:, c] = y[:len(x)] if len(y) >= len(x) else np.pad(y, (0, len(x) - len(y)))
    return out

for b in TL["BGM"]:
    x = load(f"{ROOT}/audio/bgm/{b['f']}.mp3")[int(b["off"] * R):]
    d = min(len(x), int((b["to"] - b["from"]) * R))
    if b.get("dehum"): x = dehum(x[:d]) * 1.3; print("dehum", b["f"])
    put(bgm, x[:d] * env(d, b["fin"], b["fout"]), b["from"], b["vol"])

# 闪避：对白包络平滑后压低 BGM / 环境
lv = np.abs(voice).max(1)
k = int(.25 * R); lv = np.convolve(lv, np.ones(k) / k, "same")
duck = 1 - .55 * np.clip(lv / .04, 0, 1)
# 快攻慢放
from scipy.ndimage import minimum_filter1d, uniform_filter1d
duck = uniform_filter1d(minimum_filter1d(duck, int(.6 * R)), int(.4 * R))[:, None].astype(np.float32)

mix = voice * 1.15 + sfx + amb * (0.5 + 0.5 * duck) + bgm * duck
# 总线：软限幅
peak = np.abs(mix).max(); print("peak", peak)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix[:int(TOTAL * R)]
mix *= .92 / np.abs(mix).max()
os.makedirs(f"{ROOT}/out", exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(R), "-ac", "2", "-i", "-", args.output], input=mix.astype(np.float32).tobytes(), check=True)
print("ok", len(mix) / R)
