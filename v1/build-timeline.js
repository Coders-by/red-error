// 由 scenes.js + TTS 时长 → 计算全片时间轴（绝对秒），输出 web/timeline.js 与 audio/timeline.json
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
const { SCENES, CAST } = require(path.join(ROOT, "web/scenes.js"));
const DUR = JSON.parse(fs.readFileSync(path.join(ROOT, "audio/tts/durations.json")));

const LEAD = 1.0, GAP = 0.5, TAIL = 1.6;
let T = 0;
const out = [];
for (const s of SCENES) {
  const lines = [];
  let cur = 0;
  (s.lines || []).forEach((ln, i) => {
    const key = `${s.id}_${i + 1}`;
    const st = cur + (ln.gap ?? (i === 0 ? LEAD : GAP));
    const d = DUR[key];
    lines.push({ ...ln, key, st, en: st + d });
    cur = st + d;
  });
  const dur = Math.max(s.min, lines.length ? cur + TAIL : 0);
  const ref = (v) => {
    if (typeof v === "number") return v;
    let m = /^L(\d+)(e?)([+-][\d.]+)?$/.exec(v);
    if (m) { const l = lines[+m[1] - 1]; return (m[2] ? l.en : l.st) + (+m[3] || 0); }
    m = /^end([+-][\d.]+)?$/.exec(v);
    if (m) return dur + (+m[1] || 0);
    throw new Error(`bad ref ${v} in ${s.id}`);
  };
  out.push({ ...s, t0: T, dur, lines,
    ui: (s.ui || []).map(u => ({ ...u, at: ref(u.at), ...(u.closeAt != null && { closeAt: ref(u.closeAt) }), ...(u.stampAt != null && { stampAt: ref(u.stampAt) }) })),
    sfx: (s.sfx || []).map(x => ({ ...x, at: ref(x.at) })) });
  T += dur;
}
// hud until → 绝对结束时间
const byId = Object.fromEntries(out.map(s => [s.id, s]));
for (const s of out) for (const u of s.ui) if (u.until) u.untilAbs = byId[u.until].t0 + byId[u.until].dur;

const TOTAL = T;
// 各段落起止（绝对秒）
const secSpan = {};
for (const s of out) { const a = secSpan[s.sec] ||= [s.t0, 0]; a[1] = s.t0 + s.dur; }
const sceneAt = (id, off = 0) => byId[id].t0 + off;
const sceneEnd = (id, off = 0) => byId[id].t0 + byId[id].dur + off;

// BGM 编排：file, from, to (绝对), offset (曲内起点), vol, fin, fout
const BGM = [
  { f: "Pale Rider", from: sceneAt("p_logo", 1.5), to: sceneEnd("p_title", 2), off: 0, vol: 0.55, fin: 4, fout: 4 },
  { f: "Western Streets", from: sceneAt("c1_card"), to: sceneEnd("c1_e", 1), off: 0, vol: 0.42, fin: 2, fout: 4 },
  { f: "Porch Blues", from: sceneAt("c2_card"), to: sceneEnd("c2_c", 0), off: 0, vol: 0.40, fin: 2, fout: 4 },
  { f: "Heavy Heart", from: sceneAt("c2_d", 0), to: sceneEnd("c2_e", 1.5), off: 8, vol: 0.40, fin: 4, fout: 4 },
  { f: "Smoking Gun", from: sceneAt("c3_card"), to: sceneEnd("c3_b", -0.2), off: 0, vol: 0.55, fin: 1, fout: 0.3 },
  { f: "Smoking Gun", from: sceneAt("c3_d", 3), to: sceneEnd("c3_d", 0), off: 60, vol: 0.35, fin: 3, fout: 1 },
  { f: "Cowboy Sting", from: sceneAt("c3_e", 0.2), to: sceneAt("c3_e", 8.5), off: 0, vol: 0.6, fin: 0.05, fout: 1.5 },
  { f: "Anguish", from: sceneAt("c4_card"), to: sceneEnd("c4_b", 1), off: 0, vol: 0.45, fin: 3, fout: 4 },
  { f: "Neo Western", from: sceneAt("c5_card"), to: sceneEnd("c5_b", 0.5), off: 0, vol: 0.5, fin: 2, fout: 3 },
  { f: "Crossing the Divide", from: sceneAt("c5_c", -1), to: sceneEnd("c5_d", 1), off: 66, vol: 0.45, fin: 3, fout: 4 },
  { f: "The Parting", from: sceneAt("c6_card"), to: sceneEnd("c6_d", 0.5), off: 0, vol: 0.45, fin: 3, fout: 3 },
  { f: "Long Road Ahead", from: sceneAt("c6_e", 0), to: sceneEnd("c6_f", 0), off: 0, vol: 0.55, fin: 3, fout: 3 },
  { f: "Pennsylvania Rose", from: sceneAt("ep_card"), to: sceneEnd("ep_logo", 0), off: 0, vol: 0.45, fin: 2, fout: 2 },
  { f: "Pale Rider", from: sceneAt("ep_credits"), to: sceneEnd("ep_credits", 1), off: 0, vol: 0.5, fin: 2, fout: 4 },
];

const data = { TOTAL, scenes: out, CAST, BGM };
fs.writeFileSync(path.join(ROOT, "web/timeline.js"), "window.TL=" + JSON.stringify(data) + ";");
fs.writeFileSync(path.join(ROOT, "audio/timeline.json"), JSON.stringify(data, null, 1));
for (const s of out) console.log(s.id.padEnd(11), s.t0.toFixed(1).padStart(6), s.dur.toFixed(1).padStart(5), s.dur > s.min + 0.01 ? "(+" + (s.dur - s.min).toFixed(1) + ")" : "");
console.log("TOTAL", TOTAL.toFixed(1), "s =", (TOTAL / 60).toFixed(2), "min");
