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
const DEF_KB = [0.5, 0.5, 1.04, 0.5, 0.5, 1.12];
function shots(s) {
  if (!s.img) return [];
  const a = [{ t: 0, img: s.img, kb: s.kb || DEF_KB }];
  (s.alt || []).forEach(x => a.push({ t: x.at, img: x.img, kb: x.kb || s.kb || DEF_KB }));
  return a.map((x, i) => ({ ...x, end: i + 1 < a.length ? a[i + 1].t : s.dur }));
}
function kbTransform(sh, lt, sd) {
  const k = sh.kb, span = Math.max(1, sd - sh.t), p = clamp((lt - sh.t) / span);
  const q = p * p * (3 - 2 * p) * .6 + p * .4;
  const x = lerp(k[0], k[3], q), y = lerp(k[1], k[4], q), sc = Math.max(1.02, lerp(k[2], k[5], q)) * 1.02;
  return `translate(${(0.5 - x) * W * (sc - 1)}px, ${(0.5 - y) * H * (sc - 1)}px) scale(${sc})`;
}
function setLayer(id, sh, lt, sd, op) {
  const L = $(id), img = L.firstChild;
  if (!sh || op <= 0) { L.style.opacity = 0; return; }
  const src = `imgx/${sh.img}.jpg`;
  if (img.getAttribute("src") !== src) img.setAttribute("src", src);
  img.style.transform = kbTransform(sh, lt, sd);
  L.style.opacity = op;
}

// ——— 粒子特效 ———
const fxc = $("#fx").getContext("2d");
function drawFx(type, t, lt) {
  fxc.clearRect(0, 0, W, H);
  if (!type) return;
  const g = fxc;
  if (type === "snow" || type === "snowglass") {
    for (let i = 0; i < 520; i++) {
      const z = hash(i, 1), sp = 40 + z * 170, r = .8 + z * z * 3.8;
      const x = ((hash(i, 2) * W + t * (60 + 90 * z) + Math.sin(t * .7 + i) * 30 * z) % (W + 40) + W + 40) % (W + 40) - 20;
      const y = ((hash(i, 3) * H + t * sp) % (H + 20)) - 10;
      g.globalAlpha = .25 + z * .6; g.fillStyle = "#fff";
      g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    }
    if (type === "snowglass") glass(g, t, "#dfe8f0", 60);
  } else if (type === "rain" || type === "rainglass") {
    g.strokeStyle = "#bcc8d4"; g.lineWidth = 1.2;
    for (let i = 0; i < 600; i++) {
      const z = hash(i, 1), sp = 1400 + z * 900, len = 18 + z * 40;
      const x = (hash(i, 2) * (W + 200) + t * 180) % (W + 200) - 100, y = (hash(i, 3) * (H + 200) + t * sp) % (H + 200) - 100;
      g.globalAlpha = .12 + z * .35; g.beginPath(); g.moveTo(x, y); g.lineTo(x - len * .14, y - len); g.stroke();
    }
    if (type === "rainglass") glass(g, t, "#a8b8c8", 90);
  } else if (type === "embers") {
    for (let i = 0; i < 90; i++) {
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
    for (let i = 0; i < 160; i++) {
      const z = hash(i, 1);
      const x = (hash(i, 2) * W + t * (20 + z * 60)) % W, y = hash(i, 3) * H + Math.sin(t * .5 + i) * 20;
      g.globalAlpha = (.15 + z * .45) * (.6 + .4 * Math.sin(t * 2 + i)); g.fillStyle = "#f3d9a4";
      g.beginPath(); g.arc(x, y, .6 + z * 1.8, 0, 7); g.fill();
    }
    haze(g, t, "rgba(230,170,90,", .09);
  } else if (type === "neon") {
    const cols = ["#ff3b6b", "#2de2e6", "#f6c343", "#7b61ff", "#ff8a3d"];
    for (let i = 0; i < 40; i++) {
      const z = hash(i, 1), x = (hash(i, 2) * W - t * (80 + z * 260)) % W, xx = x < 0 ? x + W : x, y = H * (.1 + hash(i, 3) * .55), r = 12 + z * 50;
      const gr = g.createRadialGradient(xx, y, 0, xx, y, r);
      gr.addColorStop(0, cols[i % 5] + "66"); gr.addColorStop(1, cols[i % 5] + "00");
      g.globalAlpha = .7; g.fillStyle = gr; g.fillRect(xx - r, y - r, r * 2, r * 2);
    }
  } else if (type === "mist") {
    haze(g, t, "rgba(255,225,190,", .16);
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
const GRAINS = [...Array(6)].map((_, k) => {
  const c = document.createElement("canvas"); c.width = 480; c.height = 204;
  const x = c.getContext("2d"), d = x.createImageData(480, 204);
  for (let i = 0; i < d.data.length; i += 4) { const v = 128 + (hash(i, k + 20) - .5) * 150; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
  x.putImageData(d, 0, 0); return c;
});
function drawGrain(t) {
  const k = Math.floor(t * FPS) % GRAINS.length;
  gc.imageSmoothingEnabled = false; gc.drawImage(GRAINS[k], 0, 0, W, H);
  // 偶发划痕与闪烁
  const f = Math.floor(t * FPS);
  if (hash(f, 3) > .93) { gc.fillStyle = "rgba(255,255,255,.5)"; gc.fillRect(hash(f, 4) * W, 0, 1.5, H); }
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

// ——— 字幕 ———
const subEl = $("#sub"), whoEl = subEl.querySelector(".who"), txtEl = subEl.querySelector(".txt");
function drawSub(s, lt) {
  let cur = null;
  for (const l of s.lines || []) if (lt >= l.st - .08 && lt <= l.en + .45) cur = l;
  if (!cur || !FX.sub) { subEl.style.opacity = 0; return; }
  const op = Math.min(clamp((lt - cur.st + .08) / .2), clamp((cur.en + .45 - lt) / .2));
  whoEl.textContent = cur.who + "："; whoEl.style.color = (TL.CAST[cur.who] || {}).color || "#ccc";
  txtEl.textContent = cur.t; txtEl.style.fontStyle = cur.vo ? "italic" : "normal";
  txtEl.style.color = cur.vo ? "#d9d2c3" : "#f4f0e8";
  subEl.style.opacity = op;
}

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

  // 画面：当前镜头（上层 B）+ 前一镜头（下层 A）交叉溶解
  const sh = shots(s); let ci = -1; sh.forEach((x, i) => { if (lt >= x.t) ci = i; });
  const cur = sh[ci];
  let prev = null, prevS = s, since = 0;
  if (cur) {
    since = lt - cur.t;
    if (ci > 0) prev = sh[ci - 1];
    else if (si > 0 && SC[si - 1].img) { prevS = SC[si - 1]; const ps = shots(prevS); prev = ps[ps.length - 1]; }
  }
  const k = cur ? clamp(since / XF) : 0;
  if (prev && k < 1) setLayer("#imgA", prev, prevS === s ? lt : prevS.dur + lt, prevS.dur, 1); else setLayer("#imgA", null);
  setLayer("#imgB", cur, lt, s.dur, cur ? (prev ? ease(k) : clamp(since / 1.2)) : 0);

  drawFx(s.fx, t, lt);
  drawGrain(t);

  const grade = s.grade === "bleach" ? "saturate(.25) contrast(1.25) brightness(1.18) sepia(.2)" : "saturate(.9) contrast(1.06) sepia(.12)";
  $("#film").style.filter = (FX.filter || grade) + (FX.dim ? ` brightness(${1 - FX.dim})` : "");
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

// 预加载字体与图片，完成后置 window.READY
window.READY = (async () => {
  const imgs = new Set(); SC.forEach(s => { shots(s).forEach(x => imgs.add(x.img)); (s.ui || []).forEach(u => u.sketch && imgs.add(u.sketch)); });
  await Promise.all([...imgs].map(n => new Promise(r => { const i = new Image(); i.onload = i.onerror = r; i.src = `imgx/${n}.jpg`; })));
  await Promise.all(["Noto Serif SC", "Rye", "LongCang", "MaShan", "Elite", "JBM"].map(f => document.fonts.load(`40px "${f}"`, "字A")));
  await document.fonts.ready;
  return true;
})();
const q = new URLSearchParams(location.search);
if (q.has("t")) window.READY.then(() => setTime(+q.get("t")));
if (q.has("play")) window.READY.then(() => { const t0 = performance.now() - (+q.get("play") || 0) * 1000; const f = () => { setTime((performance.now() - t0) / 1000); requestAnimationFrame(f); }; f(); });
