# 全部音效与环境声用 numpy 程序化合成，输出 48k 单声道 wav
import numpy as np, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio/sfx"); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
t_ = lambda d: np.arange(int(SR * d)) / SR
noise = lambda d: rng.standard_normal(int(SR * d))
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)
def env(n, a, d):  # attack/decay (秒)
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def pad(x, d):
    y = np.zeros(int(SR * d)); y[:min(len(x), len(y))] = x[:len(y)]; return y
def at(buf, x, sec, g=1.0):
    i = int(sec * SR); n = min(len(x), len(buf) - i)
    if n > 0: buf[i:i + n] += x[:n] * g
def reverb(x, amt=0.3, dec=1.2):
    ir = noise(dec) * np.exp(-t_(dec) * 5 / dec); ir = lp(ir, 5000); ir /= np.abs(ir).sum() ** 0.5 * 8
    return x + amt * np.convolve(x, ir)[:len(x)]
def save(name, x, peak=0.9):
    x = np.asarray(x, float); m = np.abs(x).max() or 1
    wavfile.write(os.path.join(OUT, name + ".wav"), SR, (x / m * peak * 32767).astype(np.int16))
def tone(f, d, a=0.005, dc=0.5, harm=(1,)):
    t = t_(d); return sum(np.sin(2 * np.pi * f * h * t) / (i + 1) for i, h in enumerate(harm)) * env(len(t), a, dc)
def click(d=0.05, lo=1500, hi=6000, dc=0.008):
    x = bp(noise(d), lo, hi) * env(int(SR * d), 0.0005, dc); return x

# ——— 单次音效 ———
def inkhit():  # 章节卡：低鼓 + 刷子质感
    d = 3.0; t = t_(d); f = 55 * np.exp(-t * 3) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.9)
    brush = bp(noise(d), 800, 5000) * env(len(t), 0.01, 0.25) * 0.5
    return reverb(boom + brush, 0.6, 2.5)
def engine():
    d = 9; t = t_(d); f = 32 + 3 * np.sin(2 * np.pi * 0.3 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * 0.3 + np.sin(ph * 2) * 0.4 + lp(noise(d), 300) * 0.8
    return lp(x, 400) * np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 2)
def ping(): return tone(1320, 0.8, 0.002, 0.18, (1, 2.01)) + np.concatenate([np.zeros(int(SR*.09)), tone(1760, 0.71, 0.002, 0.2)])
def notify():  # RDR2 式低沉木质提示
    a = tone(392, 1.2, 0.004, 0.35, (1, 2, 3.01)); b = tone(523, 1.1, 0.004, 0.4, (1, 2, 3.01))
    y = pad(a, 1.6); at(y, b, 0.12); return reverb(y, 0.5, 1.5)
def kettle():
    d = 4; t = t_(d); w = hp(bp(noise(d), 2500, 3500, 4), 1000) * np.minimum(1, t / 2)
    return w + 0.3 * np.sin(2 * np.pi * 2900 * t) * np.minimum(1, t / 3) * (1 + 0.3 * np.sin(2*np.pi*6*t))
def page():
    d = 0.9; t = t_(d); x = bp(noise(d), 600, 7000) * np.exp(-((t - 0.35) / 0.18) ** 2) * (0.6 + 0.4 * rng.random(len(t)))
    return x
def pencil():
    d = 5; y = np.zeros(int(SR * d)); s = 0.0
    while s < d - 0.4:
        L = rng.uniform(0.15, 0.5); x = hp(noise(L), 2500) * np.hanning(int(SR * L)) * rng.uniform(0.4, 1)
        at(y, x, s); s += L + rng.uniform(0.05, 0.25)
    return y
def typing(d=4.0):
    y = np.zeros(int(SR * d)); s = 0.0
    while s < d - 0.1:
        k = click(0.06, rng.uniform(1500, 2500), 7000, rng.uniform(0.006, 0.012)) + 0.5 * lp(click(0.06, 200, 900, 0.01), 900)
        at(y, k, s, rng.uniform(0.5, 1.0)); s += rng.choice([rng.uniform(0.07, 0.16), rng.uniform(0.2, 0.4)], p=[.85, .15])
    return y
def enter():
    y = pad(click(0.1, 900, 6000, 0.02), 0.5); at(y, lp(click(0.1, 100, 800, 0.03), 800), 0.01, 1.5); return y
def ding(): return reverb(tone(1046, 1.6, 0.002, 0.5, (1, 2.76, 5.4)), 0.3)
def close(): y = pad(tone(700, 0.2, 0.002, 0.05), 0.4); at(y, tone(520, 0.2, 0.002, 0.06), 0.07); return y
def shutter():
    y = pad(click(0.05, 1000, 8000, 0.01), 0.6); at(y, click(0.05, 800, 6000, 0.015), 0.09, 0.8)
    at(y, bp(noise(0.3), 300, 3000) * env(int(SR*.3), 0.02, 0.08) * 0.3, 0.12); return y
def bell():
    d = 5; t = t_(d); x = sum(np.sin(2*np.pi*220*r*t) * np.exp(-t*k) * g for r, k, g in [(1,.6,1),(2.01,1,.6),(2.95,1.5,.5),(4.2,2.2,.3),(5.4,3,.2)])
    return reverb(x * np.minimum(1, t / 0.003), 0.6, 3)
def whistle():  # 远处一阵风掠过：暖色低中频，缓起缓落，无沙粒高频
    d = 5.0; t = t_(d); g = np.sin(np.pi * t / d) ** 2.2
    return reverb((lp(bp(noise(d), 120, 900), 1200) + bp(noise(d), 500, 1800) * g ** 1.5 * 0.35) * g, 0.35, 2.2)
def gunshot():
    d = 4; t = t_(d); crack = hp(noise(0.03), 1000) * env(int(SR*.03), 0.0002, 0.006)
    body = lp(noise(d), 1500) * env(len(t), 0.0005, 0.08)
    thump = np.sin(2*np.pi*np.cumsum(60*np.exp(-t*8)+30)/SR) * env(len(t), 0.001, 0.15)
    y = body + thump * 1.2; at(y, crack, 0, 3)
    tail = lp(noise(d), 700) * np.exp(-t / 1.2) * 0.15; at(y, tail, 0.1)  # 峡谷回声
    for dl, g in [(0.45, .3), (0.9, .15), (1.5, .07)]: at(y, lp(body[:SR], 900), dl, g)
    return y
def deadeye_in():  # 反向混响吸入 + 低频下沉
    d = 2.4; t = t_(d); sw = lp(noise(d), 2500) * (t / d) ** 3
    y = np.zeros(int(SR * (d + 2.0))); at(y, sw, 0)
    at(y, np.sin(2*np.pi*np.cumsum(48*np.exp(-t_(2)*1.5)+28)/SR) * env(int(SR*2), 0.004, 0.7), d - 0.05, 1.4)
    return reverb(lp(y, 6000), 0.7, 2.5)
def deadeye_out():  # 空气回涌
    d = 2.2; t = t_(d); return reverb(bp(noise(d), 200, 3000) * np.sin(np.pi * t / d) ** 2, 0.6)
def heartbeat(d=14):
    y = np.zeros(int(SR * d)); s = 0.2; bpm = 52
    beat = lambda g: np.sin(2*np.pi*np.cumsum(55*np.exp(-t_(0.25)*10)+40)/SR) * env(int(SR*.25), 0.004, 0.06) * g
    while s < d - 0.5:
        at(y, beat(1), s); at(y, beat(0.6), s + 0.22); s += 60 / bpm
    return lp(y, 200)
def mark():  # 锁定：金属短“叮”（非谐波，快速衰减）+ 低闷
    d = 1.2; t = t_(0.4); y = np.zeros(int(SR * d))
    met = sum(np.sin(2*np.pi*f*t) * np.exp(-t*k) for f, k in [(2130, 30), (3410, 45), (5170, 60)]) * 0.25
    at(y, met, 0); at(y, hp(click(0.02), 3000) * 0.8, 0); at(y, lp(noise(0.3), 150) * env(int(SR*.3), 0.001, 0.08), 0, 1.4)
    return reverb(y, 0.45)
def clap(d=3.2):  # 一个人慢慢鼓掌
    y = np.zeros(int(SR * d)); s = 0.1
    while s < d - 0.2:
        at(y, bp(noise(0.08), 900, 4000) * env(int(SR*.08), 0.0005, 0.015), s); s += rng.uniform(0.62, 0.72)
    return reverb(y, 0.5, 1.5)
def ticks(d=6.4):  # CI 流水线快速刷新
    y = np.zeros(int(SR * d)); s = 0; iv = 0.12
    while s < d:
        at(y, tone(2400 + rng.uniform(-100, 100), 0.03, 0.0005, 0.006), s, 0.6); s += iv; iv = max(0.045, iv * 0.985)
    return y
def success():  # CI 通过：两声木质轻响
    y = np.zeros(int(SR * 1.6))
    for i, f in enumerate([880, 1320]):
        tt = t_(0.5); at(y, (np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*f*3.9*tt)) * env(len(tt), 0.001, 0.07) + bp(noise(0.5), 1500, 5000) * env(len(tt), 0.0005, 0.004), i * 0.13)
    return reverb(y, 0.35)
def complete():  # 任务完成：低沉定音鼓 + 远处钟
    d = 5; t = t_(d); boom = lp(noise(d), 120) * env(len(t), 0.004, 0.5) * 2
    bell_ = sum(np.sin(2*np.pi*146*r*t) * np.exp(-t*k) * g for r, k, g in [(1,.7,1),(2.02,1.1,.5),(2.93,1.6,.35),(4.1,2.4,.2)])
    return reverb(boom + bell_ * np.minimum(1, t / 0.004) * 0.5, 0.6, 3)
def stamp():
    y = pad(lp(noise(0.3), 500) * env(int(SR*.3), 0.0008, 0.04), 1.0); at(y, click(0.05, 400, 3000, 0.01), 0, 1.2)
    at(y, np.sin(2*np.pi*70*t_(0.3))*env(int(SR*.3),0.001,0.07), 0, 1.5); return reverb(y, 0.3)
def cough():  # 咳嗽：共振峰滤波的气流爆破，无正弦
    y = np.zeros(int(SR * 2.4))
    for s, g in [(0, 1), (0.42, 0.7), (0.78, 0.45)]:
        L = 0.28; n = int(SR * L); x = noise(L)
        v = bp(x, 380, 700, 3) * 1.2 + bp(x, 1100, 1900, 3) * 0.8 + bp(x, 2400, 3400, 2) * 0.3
        at(y, v * env(n, 0.006, 0.07), s, g)
    at(y, bp(noise(0.9), 500, 2500) * env(int(SR*.9), 0.25, 0.25) * 0.12, 1.3)
    return reverb(lp(y, 5000), 0.2)
def lighter():
    y = pad(click(0.04, 2000, 9000, 0.004), 1.6); at(y, click(0.04, 1500, 8000, 0.004), 0.05, 0.7)
    at(y, bp(noise(1.2), 200, 2000) * env(int(SR*1.2), 0.05, 0.4) * 0.3, 0.1); return y
def thunder():
    d = 7; t = t_(d); x = lp(noise(d), 180) * (np.exp(-t/2.2) * np.minimum(1, t/0.3))
    x += lp(noise(d), 900) * env(len(t), 0.01, 0.25) * 0.4
    return x * (1 + 0.6 * lp(noise(d), 3))
def whoosh():
    d = 1.6; t = t_(d); g = np.exp(-((t - 0.8) / 0.28) ** 2)
    f = 400 + 1600 * g; x = np.zeros(len(t)); seg = 1600
    n = noise(d)
    for i in range(0, len(t), seg):
        c = f[i]; x[i:i+seg] = bp(n[i:i+seg+2000], c*0.6, min(c*1.6, 20000))[:len(x[i:i+seg])]
    return x * g
def sent(): y = pad(tone(880, 0.3, 0.002, 0.06), 0.5); at(y, tone(1320, 0.3, 0.002, 0.08), 0.06); return y
def alarm():  # 远处的告警提示音（柔化，隔着房间）
    d = 2.2; t = t_(d); gate = env(len(t), 0.002, 1) * 0 + ((t % 0.55) < 0.18) * 1.0
    x = (np.sin(2*np.pi*880*t) + 0.25*np.sin(2*np.pi*1760*t)) * lp(gate, 60)
    return reverb(lp(x, 2200), 0.5, 1.2) * np.minimum(1, (d - t) / 0.3)
def pat():  # 轻拍键盘
    y = pad(lp(noise(0.12), 700) * env(int(SR*.12), 0.001, 0.03), 1.0); at(y, lp(noise(0.12), 700) * env(int(SR*.12), 0.001, 0.03), 0.42, 0.8); return y
def lidclose():
    y = pad(lp(noise(0.2), 1200) * env(int(SR*.2), 0.001, 0.05), 1.4); at(y, click(0.05, 1000, 5000, 0.01), 0, 0.8)
    at(y, np.sin(2*np.pi*110*t_(0.3))*env(int(SR*.3),0.001,0.06), 0, 1.0); return reverb(y, 0.6, 2)
def slam():  # 片名砸下
    d = 5; t = t_(d); boom = np.sin(2*np.pi*np.cumsum(70*np.exp(-t*2)+30)/SR) * env(len(t), 0.002, 1.3)
    metal = sum(np.sin(2*np.pi*f*t)*np.exp(-t*k) for f, k in [(311,1.2),(467,1.6),(740,2.2),(1123,3)]) * 0.25
    return reverb(boom + metal + lp(noise(d), 2000) * env(len(t), 0.001, 0.12), 0.8, 3.5)
def laugh():
    y = np.zeros(int(SR * 2.4)); s = 0
    for i in range(6):
        L = 0.14; tt = t_(L); f = 280 - i * 8
        v = np.sin(2*np.pi*f*tt) + 0.5*np.sin(4*np.pi*f*tt) + 0.3*bp(noise(L), 800, 3000)
        at(y, v * np.hanning(len(tt)) * (1 - i * 0.1), s); s += 0.2
    return reverb(bp(y, 150, 4000), 0.3)

def buzz():  # 手机在桌面上震动
    d = 0.9; t = t_(d); g = ((t % 0.45) < 0.32).astype(float) * (t < 0.8)
    x = (np.sin(2*np.pi*150*t) + 0.6*np.sign(np.sin(2*np.pi*300*t)) * 0.3) * g
    return lp(x + 0.3 * bp(noise(d), 200, 900) * g, 1800)
def key():  # 单个机械键（孩子按得慢而重）
    y = pad(click(0.08, 1200, 6500, 0.012), 0.4); at(y, lp(click(0.1, 100, 700, 0.025), 700), 0.004, 1.6)
    return reverb(y, 0.25, 0.6)

# ——— 环境声（30 秒立体声，FFT 频域塑形 → 天然首尾无缝；不含任何正弦嗡鸣） ———
AD = 30
NA = SR * AD
FR = np.fft.rfftfreq(NA, 1 / SR)
def colored(shape, n=NA):
    """频域塑形噪声，循环边界天然无缝；shape(f) 为幅度曲线"""
    X = (rng.standard_normal(len(FR)) + 1j * rng.standard_normal(len(FR))) * shape(np.maximum(FR, 1.0))
    X[0] = 0; x = np.fft.irfft(X, n); return x / (x.std() or 1)
def band(lo, hi, tilt=-0.5, soft=1.2):
    """平滑宽带：lo~hi 之间 f^tilt，两侧按 soft 八度缓降，避免尖锐共振"""
    return lambda f: f ** tilt / (1 + (lo / f) ** (2 * soft)) / (1 + (f / hi) ** (2 * soft))
def slow(rate, lo=0.0, hi=1.0):
    """循环慢变包络：带宽约 rate Hz 的平滑随机曲线，映射到 lo..hi"""
    x = colored(lambda f: np.exp(-(f / rate) ** 2)); x = (x - x.min()) / (np.ptp(x) or 1)
    return lo + (hi - lo) * x
def st(fn, width=0.6):
    """立体声：共同分量 + 左右独立分量，width 越大越开阔"""
    c = fn(); l = fn(); r = fn(); k = np.sqrt(1 - width ** 2)
    return np.stack([c * k + l * width, c * k + r * width], 1)
def scatter(buf, grains, rate, gain=(0.1, 1.0), pan=0.8):
    """把颗粒声随机撒进立体声缓冲（循环回绕）"""
    n = int(rate * AD); N = len(buf)
    for _ in range(n):
        g = grains[rng.integers(len(grains))]; i = rng.integers(N); a = np.exp(rng.uniform(np.log(gain[0]), np.log(gain[1])))
        p = rng.uniform(-pan, pan); idx = (i + np.arange(len(g))) % N
        buf[idx, 0] += g * a * np.sqrt((1 - p) / 2); buf[idx, 1] += g * a * np.sqrt((1 + p) / 2)
    return buf
def grain(lo, hi, dc, L=None):
    L = L or int(SR * dc * 8); return bp(rng.standard_normal(L), lo, hi) * np.exp(-np.arange(L) / (SR * dc))
def gusty(calm=0.35, bright=1.0, rate=0.12):
    """风：三段频带各跟随同一阵风曲线（有先后），阵风越强越亮，像空气不是嗡鸣"""
    g = slow(rate, calm, 1.0); g2 = np.roll(g, int(SR * 0.6)) ** 2; g3 = np.roll(g, int(SR * 1.1)) ** 3
    def one():
        lo = colored(band(70, 320, -0.8, 1.0)); mid = colored(band(300, 1400, -0.6, 1.0)); air = colored(band(1400, 5500, -0.4, 1.3))
        return lo * 0.55 * g + mid * 0.5 * g2 + air * 0.22 * bright * g3
    return st(one, 0.75)
def wind():  # 雪夜寒风：低中频为主，缓慢阵风，外加极轻的雪粒打窗
    x = gusty(0.3, 0.9, 0.1)
    return scatter(x, [grain(3000, 9000, 0.0012) for _ in range(12)], 14, (0.02, 0.09))
def desert():  # 正午旷野：暖而干的低空气流，偶尔远处起风，高频明显收住
    g = slow(0.07, 0.25, 1.0)
    def one():
        return colored(band(60, 500, -0.9, 1.0)) * 0.6 * g + colored(band(400, 2200, -0.7, 1.0)) * 0.25 * g ** 2.5
    return st(one, 0.7)
def rain():  # 雨夜：远处雨幕 + 近处不同大小的雨滴 + 零星屋檐滴水
    roar = st(lambda: colored(band(150, 4000, -0.7, 1.0)) * slow(0.15, 0.8, 1.0), 0.8) * 0.5
    fine = [grain(rng.uniform(2500, 5000), rng.uniform(7000, 11000), rng.uniform(0.0008, 0.002)) for _ in range(30)]
    mid = [grain(rng.uniform(900, 1800), rng.uniform(3000, 6000), rng.uniform(0.002, 0.005)) for _ in range(20)]
    x = scatter(roar, fine, 420, (0.04, 0.35))
    x = scatter(x, mid, 60, (0.1, 0.6))
    drip = []
    for _ in range(6):  # 屋檐滴水：短噪声冲击 + 很快衰减的水声，非纯正弦
        L = int(SR * 0.08); f = rng.uniform(1100, 2200); ex = rng.standard_normal(L) * np.exp(-np.arange(L) / (SR * 0.001))
        drip.append(bp(ex, f * 0.85, f * 1.15, 2) * 6 * np.exp(-np.arange(L) / (SR * 0.012)))
    return scatter(x, drip, 0.6, (0.3, 0.8), 0.6)
def fan():  # 服务器机柜：平滑宽带气流，微弱起伏，无转速谐波
    g = slow(0.2, 0.9, 1.0)
    return st(lambda: colored(band(90, 5000, -0.55, 1.0)) * g, 0.5)
def room():  # 安静室内底噪：非常轻、偏暗
    return st(lambda: colored(band(50, 1800, -0.8, 1.0)), 0.6)
def office():  # 废弃写字楼夜里：室内底噪 + 远处暖气管偶尔轻响
    x = room() * 0.9
    x = scatter(x, [grain(600, 2500, 0.004) for _ in range(8)], 0.25, (0.8, 1.6), 0.7)
    return scatter(x, [grain(1500, 5000, 0.25, int(SR * 1.2)) * 0.05 for _ in range(4)], 0.08, (0.8, 1.0), 0.5)
def carin():  # 车内：胎噪与路噪，随路面缓慢起伏
    g = slow(0.3, 0.75, 1.0)
    return st(lambda: colored(band(40, 450, -0.9, 1.0)) * g + colored(band(500, 2500, -0.7, 1.0)) * 0.08, 0.35)
def city():  # 远处城市：车流雾化成一层 + 偶尔驶过
    x = st(lambda: colored(band(80, 1500, -0.8, 1.0)) * slow(0.1, 0.7, 1.0), 0.7) * 0.8
    for _ in range(3):
        L = SR * 5; w = np.hanning(L) ** 1.5; c = colored(band(200, 2500, -0.6, 1.0))[:L] * w
        i = rng.integers(NA - L); p = rng.uniform(-0.6, 0.6); pan = np.linspace(-p, p, L)
        x[i:i + L, 0] += c * 0.9 * np.sqrt((1 - pan) / 2); x[i:i + L, 1] += c * 0.9 * np.sqrt((1 + pan) / 2)
    return x
def chirp(f0, L=0.12):
    tt = t_(L); f = f0 * (1 + 0.35 * np.sin(np.pi * tt / L)); return np.sin(2*np.pi*np.cumsum(f)/SR) * np.sin(np.pi*tt/L) ** 2
def birds():  # 清晨：极轻的树叶/空气沙响（去掉低中频底噪，避免嗡鸣）+ 分散在左右远近的鸟鸣
    x = st(lambda: colored(band(900, 6000, -0.4, 1.4)) * slow(0.15, 0.5, 1.0), 0.85) * 0.07
    s = 0.3
    while s < AD - 2:
        f0 = rng.choice([2800, 3400, 4200, 5000]); k = rng.integers(2, 6); p = rng.uniform(-0.8, 0.8); a0 = rng.uniform(0.25, 1.0)
        for j in range(k):
            c = chirp(f0 * rng.uniform(0.95, 1.1), rng.uniform(0.06, 0.14)) * a0 * rng.uniform(0.6, 1.0); i = int((s + j * 0.13) * SR)
            x[i:i + len(c), 0] += c * np.sqrt((1 - p) / 2); x[i:i + len(c), 1] += c * np.sqrt((1 + p) / 2)
        s += rng.uniform(0.8, 2.5)
    return np.stack([reverb(x[:, 0], 0.35), reverb(x[:, 1], 0.35)], 1)
def dawn(): return birds()  # 清晨：只保留鸟鸣与极轻叶响，去掉低频风（嗡鸣感来源）

def save_amb(name, x, rms_db):
    """环境声按 RMS 归一（而不是按峰值），并轻微软限幅"""
    x = x - x.mean(0); x = x / np.sqrt((x ** 2).mean()) * 10 ** (rms_db / 20)
    x = np.tanh(x / 0.9) * 0.9
    wavfile.write(os.path.join(OUT, "amb_" + name + ".wav"), SR, (x * 32767).astype(np.int16))
for name, fn in list(globals().items()):
    if callable(fn) and name in """inkhit engine ping notify kettle page pencil typing enter ding close shutter bell whistle
      gunshot deadeye_in deadeye_out heartbeat mark clap ticks success complete stamp cough lighter thunder whoosh sent
      alarm pat lidclose slam laugh buzz key""".split():
        save(name, fn())
AMB_RMS = dict(wind=-19, carin=-18, fan=-20, office=-21, desert=-22, room=-21, rain=-19, city=-20, birds=-25, dawn=-25)
for name, db in AMB_RMS.items():
    save_amb(name, globals()[name](), db)
print(sorted(os.listdir(OUT)))
