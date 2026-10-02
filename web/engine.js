// 确定性渲染引擎：window.setTime(t) 画出第 t 秒的画面（无定时器、无 CSS 动画）
const W = 1920, H = 816, FPS = 24;
const $ = (s) => document.querySelector(s);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ease = (x) => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eout = (x) => 1 - Math.pow(1 - clamp(x), 3);
const lerp = (a, b, k) => a + (b - a) * k;
const prog = (lt, st, d) => clamp((lt - st) / d);
// 淡入淡出：lt∈[0,total]
const vis = (lt, total, fi = .5, fo = .5) => lt < 0 || lt > total ? 0 : Math.min(clamp(lt / fi), clamp((total - lt) / fo));
const hash = (i, k = 0) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };

const SC = TL.scenes;
const FX = { filter: "", flash: 0, shake: 0, sub: true };
const UI = {};   // 各 UI 类型注册于 ui.js：UI[type] = { film?, mk(u, s), up(e, u, lt, total, s, slt) }

// ——— 画面镜头（含 alt 切镜） ———
const SRC = {};
const DEF_KB = [0.5, 0.5, 1.04, 0.5, 0.5, 1.12];
function shots(s) {
  if (!s.img) return [];
  const a = [{ t: 0, img: s.img, clip: s.clip, kb: s.kb || DEF_KB, tr: s.tr || "dissolve" }];
  (s.alt || []).forEach(x => a.push({ t: x.at, img: x.img, clip: x.clip, kb: x.kb || s.kb || DEF_KB, tr: x.tr || "cut" }));
  return a.map((x, i) => ({ ...x, end: i + 1 < a.length ? a[i + 1].t : s.dur }));
}
// 手持：几组不相关正弦叠加，模拟呼吸与手抖
function handheld(t, a) {
  const x = a * (Math.sin(t * 1.13) * 5 + Math.sin(t * 2.71 + 1.3) * 2.4 + Math.sin(t * 6.3 + 4) * .6);
  const y = a * (Math.sin(t * .87 + 2) * 3.6 + Math.sin(t * 2.23 + .4) * 1.8 + Math.sin(t * 7.7 + 1) * .5);
  const r = a * .06 * Math.sin(t * .61 + .8);
  return { x, y, r };
}
function kbTransform(sh, lt, sd, hh, t, dx = 0) {
  const k = sh.kb, span = Math.max(1, sd - sh.t), p = clamp((lt - sh.t) / span);
  const q = p * p * (3 - 2 * p) * .6 + p * .4;
  const base = 1.03 + hh * .012;
  const x = lerp(k[0], k[3], q), y = lerp(k[1], k[4], q), sc = Math.max(base, lerp(k[2], k[5], q) * 1.02);
  const h = handheld(t, hh);
  return `translate(${(0.5 - x) * W * (sc - 1) + h.x + dx}px, ${(0.5 - y) * H * (sc - 1) + h.y}px) rotate(${h.r}deg) scale(${sc})`;
}
function setLayer(id, sh, lt, sd, op, o = {}) {
  const L = $(id), img = L.firstChild;
  if (!sh || op <= 0) { L.style.opacity = 0; return; }
  const src = sh.clip ? clipFrameSource(sh.clip, lt - sh.t, window.CLIPS || {}) : SRC[sh.img] || `imgx/${sh.img}.jpg`;
  if (img.getAttribute("src") !== src) img.setAttribute("src", src);
  img.style.transform = sh.clip ? `translateX(${o.dx || 0}px) scale(1.03)` : kbTransform(sh, lt, sd, o.hh ?? .35, o.t ?? 0, o.dx || 0);
  img.style.filter = o.blur ? `blur(${o.blur}px)` : "";
  L.style.opacity = op;
}

// ——— 粒子特效 ———
const fxc = $("#fx").getContext("2d");
function drawFx(type, t, lt) {
  fxc.clearRect(0, 0, W, H);
  if (!type) return;
  const g = fxc;
  if (type === "snow" || type === "snowglass") {
    for (let i = 0; i < 200; i++) {
      const z = hash(i, 1), sp = 40 + z * 170, r = 1 + z * z * 3.2;
      const x = ((hash(i, 2) * W + t * (60 + 90 * z) + Math.sin(t * .7 + i) * 30 * z) % (W + 40) + W + 40) % (W + 40) - 20;
      const y = ((hash(i, 3) * H + t * sp) % (H + 20)) - 10;
      g.globalAlpha = (.12 + z * .4) * (z > .85 ? 1 : .8); g.fillStyle = "#f4f6f8";
      g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    }
    if (type === "snowglass") glass(g, t, "#dfe8f0", 24);
  } else if (type === "rain" || type === "rainglass") {
    g.strokeStyle = "#bcc8d4"; g.lineWidth = 1.2;
    for (let i = 0; i < 240; i++) {
      const z = hash(i, 1), sp = 1400 + z * 900, len = 18 + z * 40;
      const x = (hash(i, 2) * (W + 200) + t * 180) % (W + 200) - 100, y = (hash(i, 3) * (H + 200) + t * sp) % (H + 200) - 100;
      g.globalAlpha = .06 + z * .22; g.beginPath(); g.moveTo(x, y); g.lineTo(x - len * .14, y - len); g.stroke();
    }
    if (type === "rainglass") glass(g, t, "#a8b8c8", 30);
  } else if (type === "embers") {
    for (let i = 0; i < 40; i++) {
      const z = hash(i, 1), life = 4 + z * 4, ph = ((t + hash(i, 2) * life) % life) / life;
      const x = W * (.35 + hash(i, 3) * .5) + Math.sin(t * 1.3 + i) * 40 * ph, y = H * (.95 - ph * .9);
      g.globalAlpha = Math.sin(ph * Math.PI) * (.4 + z * .6);
      g.fillStyle = z > .5 ? "#ffb347" : "#ff7a2a"; g.beginPath(); g.arc(x, y, 1 + z * 2.2, 0, 7); g.fill();
    }
  } else if (type === "steam") {
    for (let i = 0; i < 26; i++) {
      const life = 5, ph = ((t + hash(i, 2) * life) % life) / life;
      const x = W * (.5 + (hash(i, 3) - .5) * .18) + Math.sin(t * .6 + i) * 60 * ph, y = H * (.62 - ph * .6), r = 60 + ph * 220;
      const gr = g.createRadialGradient(x, y, 0, x, y, r);
      gr.addColorStop(0, `rgba(255,250,240,${.1 * Math.sin(ph * Math.PI)})`); gr.addColorStop(1, "rgba(255,250,240,0)");
      g.globalAlpha = 1; g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
    }
  } else if (type === "dust") {
    for (let i = 0; i < 50; i++) {
      const z = hash(i, 1);
      const x = (hash(i, 2) * W + t * (20 + z * 60)) % W, y = hash(i, 3) * H + Math.sin(t * .5 + i) * 20;
      g.globalAlpha = (.08 + z * .3) * (.6 + .4 * Math.sin(t * 2 + i)); g.fillStyle = "#f3d9a4";
      g.beginPath(); g.arc(x, y, .6 + z * 1.8, 0, 7); g.fill();
    }
    haze(g, t, "rgba(230,170,90,", .04);
  } else if (type === "neon") {
    const cols = ["#ff3b6b", "#2de2e6", "#f6c343", "#7b61ff", "#ff8a3d"];
    for (let i = 0; i < 18; i++) {
      const z = hash(i, 1), x = (hash(i, 2) * W - t * (80 + z * 260)) % W, xx = x < 0 ? x + W : x, y = H * (.1 + hash(i, 3) * .55), r = 12 + z * 50;
      const gr = g.createRadialGradient(xx, y, 0, xx, y, r);
      gr.addColorStop(0, cols[i % 5] + "66"); gr.addColorStop(1, cols[i % 5] + "00");
      g.globalAlpha = .7; g.fillStyle = gr; g.fillRect(xx - r, y - r, r * 2, r * 2);
    }
  } else if (type === "mist") {
    haze(g, t, "rgba(255,225,190,", .1);
  }
  g.globalAlpha = 1;
}
function haze(g, t, rgba, a) {
  for (let i = 0; i < 6; i++) {
    const x = ((hash(i, 5) * W + t * (15 + i * 6)) % (W + 1200)) - 600, y = H * (.3 + hash(i, 6) * .6), r = 500 + hash(i, 7) * 400;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, rgba + a + ")"); gr.addColorStop(1, rgba + "0)");
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
}
function glass(g, t, col, n) {  // 车窗/玻璃上的水珠
  for (let i = 0; i < n; i++) {
    const z = hash(i, 8), x = hash(i, 9) * W, slide = z > .8 ? ((t * 30 * z + hash(i, 4) * H) % H) : hash(i, 10) * H, r = 2 + z * 6;
    g.globalAlpha = .18 + z * .2; g.fillStyle = col; g.beginPath(); g.ellipse(x, slide, r * .8, r, 0, 0, 7); g.fill();
    g.globalAlpha = .35; g.fillStyle = "#fff"; g.beginPath(); g.arc(x - r * .3, slide - r * .3, r * .25, 0, 7); g.fill();
  }
}
// ——— 胶片颗粒 ———
const gc = $("#grain").getContext("2d");
const GW = 960, GH = 408;
const GRAINS = [...Array(6)].map((_, k) => {
  const c = document.createElement("canvas"); c.width = GW; c.height = GH;
  const x = c.getContext("2d"), d = x.createImageData(GW, GH);
  for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (hash(i, k + 20) + hash(i, k + 40) - 1) * 70; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
  x.putImageData(d, 0, 0); return c;
});
function drawGrain(t) {
  const k = Math.floor(t * FPS) % GRAINS.length;
  gc.imageSmoothingEnabled = true; gc.drawImage(GRAINS[k], 0, 0, W, H);
  const f = Math.floor(t * FPS);
  if (hash(f, 3) > .985) { gc.fillStyle = "rgba(255,255,255,.25)"; gc.fillRect(hash(f, 4) * W, 0, 1, H); }
}

// ——— UI 实例（全局绝对时间窗） ———
const INST = [];
SC.forEach(s => (s.ui || []).forEach((u, i) => {
  const A = s.t0 + u.at;
  const E = u.untilAbs ?? (u.dur ? A + u.dur : s.t0 + s.dur);
  INST.push({ s, u, A, E, key: `${s.id}_${i}`, e: null });
}));
function mountUI(it) {
  const def = UI[it.u.type];
  if (!def) { console.warn("no ui", it.u.type); return null; }
  const e = def.mk(it.u, it.s); e.classList.add("ui-" + it.u.type);
  (def.film ? $("#filmui") : $("#ui")).appendChild(e); return e;
}

// ——— 字幕（默片）：普通台词 = 下方字幕 + 署名；card = 全屏字卡；vo = 斜体旁白；voice = 真正出声的那一句 ———
const subEl = $("#sub"), whoEl = subEl.querySelector(".who"), txtEl = subEl.querySelector(".txt");
const cardEl = $("#card"), cardTx = cardEl.querySelector(".ct"), cardWho = cardEl.querySelector(".cw");
// 字卡：更长的缓入缓出（smoothstep），避免亮度突变造成闪烁感
const CARD_IN = .3, CARD_FIN = .7, CARD_OUT = .6, CARD_FOUT = .8;
function curLine(s, lt, pre = .08, post = .35) {
  let c = null;
  for (const l of s.lines || []) if (lt >= l.st - (l.card ? CARD_IN : pre) && lt <= l.en + (l.card ? CARD_OUT : post)) c = l;
  return c;
}
const sstep = x => { x = clamp(x); return x * x * (3 - 2 * x); };
function drawSub(s, lt) {
  const cur = curLine(s, lt);
  cardEl.style.opacity = 0; subEl.style.opacity = 0;
  if (!cur || !FX.sub) return;
  const op = cur.card
    ? Math.min(sstep((lt - cur.st + CARD_IN) / CARD_FIN), sstep((cur.en + CARD_OUT - lt) / CARD_FOUT))
    : Math.min(clamp((lt - cur.st + .08) / .25), clamp((cur.en + .35 - lt) / .3));
  if (cur.card) {
    cardTx.textContent = cur.t; cardTx.className = "ct" + (cur.hand ? " hand" : "");
    cardWho.textContent = cur.hand ? "" : "—— " + cur.who;
    cardEl.style.opacity = op; tf2(cardTx, `scale(${1.03 - .03 * eout((lt - cur.st) / 1.2)})`);
    return;
  }
  whoEl.textContent = cur.vo ? "" : cur.who; whoEl.style.color = (TL.CAST[cur.who] || {}).color || "#ccc";
  txtEl.textContent = cur.t; subEl.className = cur.vo ? "vo" : cur.voice ? "voice" : "";
  subEl.style.opacity = op;
}
const tf2 = (e, v) => { e.style.transform = v; };

// ——— 主入口 ———
const XF = .9;
let lastScene = -1;
window.setTime = function (t) {
  let si = SC.findIndex(s => t >= s.t0 && t < s.t0 + s.dur); if (si < 0) si = SC.length - 1;
  const s = SC[si], lt = t - s.t0;
  FX.filter = ""; FX.flash = 0; FX.shake = 0; FX.sub = true; FX.dim = 0; FX.kbBoost = 0;

  // UI 先更新（它们可以写 FX）
  for (const it of INST) {
    const on = t >= it.A - .001 && t < it.E + (UI[it.u.type]?.tail ?? .8);
    if (on) {
      if (!it.e) it.e = mountUI(it);
      if (it.e) { it.e.style.display = ""; UI[it.u.type].up(it.e, it.u, t - it.A, it.E - it.A, it.s, lt); }
    } else if (it.e) { it.e.remove(); it.e = null; }
  }

  // 画面：当前镜头（上层 B）+ 前一镜头（下层 A），按 tr 转场：dissolve / cut / whip / rack
  const sh = shots(s); let ci = -1; sh.forEach((x, i) => { if (lt >= x.t) ci = i; });
  const cur = sh[ci];
  let prev = null, prevS = s, since = 0;
  if (cur) {
    since = lt - cur.t;
    if (ci > 0) prev = sh[ci - 1];
    else if (si > 0 && SC[si - 1].img && !SC[si - 1].noCarry) { prevS = SC[si - 1]; const ps = shots(prevS); prev = ps[ps.length - 1]; }
  }
  const hhB = s.hh ?? .35, hhA = prevS.hh ?? .35, plt = prevS === s ? lt : prevS.dur + lt;
  const tr = cur ? cur.tr : "dissolve";
  let opB = cur ? (prev ? 1 : clamp(since / 1.2)) : 0, opA = 0, oA = { hh: hhA, t }, oB = { hh: hhB, t };
  if (cur && prev) {
    if (tr === "dissolve") { const k = clamp(since / XF); opB = ease(k); opA = k < 1 ? 1 : 0; }
    else if (tr === "whip") {
      const D = .42, k = clamp(since / D), e = ease(k);
      opA = k < 1 ? 1 : 0; opB = clamp((k - .35) / .3);
      oA = { ...oA, dx: -e * W * .9, blur: 30 * Math.sin(Math.min(1, k * 1.6) * Math.PI / 2) };
      oB = { ...oB, dx: (1 - e) * W * .9, blur: 30 * (1 - e) };
    } else if (tr === "rack") { oB.blur = 16 * (1 - eout(since / 1.3)); }
  }
  setLayer("#imgA", opA > 0 ? prev : null, plt, prevS.dur, opA, oA);
  setLayer("#imgB", cur, lt, s.dur, opB, oB);

  drawFx(cur?.clip ? null : s.fx, t, lt);
  drawGrain(t);

  // 默片式轻微闪烁（亮度随帧抖动 ±1.5%）
  const fl = 1 + (hash(Math.floor(t * FPS), 9) - .5) * .03;
  const grade = s.grade === "bleach" ? "saturate(.25) contrast(1.25) brightness(1.18) sepia(.2)" : "saturate(.92) contrast(1.08) sepia(.1)";
  $("#film").style.filter = (FX.filter || grade) + ` brightness(${(1 - (FX.dim || 0)) * fl})`;
  $("#film").style.transform = FX.shake ? `translate(${(hash(t * 97, 1) - .5) * FX.shake}px, ${(hash(t * 97, 2) - .5) * FX.shake}px)` : "";

  drawSub(s, lt);

  // 黑场：片头淡入、scene.fadeOut、片尾
  let blk = 1 - clamp(t / 1.5);
  if (s.fadeOut) blk = Math.max(blk, clamp((lt - (s.dur - s.fadeOut)) / s.fadeOut));
  blk = Math.max(blk, clamp((t - (TL.TOTAL - 2)) / 2));
  blk = Math.max(blk, FX.flash < 0 ? -FX.flash : 0);
  $("#black").style.opacity = blk;
  $("#black").style.background = FX.flash > 0 ? `rgba(255,255,255,${FX.flash})` : "#000";
  if (FX.flash > 0) $("#black").style.opacity = 1;
  lastScene = si;
};

// Capture must wait for the chosen image to decode before taking its screenshot.
window.renderFrame = async function (t) {
  setTime(t);
  await Promise.all([$("#imgA"), $("#imgB")].filter(layer => +layer.style.opacity > 0)
    .map(layer => layer.firstChild.decode()));
};

// 预加载字体与图片，完成后置 window.READY
window.READY = (async () => {
  const imgs = new Set(); SC.forEach(s => { shots(s).forEach(x => imgs.add(x.img)); (s.ui || []).forEach(u => u.sketch && imgs.add(u.sketch)); });
  // 优先高清底图 imgx_hd/，缺失时回退 imgx/
  const load = (n, dir) => new Promise(r => { const i = new Image(); i.onload = () => r(true); i.onerror = () => r(false); i.src = `${dir}/${n}.jpg`; });
  await Promise.all([...imgs].map(async n => { SRC[n] = (await load(n, "imgx_hd")) ? `imgx_hd/${n}.jpg` : (await load(n, "imgx"), `imgx/${n}.jpg`); }));
  await Promise.all(["Noto Serif SC", "Rye", "LongCang", "MaShan", "Elite", "JBM"].map(f => document.fonts.load(`40px "${f}"`, "字A")));
  await document.fonts.ready;
  for (const s of SC) for (const sh of shots(s)) {
    if (sh.clip) {
      const src = clipFrameSource(sh.clip, 0, window.CLIPS || {});
      await new Promise((resolve, reject) => {
        const img = new Image(); img.onload = resolve;
        img.onerror = () => reject(new Error(`Cannot load ${src}`)); img.src = src;
      });
    }
  }
  return true;
})();
const q = new URLSearchParams(location.search);
if (q.has("t")) window.READY.then(() => renderFrame(+q.get("t")));
if (q.has("play")) window.READY.then(() => { const t0 = performance.now() - (+q.get("play") || 0) * 1000; const f = async () => { await renderFrame((performance.now() - t0) / 1000); requestAnimationFrame(f); }; f(); });
