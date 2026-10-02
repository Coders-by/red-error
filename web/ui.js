// 所有 UI 组件：mk 建 DOM，up 按时间确定性更新（lt=本组件局部时间，total=持续时长，slt=场景局部时间）
const SVG = (w, h, inner, cls = "") => `<svg class="${cls}" viewBox="0 0 ${w} ${h}" width="100%" height="100%">${inner}</svg>`;
const STAR = SVG(100, 100, `<path d="M50 4 L61 38 L96 38 L68 59 L78 94 L50 73 L22 94 L32 59 L4 38 L39 38Z" fill="none" stroke="#c9a25a" stroke-width="3"/><circle cx="50" cy="52" r="10" fill="#a8201a"/>`);
const op = (e, v) => { e.style.opacity = v; };
const tf = (e, v) => { e.style.transform = v; };

UI.studio = {
  mk: () => el("div", "full", `<div class="star">${STAR}</div><div class="mk">HANDMADE&nbsp;STUDIOS</div><div class="sm">手 搓 工 作 室 &nbsp;出 品</div>`),
  up(e, u, lt, total) { op(e, vis(lt, total - .6, 1.6, 1.4)); tf(e.querySelector(".mk"), `scale(${1 + lt * .006})`); },
};

// 序章：极暗的西部现代场景做底；前两句克制淡入，第三句较快匀速打出（无光标、无键盘声），第四句淡入，停顿后末句整句显现
const PRO_AT = [0.5, 3.9, 7.4, 11.5, 15.7], PRO_CH = 1.7 / 22, PRO_TYPED = [2, 3];
UI.prologue = {
  mk(u) {
    const e = el("div", "full");
    u.lines.forEach((l, i) => {
      const p = el("p", i === u.lines.length - 1 ? "last" : "");
      if (PRO_TYPED.includes(i)) [...l].forEach(ch => p.appendChild(el("span", "", ch === " " ? "&nbsp;" : ch))); else p.textContent = l;
      e.appendChild(p);
    });
    return e;
  },
  up(e, u, lt, total) {
    const out = clamp((total - 1.6 - lt) / 1.6);
    FX.dim = 1 - .24 * sstep(lt / 3.5) * out;
    e.querySelectorAll("p").forEach((p, i) => {
      const t = lt - PRO_AT[i];
      if (PRO_TYPED.includes(i)) {
        const cs = p.children, n = cs.length;
        for (let j = 0; j < n; j++) op(cs[j], clamp((t - j * PRO_CH) / .06));
        op(p, out); return;
      }
      const k = sstep(t / (i === 4 ? 2.0 : 1.6));
      op(p, k * out); tf(p, `translateY(${(1 - k) * 6}px)`);
    });
  },
};

UI.chapter = {
  mk(u) {
    return el("div", "full", `<div class="num">${u.num}</div><div class="cn">${u.cn}</div><div class="rule"></div>
      <div class="en">${u.en}</div>${u.sub ? `<div class="sub">${u.sub}</div>` : ""}`);
  },
  up(e, u, lt, total) {
    const v = vis(lt, total, .5, 1.0); op(e, v);
    const cn = e.querySelector(".cn"), k = eout(lt / 1.6);
    tf(cn, `scale(${1.18 - .18 * k})`); cn.style.filter = `blur(${(1 - k) * 12}px)`; cn.style.letterSpacing = `${.35 - .2 * k}em`;
    e.querySelector(".rule").style.width = `${520 * eout((lt - .5) / 1.2)}px`;
    op(e.querySelector(".en"), clamp((lt - 1) / .8)); op(e.querySelector(".num"), clamp((lt - .2) / .8));
    const sb = e.querySelector(".sub"); if (sb) op(sb, clamp((lt - 2) / 1));
    FX.dim = .35 * v; FX.sub = false;
  },
};

const ICON_WARN = SVG(44, 44, `<path d="M22 3 L42 40 L2 40Z" fill="none" stroke="#a8201a" stroke-width="3"/><rect x="20" y="15" width="4" height="13" fill="#e9dfc8"/><rect x="20" y="31" width="4" height="4" fill="#e9dfc8"/>`);
UI.notify = {
  mk: (u) => el("div", "", `<div class="ic">${ICON_WARN}</div><div class="t">${u.title}</div><div class="b">${u.body}</div>`),
  up(e, u, lt, total) {
    const k = eout(lt / .5), o = clamp((total - lt) / .6);
    op(e, Math.min(k, o)); tf(e, `translateX(${(1 - k) * -60}px)`);
  },
};

UI.hud = {
  mk(u) {
    let roads = "";
    for (let i = 0; i < 9; i++) roads += `<path d="M${hash(i, 1) * 220} 0 Q ${hash(i, 2) * 220} 110 ${hash(i, 3) * 220} 220" stroke="rgba(220,210,190,.28)" stroke-width="${1 + hash(i, 4) * 3}" fill="none"/>`;
    return el("div", "", `<div class="loc">${u.loc}</div><div class="radar">${SVG(220, 220, `<g class="map">${roads}</g>
      <path class="sweep" d="M110 110 L110 0 A110 110 0 0 1 205 55 Z" fill="rgba(230,220,200,.12)"/>
      <circle cx="110" cy="110" r="8" fill="#e8dfcd"/><path d="M110 96 L117 114 L110 110 L103 114Z" fill="#111"/>
      <circle class="blip" cx="160" cy="70" r="5" fill="#c9a25a"/>`)}</div>`);
  },
  up(e, u, lt, total) {
    op(e, vis(lt, total, .8, .8));
    e.querySelector(".sweep").setAttribute("transform", `rotate(${lt * 60} 110 110)`);
    e.querySelector(".map").setAttribute("transform", `translate(0 ${(lt * 6) % 40 - 20})`);
    op(e.querySelector(".loc"), vis(lt, 5, .8, 1));
  },
};

UI.phone = {
  mk: (u) => el("div", "", `<div class="app"><i>头</i>${u.app}<em>现在</em></div><div class="tt">${u.title}</div><div class="bb">${u.body}</div>`),
  up(e, u, lt, total) { const k = eout(lt / .45); op(e, Math.min(k, clamp((total - lt) / .5))); tf(e, `translateY(${(1 - k) * -50}px)`); },
};

UI.journal = {
  mk(u) {
    return el("div", "", `<div class="book"><div class="pg paper"><div class="sk" style="background-image:url(${SRC[u.sketch] || `imgx/${u.sketch}.jpg`})"></div>
      <div class="skcap">营地的“篝火”</div></div><div class="pg paper"><div class="lines"></div><div class="date">${u.date}</div>
      ${u.text.map(t => `<div class="ln">${t}</div>`).join("")}</div></div>`);
  },
  up(e, u, lt, total) {
    const k = eout(lt / .9); op(e, Math.min(k, clamp((total - lt) / .8))); tf(e, `translateY(${(1 - k) * 80}px) rotate(${(1 - k) * -2}deg)`);
    op(e.querySelector(".sk"), .8 * clamp((lt - .6) / 1.5)); op(e.querySelector(".skcap"), clamp((lt - 1.5) / 1));
    op(e.querySelector(".date"), clamp((lt - 1) / .8));
    e.querySelectorAll(".ln").forEach((l, i) => {
      const st = 1.8 + i * 2.6, p = clamp((lt - st) / 2.3);
      l.style.clipPath = `inset(0 ${100 - p * 100}% 0 0)`;
    });
    FX.dim = .5 * k;
  },
};
const CODE_AI = `diff --git a/pay/refund.ts b/pay/refund.ts
@@ -12,9 +12,14 @@ export class RefundService {
-  async refund(id) {
+  async refund(id: OrderId): Promise<Result> {
+    const order = await this.repo.lock(id);
+    if (!order) return Err("NOT_FOUND");
+    return this.tx.run(async (t) => {
+      await t.ledger.reverse(order.payId);
✓ tests/refund.spec.ts   42 passed
✓ tests/ledger.spec.ts   31 passed`;
UI.chat = {
  mk: (u) => el("div", "", `<div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><b>Agent · 深夜会话</b></div>
    <div class="timer"></div><div class="body"><div class="me"></div><div class="ai"><div class="st"></div><div class="code"></div><div class="done"></div></div></div>`),
  up(e, u, lt, total, s, slt) {
    const close = clamp((slt - u.closeAt) / .4), k = eout(lt / .5);
    op(e, Math.min(k, 1 - close)); tf(e, `translateY(${(1 - k) * 40 + close * 30}px) scale(${1 - close * .04})`);
    const typed = Math.floor(u.prompt.length * clamp((lt - .1) / 3.2));
    e.querySelector(".me").textContent = u.prompt.slice(0, Math.max(1, typed)) + (lt < 3.7 && Math.floor(lt * 3) % 2 ? "▍" : "");
    op(e.querySelector(".me"), clamp(lt / .3));
    const run = lt > 3.7, done = lt > 8.7;
    op(e.querySelector(".ai"), run ? 1 : 0);
    const el_ = done ? 38 : Math.floor(clamp((lt - 3.7) / 5) * 38);
    e.querySelector(".timer").textContent = run ? `00:${String(el_).padStart(2, "0")}` : "";
    const frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    e.querySelector(".st").textContent = done ? "● 完成 · 耗时 38 秒" : `${frames[Math.floor(lt * 12) % 10]} 正在分析 14 个文件 · 生成测试…`;
    const lines = CODE_AI.split("\n"), n = Math.floor(lines.length * clamp((lt - 4) / 4.4));
    e.querySelector(".code").innerHTML = lines.slice(0, n).map(l => `<div style="color:${l[0] === "+" ? "#7ed49a" : l[0] === "-" ? "#f47067" : l[0] === "✓" ? "#7ed49a" : "#9fb3c8"}">${l.replace(/</g, "&lt;")}</div>`).join("");
    e.querySelector(".done").textContent = done ? "✓ 73 个测试全部通过 · 接口签名未变" : "";
  },
};

UI.photo = {
  mk: (u, s) => el("div", "", `<div class="ph" style="background-image:url(img_hd/${s.img}.jpg)"></div><div class="cap">${u.caption}</div>`),
  up(e, u, lt, total) {
    const k = eout(lt / 1.2); op(e, Math.min(k, clamp((total - lt) / 1.2)));
    tf(e, `translateY(${(1 - k) * 60}px) rotate(${-3 + (1 - k) * -4 + lt * .08}deg) scale(${1 + lt * .006})`);
    e.querySelector(".ph").style.filter = `sepia(.65) contrast(1.1) saturate(.7) brightness(${.4 + .6 * clamp(lt / 2)})`;
    FX.dim = .6 * k; FX.flash = lt < .25 ? .6 * (1 - lt / .25) : 0;
  },
};

UI.mission = {
  mk: (u) => el("div", "", `<div class="h">NEW MISSION</div><div class="t">${u.title}</div><div class="rule" style="color:#c9bfa9"></div>
    <ul>${u.goals.map((g, i) => `<li class="${i ? "g" : ""}">${g}</li>`).join("")}</ul>`),
  up(e, u, lt, total) {
    const k = eout(lt / .6); op(e, Math.min(k, clamp((total - lt) / .7))); tf(e, `translateX(${(1 - k) * 60}px)`);
    e.querySelectorAll("li").forEach((l, i) => op(l, clamp((lt - .7 - i * .5) / .4)));
  },
};

UI.duel = {
  mk: () => el("div", "full", `<div class="lab">HIGH&nbsp;NOON</div><div class="vs">
    <div class="side"><div class="n" style="color:#c9a25a">老 亚</div><div class="r">手写 · VIM · 15 年</div><div class="bar"><i class="a" style="background:#c9a25a"></i></div><div class="r pa"></div></div>
    <div class="clock"></div>
    <div class="side"><div class="n" style="color:#9fb3c8">AGENT-7</div><div class="r">自主编码 · 并行 × 64</div><div class="bar"><i class="b" style="background:#9fb3c8"></i></div><div class="r pb"></div></div></div>`),
  up(e, u, lt, total) {
    op(e, vis(lt, total, .3, .8));
    const a = eout(lt / (total - .8)) * .97 + (lt > total - 1 ? .03 : 0), b = clamp(lt / (total - .8)) * .94;
    e.querySelector(".a").style.width = a * 100 + "%"; e.querySelector(".b").style.width = b * 100 + "%";
    e.querySelector(".pa").textContent = `${Math.round(a * 100)}%  · 0 缺陷`;
    e.querySelector(".pb").textContent = `${Math.round(b * 100)}%  · 3 缺陷`;
    const h = 12 + Math.floor(lt * 40 / 60), m = Math.floor(lt * 40) % 60;
    e.querySelector(".clock").textContent = `${h}:${String(m).padStart(2, "0")}`;
    FX.dim = .45; FX.flash = lt < .3 ? .9 * (1 - lt / .3) : 0; FX.shake = lt < .5 ? 14 * (1 - lt / .5) : 0;
  },
};

const DE_CODE = [
  "function settle(order, now) {",
  "  const cutoff = new Date(order.date + ' 23:59');",
  "  if (now > cutoff) return close(order);",
  "  pool.forEach(async (tx) => {",
  "    balance += await tx.amount();",
  "  });",
  "  return order.user.wallet.credit(balance);",
  "}",
];
const DE_MARK = [{ l: 1, x: 900, tag: "时区" }, { l: 3, x: 760, tag: "并发" }, { l: 6, x: 900, tag: "空指针" }];
const XSVG = SVG(64, 64, `<path d="M8 8 L56 56 M56 8 L8 56" stroke="#ff3b2e" stroke-width="7" stroke-linecap="round"/>`);
UI.deadeye = {
  film: true,
  mk() {
    const e = el("div", "full");
    e.appendChild(el("div", "code", DE_CODE.map((c, i) => `<div class="ln"><span class="no">${i + 41}</span>${c.replace(/</g, "&lt;")}</div>`).join("")));
    DE_MARK.forEach(() => { e.appendChild(el("div", "x", XSVG)); e.appendChild(el("div", "tag")); });
    return e;
  },
  up(e, u, lt, total, s, slt) {
    const out = clamp((slt - (s.dur - 2.4)) / 1.2), inn = clamp(lt / 1.2), k = inn * (1 - out);
    op(e, k);
    FX.filter = `sepia(${.9 * k}) saturate(${1 + 1.4 * k}) hue-rotate(${-18 * k}deg) contrast(${1 + .35 * k}) brightness(${1 - .45 * k})`;
    const code = e.querySelector(".code"); tf(code, `translate(-60px, -150px) scale(${1 + slt * .004})`);
    const xs = e.querySelectorAll(".x"), tags = e.querySelectorAll(".tag");
    DE_MARK.forEach((m, i) => {
      const at_ = s.lines[i].st, p = clamp((slt - at_) / .18);
      const y = 210 - 150 + m.l * 25 * 1.85 - 18;
      xs[i].style.left = m.x - 60 + "px"; xs[i].style.top = y + "px";
      op(xs[i], p); tf(xs[i], `scale(${2.2 - 1.2 * eout(p)}) rotate(${(1 - p) * 40}deg)`);
      tags[i].textContent = m.tag; tags[i].style.left = m.x + 20 + "px"; tags[i].style.top = y + 14 + "px"; op(tags[i], clamp((slt - at_ - .15) / .3));
    });
    e.querySelectorAll(".ln").forEach((l, i) => {
      const hit = DE_MARK.findIndex(m => m.l === i);
      l.style.color = hit >= 0 && slt > s.lines[hit].st ? "#ffb4a6" : "";
    });
  },
};
const CI_ERR = ["TypeError: cannot read 'wallet' of undefined", "AssertionError: expected 2026-10-12T23:59+08 got …T15:59Z",
  "RaceCondition: balance mismatch 1200 != 1180", "Timeout: settle() exceeded 5000ms", "FAIL tests/settle.spec.ts (3 failed)"];
UI.ci = {
  mk: () => { const e = el("div", "", `<div class="hd"><b>agent-7 / order-system</b> · pipeline #auto-retry<span class="run"></span></div><div class="grid"></div><div class="log"></div><div class="big"></div>`);
    const g = e.querySelector(".grid"); for (let i = 0; i < 101; i++) g.appendChild(el("i")); return e; },
  up(e, u, lt, total) {
    const k = eout(lt / .5); op(e, Math.min(k, clamp((total - lt + .8) / .6))); tf(e, `scale(${.96 + .04 * k})`);
    const n = Math.min(101, Math.floor(101 * Math.pow(clamp((lt - .2) / 6.3), .8)));
    e.querySelectorAll(".grid i").forEach((c, i) => { c.className = i < n ? (i === 100 ? "p" : hash(i, 3) > .8 ? "w" : "f") : ""; });
    e.querySelector(".run").textContent = `RUN ${String(Math.max(1, n)).padStart(3, "0")} / ∞`;
    const lg = []; for (let i = Math.max(0, n - 9); i < n; i++) lg.push(i === 100 ? `<div class="ok">run #101  ✓ ALL TESTS PASSED  ·  0 defects  ·  time 00:00:41</div>` : `<div>run #${String(i + 1).padStart(3, "0")}  <span class="e">✗ ${CI_ERR[Math.floor(hash(i, 5) * 5)]}</span></div>`);
    e.querySelector(".log").innerHTML = lg.join("");
    e.querySelector(".big").textContent = n >= 101 ? "✓ PASSED · 第 101 次" : "";
    FX.dim = .55 * k;
  },
};

const MEDAL = (c) => SVG(150, 150, `<path d="M45 0 L65 55 L85 55 L105 0Z" fill="#6b1d18"/><circle cx="75" cy="95" r="50" fill="${c}" stroke="#fff6" stroke-width="3"/>
  <circle cx="75" cy="95" r="38" fill="none" stroke="#0005" stroke-width="3"/><path d="M75 68 L82 88 L103 88 L86 100 L92 121 L75 108 L58 121 L64 100 L47 88 L68 88Z" fill="#0004"/>`);
UI.complete = {
  mk: (u) => el("div", "full", `<div class="band"></div><div class="ttl">任 务 完 成</div><div class="mn">${u.title}</div><div class="rule"></div>
    <div class="medal">${MEDAL("#b9bcc0")}</div><div class="note">${u.medal} · ${u.note}</div>`),
  up(e, u, lt, total) {
    op(e, vis(lt, total, .4, .9)); const m = e.querySelector(".medal"), p = eout((lt - .8) / .6);
    op(m, p); tf(m, `scale(${1.6 - .6 * p}) rotate(${(1 - p) * -30}deg)`);
    e.querySelector(".rule").style.width = 700 * eout((lt - .3) / .8) + "px";
  },
};

UI.hr = {
  mk: () => el("div", "paper", `<div class="hd"><span>人力资源系统 · 自动评估</span><span>机密</span></div><h3>员工能力档案</h3><div class="id">EMP-00427 · 入职 2011.03</div>
    <table><tr><td>姓名</td><td>亚 · 摩根</td></tr><tr><td>职级</td><td>资深工程师 P7</td></tr><tr><td>司龄</td><td>15 年</td></tr>
    <tr><td>技能栈</td><td class="sk"><span>C</span><span>Vim</span><span>手写 SQL</span><span>Makefile</span><span>画图</span></td></tr>
    <tr><td>AI 协作指数</td><td style="font-family:var(--mono)">0.03 / 1.00</td></tr><tr><td>系统建议</td><td>岗位优化</td></tr></table>
    <div class="stamp">遗 产<small>LEGACY</small></div>`),
  up(e, u, lt, total, s, slt) {
    const k = eout(lt / .8); op(e, Math.min(k, clamp((total - lt) / .8))); tf(e, `translateY(${(1 - k) * 50}px) rotate(1.5deg)`);
    const st = e.querySelector(".stamp"), p = clamp((slt - u.stampAt) / .12);
    op(st, p > 0 ? .9 : 0); tf(st, `rotate(-12deg) scale(${2.4 - 1.4 * p})`);
    if (slt > u.stampAt && slt < u.stampAt + .25) FX.shake = 10;
  },
};

const BB = [
  { t: "AI 员工 · 永不下班", s: "AGENT CLOUD", c: "#2de2e6", x: 80, y: 180, f: 64, d: 0 },
  { t: "一个人 = 一家公司", s: "超级个体计划", c: "#ff3b6b", x: 1180, y: 230, f: 58, d: 1.2 },
  { t: "代码？交给它", s: "一键生成 · 一键上线", c: "#f6c343", x: 200, y: 560, f: 52, d: 3.2 },
  { t: "效率 ×100", s: "AUTOPILOT 7", c: "#7b61ff", x: 1250, y: 610, f: 72, d: 5 },
  { t: "你还在手写代码吗？", s: "别让手艺拖累你", c: "#ff8a3d", x: 640, y: 170, f: 56, d: 7.5 },
  { t: "LEGACY → CLOUD", s: "遗产系统迁移 · 限时 0 元", c: "#2de2e6", x: 1100, y: 420, f: 50, d: 9.5 },
];
UI.billboards = {
  mk: () => { const e = el("div", "full"); BB.forEach(b => e.appendChild(el("div", "bb", `${b.t}<small>${b.s}</small>`))); return e; },
  up(e, u, lt, total) {
    e.querySelectorAll(".bb").forEach((d, i) => {
      const b = BB[i], p = lt - b.d, v = vis(p, 4.2, .3, .8), fl = hash(Math.floor(lt * 24), i) > .93 ? .4 : 1;
      op(d, v * fl); d.style.left = b.x - p * 30 + "px"; d.style.top = b.y + "px"; d.style.fontSize = b.f + "px"; d.style.color = b.c;
      d.style.border = `2px solid ${b.c}`; d.style.textShadow = `0 0 18px ${b.c}, 0 0 40px ${b.c}`; d.style.boxShadow = `0 0 30px ${b.c}55, inset 0 0 20px ${b.c}33`;
      tf(d, `perspective(900px) rotateY(${(i % 2 ? -1 : 1) * 14}deg) scale(${1 + p * .03})`);
    });
  },
};

UI.quote = {
  mk: (u) => el("div", "full", `<p>${u.text[0]}</p><div class="rule"></div><p>${u.text[1]}</p>`),
  up(e, u, lt, total, s) {
    const ps = e.querySelectorAll("p"), l2 = s.lines[1].st - s.lines[0].st;
    op(ps[0], clamp(lt / 1) * clamp((total - lt) / 1)); op(ps[1], clamp((lt - l2) / 1) * clamp((total - lt) / 1));
    ps.forEach((p, i) => p.style.filter = `blur(${(1 - clamp((lt - i * l2) / 1)) * 8}px)`);
    e.querySelector(".rule").style.width = 600 * eout((lt - .5) / 1.5) + "px";
    FX.dim = .5 * clamp(lt); FX.sub = false;
  },
};

UI.im = {
  mk: () => el("div", "", `<div class="top">科尔特手艺人（5）</div><div class="msgs">
    <div class="sys">凌晨 02:14</div>
    <div class="m me"><div class="av" style="background:#9a9a6a">米</div><div><div class="bub file"><i></i><div>手艺人方法论_全部源码.zip<br><span style="color:#666;font-size:15px">2.4 GB</span></div></div></div></div>
    <div class="m me"><div class="av" style="background:#9a9a6a">米</div><div class="bub">已发给米尔顿先生。用来训练 Agent-8，效果应该不错。</div></div>
    <div class="sys">“米卡”撤回了一条消息</div>
    <div class="m"><div class="av" style="background:#c47f8f">萨</div><div><div class="nm">萨姐</div><div class="bub">？？？</div></div></div>
    </div><div class="warn">⚠ 仓库权限变更：外部账号 milton@efficiency.ai 已获得读取权限</div>`),
  up(e, u, lt, total) {
    const k = eout(lt / .6); op(e, Math.min(k, clamp((total - lt) / .6))); tf(e, `translateY(${(1 - k) * 50}px)`);
    const it = e.querySelectorAll(".msgs > *"); const ts = [0, .5, 3.1, 4.2, 5.2];
    it.forEach((m, i) => { const p = eout((lt - ts[i]) / .3); op(m, p); tf(m, `translateY(${(1 - p) * 14}px)`); });
    const w = e.querySelector(".warn"), p = eout((lt - 5.7) / .4); tf(w, `translateY(${(1 - p) * 100}%)`);
    if (lt > 5.7 && lt < 7.8) FX.filter = `saturate(.9) contrast(1.06) sepia(.12) hue-rotate(${Math.sin(lt * 12) > 0 ? -8 : 0}deg)`;
  },
};
// 终端逐字打出：segs = [{at, text, cls?, speed?}]
function termRender(segs, lt) {
  let html = "", last = 0;
  for (const g of segs) {
    if (lt < g.at) break;
    const n = g.instant ? g.text.length : Math.floor((lt - g.at) * (g.speed || 18));
    const s = g.text.slice(0, n).replace(/</g, "&lt;");
    html += g.cls ? `<span class="${g.cls}">${s}</span>` : s; last = g.at;
  }
  return html + (Math.floor(lt * 2.2) % 2 ? `<span class="cur"></span>` : `<span class="cur" style="opacity:0"></span>`);
}
const COMMIT = [
  { at: 0.1, text: "~/colter/order-system ", cls: "pr", instant: 1 }, { at: 0.1, text: "$ ", cls: "pr", instant: 1 },
  { at: 0.4, text: "git add -A && git commit -m \"final: thank you, old friend\"\n", speed: 13 },
  { at: 4.8, text: "[main 7a3f2e1] final: thank you, old friend\n 42 files changed, 15 years inserted(+), 0 deletions(-)\n", cls: "d", instant: 1 },
  { at: 5.6, text: "~/colter/order-system ", cls: "pr", instant: 1 }, { at: 5.6, text: "$ ", cls: "pr", instant: 1 },
  { at: 6.0, text: "git push\n", speed: 8 },
  { at: 7.5, text: "Enumerating objects: 15 years, done.\nWriting objects: 100% ", cls: "d", instant: 1 },
  { at: 7.9, text: "████████████████████", cls: "g", speed: 30 },
  { at: 8.8, text: "\nTo colter:order-system.git\n   e4d9a01..7a3f2e1  main -> main\n\n", cls: "g", instant: 1 },
  { at: 9.6, text: "# 老伙计，辛苦了。", cls: "y", speed: 6 },
];
UI.commit = {
  mk: () => el("div", ""),
  up(e, u, lt, total) { const k = eout(lt / .6); op(e, Math.min(k, clamp((total - lt) / 1))); e.innerHTML = termRender(COMMIT, lt); FX.dim = .5 * k; },
};
const HANDC = [
  { at: 0.3, text: "// 这一行，我自己写。\n", cls: "c", speed: 9 },
  { at: 2.6, text: "function ", cls: "k", speed: 20 }, { at: 3.0, text: "settle(order, now) {\n", speed: 16 },
  { at: 4.3, text: "  const ", cls: "k", speed: 20 }, { at: 4.6, text: "tz = order.user.tz ?? ", speed: 16 }, { at: 6.0, text: "'Asia/Shanghai'", cls: "s", speed: 16 },
  { at: 7.0, text: ";\n  // 老亚教的：先想清楚时区，再谈效率\n", cls: "c", speed: 18 },
];
UI.handcode = {
  mk: () => { const e = el("div", ""); e.innerHTML = `<div class="bar">settle.ts — 手写模式</div><div class="tx" style="margin-top:36px"></div><div class="ai">AI 建议已关闭 · Tab 补全 0 次</div>`; return e; },
  up(e, u, lt, total) { const k = eout(lt / .8); op(e, Math.min(k, clamp((total - lt) / 1))); e.querySelector(".tx").innerHTML = termRender(HANDC, lt); FX.dim = .35 * k; },
};
UI.dash = {
  mk: () => el("div", "", `<h4>比彻之希工作室 · 本周</h4>
    <div class="row">Agent 自动化任务<b>1,284</b></div><div class="row">人工 Review 通过<b>97.6%</b></div>
    <div class="row">支付 / 结算核心模块<span class="pill h">手写 · 马迭代</span></div><div class="row">线上事故<b>0</b></div>`),
  up(e, u, lt, total) {
    const k = eout(lt / .7); op(e, Math.min(k, clamp((total - lt) / .7))); tf(e, `translateY(${(1 - k) * 40}px)`);
    e.querySelectorAll(".row").forEach((r, i) => op(r, clamp((lt - .5 - i * .5) / .4)));
  },
};
UI.finale = {
  mk: () => el("div", "full", `<p>古法已死。</p><p>手艺永存。</p>`),
  up(e, u, lt, total) { const ps = e.querySelectorAll("p"); ps.forEach((p, i) => { const k = clamp((lt - i * 2) / 1.5); op(p, k * clamp((total - .5 - lt) / 1)); p.style.filter = `blur(${(1 - k) * 10}px)`; }); FX.sub = false; },
};
UI.logo = {
  mk: () => el("div", "full", `<div class="red">红色报错</div><div class="rd">REDEMPTION</div><div class="rule" style="width:640px;color:#a8201a;margin-top:18px"></div><div class="two">救 赎</div>`),
  up(e, u, lt, total) {
    op(e, vis(lt, total - .4, .05, 1.5)); const r = e.querySelector(".red"), p = eout(lt / .35);
    tf(r, `scale(${1.5 - .5 * p})`); r.style.filter = `blur(${(1 - p) * 8}px)`;
    tf(e.querySelector(".rd"), `translateY(${(1 - eout((lt - .4) / 1)) * 20}px)`); op(e.querySelector(".rd"), clamp((lt - .4) / 1));
    op(e.querySelector(".two"), clamp((lt - 1.2) / 1)); FX.shake = lt < .4 ? 18 * (1 - lt / .4) : 0;
  },
};
const CREDITS = [
  ["一部致敬《荒野大镖客：救赎 2》的 AI 短片", ""],
  ["老亚", "亚 · 摩根"], ["达总", "达奇 · 范德林"], ["马迭代", "阿迭"], ["米卡", "米卡 · 贝尔"], ["萨姐", "萨迪 · 阿德勒"], ["效率审计", "米尔顿先生"],
  ["老伙计", "一把用了十五年的机械键盘"],
  ["音乐", "Kevin MacLeod (incompetech.com)<small>Pale Rider · Western Streets · Porch Blues · Heavy Heart · Smoking Gun · Cowboy Sting</small>"],
  ["", "<small>Anguish · Neo Western · Crossing the Divide · The Parting · Long Road Ahead · Pennsylvania Rose</small>"],
  ["", "<small>Licensed under Creative Commons: By Attribution 4.0</small>"],
  ["画面", "AI 生成 · Flux"], ["声音", "本片为默片 · 音效程序化合成"],
  ["特别感谢", "所有仍在手写代码的人"],
];
UI.credits = {
  mk: () => { const e = el("div", "full"); e.appendChild(el("div", "roll", CREDITS.map(([r, n]) => `<div class="blk"><div class="r">${r}</div><div class="n">${n}</div></div>`).join(""))); return e; },
  up(e, u, lt, total) { op(e, vis(lt, total, 1, 1.5)); const roll = e.querySelector(".roll"); tf(roll, `translateY(${1080 - (roll.offsetHeight + 1080) * (lt / total) * .98}px)`); FX.sub = false; },
};
UI.egg = {
  mk: () => el("div", ""),
  up(e, u, lt, total) { FX.dim = .55 * clamp(lt / 1.5); },
};

// ——— 默片版新增 ———
// 冷开场：锁屏上不断堆叠的告警
const ALERTS = [
  ["监控告警", "P0 · 支付服务 5xx 错误率 38%"], ["监控告警", "P0 · 订单服务 响应超时"], ["萨姐", "谁在线？？"],
  ["监控告警", "P0 · 数据库连接池耗尽"], ["达总", "未接来电 (3)"], ["监控告警", "P0 · 回滚失败"], ["米卡", "完了"]];
const ALERT_T = [.4, 1.6, 2.6, 3.4, 4.0, 4.6, 5.1];
UI.alerts = {
  mk: () => el("div", "", `<div class="tm">02:14</div><div class="dt">10月9日 星期五</div><div class="st"></div>`),
  up(e, u, lt, total) {
    op(e, vis(lt, total, .4, .5));
    const st = e.querySelector(".st"), n = ALERT_T.filter(x => lt >= x).length;
    if (st.childElementCount !== n) st.innerHTML = ALERTS.slice(0, n).reverse().map(([a, b], i) =>
      `<div class="al${a === "监控告警" ? " p0" : ""}"><i>${a === "监控告警" ? "!" : a[0]}</i><div><b>${a}</b><span>${b}</span></div><em>现在</em></div>`).join("");
    const k = n ? eout((lt - ALERT_T[n - 1]) / .3) : 0, f = st.firstChild;
    if (f) { tf(f, `translateY(${(1 - k) * -30}px) scale(${.96 + .04 * k})`); op(f, k); }
    FX.shake = n && lt - ALERT_T[n - 1] < .25 ? 3 : 0;
  },
};
// 右上角时间戳，按场景时间跳变
UI.clock = {
  mk: () => el("div", "", `<span></span>`),
  up(e, u, lt, total, s, slt) {
    let m = u.marks[0], i0 = 0; u.marks.forEach((x, i) => { if (slt >= x[0]) { m = x; i0 = i; } });
    const k = clamp((slt - m[0]) / .15);
    e.firstChild.textContent = m[1]; op(e, vis(lt, total, .3, .6) * (i0 ? k : 1));
  },
};
// RDR2 式人物登场卡
UI.name = {
  mk: (u) => el("div", "", `<div class="n">${u.n}</div><div class="rl"></div>${u.r.map(x => `<div class="r">${x}</div>`).join("")}`),
  up(e, u, lt, total) {
    const k = eout(lt / .5); op(e, Math.min(k, clamp((total - lt) / .5)));
    tf(e.querySelector(".n"), `translateX(${(1 - k) * 24}px)`);
    e.querySelector(".rl").style.width = 220 * eout((lt - .15) / .6) + "px";
    e.querySelectorAll(".r").forEach((r, i) => op(r, clamp((lt - .4 - i * .3) / .4)));
  },
};
// 孩子一个键一个键地敲
// 拼音输入：每个键后的 [已上屏, 组字中]；与 scenes.js ep_c 的 key 音效一一对应（UI 时间 +1.0）
const KID_T = [.8, 1.5, 2.4, 3.0, 3.6, 4.4, 5.2, 5.9, 6.4, 6.9, 7.5, 8.0, 8.5, 9.2];
const KID_S = [["", "n"], ["", "ni"], ["", "nih"], ["", "niha"], ["", "nihao"], ["你好", ""], ["你好，", ""],
  ["你好，", "s"], ["你好，", "sh"], ["你好，", "shi"], ["你好，", "shij"], ["你好，", "shiji"], ["你好，", "shijie"], ["你好，世界", ""]];
UI.kidtype = {
  mk: () => el("div", "", `<div class="ln"><span class="p">1</span><span class="tx"></span><span class="py"></span><span class="cur"></span></div><div class="ln l2"><span class="p">2</span><span class="tx2"></span></div>`),
  up(e, u, lt, total) {
    op(e, clamp(lt / .8) * clamp((total - lt) / 1));
    const n = KID_T.filter(x => lt >= x).length, [done, py] = n ? KID_S[n - 1] : ["", ""];
    e.querySelector(".tx").textContent = done; e.querySelector(".py").textContent = py;
    op(e.querySelector(".cur"), Math.floor(lt * 2.2) % 2 && lt < 10 ? 1 : 0);
    op(e.querySelector(".l2"), lt >= 10 ? 1 : 0);
    FX.dim = .25 * clamp(lt / 1);
  },
};
