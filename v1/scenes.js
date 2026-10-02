// 《红色报错：救赎》分镜数据 —— 构建脚本(Node) 与 渲染页(浏览器) 共用
// at: 秒数 | "L2" 第2句开始 | "L2e" 第2句结束 | "end-3" 场景结束前3秒
const SCENES = [
  // ───────── 序幕 ─────────
  { id: "p_logo", sec: "prologue", min: 7, img: null, amb: "wind", ambVol: 0.25,
    ui: [{ type: "studio", at: 0.8 }] },
  { id: "p_title", sec: "prologue", min: 25, img: null, amb: "wind", ambVol: 0.35,
    ui: [{ type: "prologue", at: 0.5, lines: [
      "2026 年。",
      "古法与手搓的时代，已经走到尽头。",
      "大模型接管了键盘，Agent 在深夜里悄无声息地提交代码。",
      "那些不肯放下手艺的人，正在被效率一个一个追上。",
      "有的人选择反抗，有的人选择逃离，",
      "还有少数人……",
      "仍在手写每一行代码。"] }] },

  // ───────── 第一章 寒冬 ─────────
  { id: "c1_card", sec: "ch1", min: 5.5, img: "blizzard_van",
    ui: [{ type: "chapter", at: 0, num: "第 一 章", cn: "寒 冬", en: "CHAPTER I  ·  COLTER" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c1_a", sec: "ch1", min: 9, img: "blizzard_van", kb: [0.5, 0.55, 1.0, 0.5, 0.5, 1.12], fx: "snow", amb: "wind", ambVol: 0.8,
    sfx: [{ at: 0, name: "engine", vol: 0.5 }],
    lines: [
      { who: "老亚", vo: true, t: "黑水那一晚之后，我们就一直在逃。" },
      { who: "老亚", vo: true, t: "一次手写代码的上线，从凌晨两点，一直崩到了天亮。" }],
    ui: [{ type: "notify", at: 1.2, dur: 5, title: "黑水事故", body: "生产环境宕机 6 小时 · 回滚失败 · 客户流失 41%" }] },
  { id: "c1_b", sec: "ch1", min: 8, img: "van_interior", kb: [0.45, 0.5, 1.05, 0.55, 0.5, 1.12], fx: "snowglass", amb: "carin", ambVol: 0.6,
    lines: [
      { who: "米卡", t: "一天。人家靠 AI，一天就上线了。" },
      { who: "萨姐", t: "闭嘴吧米卡，开你的车。" },
      { who: "马迭代", t: "其实……那个 AI 我试过，它确实……" },
      { who: "老亚", t: "阿迭，睡会儿吧。" }],
    ui: [{ type: "phone", at: 0.4, dur: 5.5, app: "科技头条", title: "竞品靠 AI Agent 一天上线全新产品", body: "“我们团队只有 3 个人，其余都交给了 Agent。”" }],
    sfx: [{ at: 0.4, name: "ping" }] },
  { id: "c1_c", sec: "ch1", min: 9, img: "office_snow", kb: [0.5, 0.6, 1.15, 0.5, 0.45, 1.0], fx: "snow", amb: "wind", ambVol: 0.7,
    lines: [
      { who: "老亚", vo: true, t: "我们在城郊找到一栋没人要的旧写字楼。" },
      { who: "老亚", vo: true, t: "暖气早就停了，只剩一台服务器还在转。" }],
    ui: [{ type: "notify", at: 1.0, dur: 4.5, title: "新的营地", body: "科尔特写字园 · 城郊 · 零下 12℃" },
         { type: "hud", at: 2.0, until: "c2_e", loc: "科尔特写字园" }],
    sfx: [{ at: 1.0, name: "notify" }] },
  { id: "c1_d", sec: "ch1", min: 8, img: "server_warm", kb: [0.5, 0.5, 1.12, 0.5, 0.5, 1.0], fx: "embers", amb: "fan", ambVol: 0.5,
    lines: [
      { who: "萨姐", t: "都过来，靠着机柜。它比暖气管用。" },
      { who: "米卡", t: "手写代码的下场，连取暖都得靠它散热。" },
      { who: "老亚", t: "至少，它还在转。" }] },
  { id: "c1_e", sec: "ch1", min: 10, img: "dutch_snow", kb: [0.5, 0.5, 1.0, 0.5, 0.42, 1.18], fx: "snow", amb: "wind", ambVol: 0.55,
    lines: [
      { who: "达总", t: "兄弟们，听我说。" },
      { who: "达总", t: "我们输了一场，但没有输掉手艺。" },
      { who: "达总", t: "我有一个计划。" },
      { who: "达总", t: "再撑一个版本。就一个版本。" }],
    ui: [{ type: "notify", at: "L3e", dur: 4.5, title: "任务日志已更新", body: "达总的计划：再撑一个版本" }],
    sfx: [{ at: "L3e", name: "notify" }] },

  // ───────── 第二章 营地 ─────────
  { id: "c2_card", sec: "ch2", min: 5.5, img: "camp_night",
    ui: [{ type: "chapter", at: 0, num: "第 二 章", cn: "营 地", en: "CHAPTER II  ·  HORSESHOE OVERLOOK" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c2_a", sec: "ch2", min: 7, img: "camp_night", kb: [0.4, 0.5, 1.12, 0.6, 0.5, 1.12], amb: "office", ambVol: 0.6,
    lines: [{ who: "老亚", vo: true, t: "那段日子很苦。可后来，我常常想起它。" }] },
  { id: "c2_b", sec: "ch2", min: 7, img: "noodles", kb: [0.5, 0.5, 1.2, 0.5, 0.55, 1.05], fx: "steam", amb: "office", ambVol: 0.5,
    lines: [{ who: "老亚", vo: true, t: "凌晨三点的泡面，就是营地的篝火。" }],
    ui: [{ type: "notify", at: 0.8, dur: 5, title: "营地补给", body: "泡面 ×12    咖啡 ×0    头发 −3%" }],
    sfx: [{ at: 0.8, name: "notify" }, { at: 3, name: "kettle", vol: 0.5 }] },
  { id: "c2_c", sec: "ch2", min: 14, img: "notebook_draw", kb: [0.5, 0.5, 1.0, 0.45, 0.5, 1.1], amb: "office", ambVol: 0.3,
    ui: [{ type: "journal", at: 0.6, date: "十月十二日  晴转雪", sketch: "server_warm", text: [
      "达总说，我们是最后一批手艺人。",
      "我不知道这是一种荣誉，",
      "还是一句墓志铭。"] }],
    lines: [
      { who: "老亚", vo: true, t: "十月十二日，晴转雪。达总说，我们是最后一批手艺人。" },
      { who: "老亚", vo: true, t: "我不知道这是一种荣誉，还是一句墓志铭。" }],
    sfx: [{ at: 0.6, name: "page" }, { at: 1.2, name: "pencil", vol: 0.6 }] },
  { id: "c2_d", sec: "ch2", min: 16, img: "young_dad", kb: [0.5, 0.5, 1.05, 0.55, 0.45, 1.15], amb: "office", ambVol: 0.3,
    ui: [{ type: "chat", at: 0.5, closeAt: "L2", prompt: "帮我重构支付模块，接口保持不变，补全单元测试。" }],
    lines: [
      { who: "马迭代", gap: 9.5, t: "三十八秒……" },
      { who: "老亚", t: "阿迭？还没睡？" },
      { who: "马迭代", t: "马上。马上就睡。" }],
    sfx: [{ at: 0.6, name: "typing", dur: 3.2 }, { at: 4.2, name: "enter" }, { at: 9.2, name: "ding" }, { at: "L2", name: "close" }] },
  { id: "c2_e", sec: "ch2", min: 9, img: "photo_team", amb: "office", ambVol: 0.3,
    ui: [{ type: "photo", at: 0.4, caption: "科尔特写字园 · 2026 冬" }],
    lines: [{ who: "老亚", vo: true, gap: 1.5, t: "那时候我们还不知道，那是最后一个一起过的冬天。" }],
    sfx: [{ at: 0.4, name: "shutter" }] },

  // ───────── 第三章 正午对决 ─────────
  { id: "c3_card", sec: "ch3", min: 5.5, img: "noon_standoff",
    ui: [{ type: "chapter", at: 0, num: "第 三 章", cn: "正 午 对 决", en: "CHAPTER III  ·  HIGH NOON" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c3_a", sec: "ch3", min: 12, img: "milton", kb: [0.5, 0.45, 1.15, 0.5, 0.45, 1.0], fx: "dust", amb: "desert", ambVol: 0.6,
    lines: [
      { who: "米尔顿", t: "摩根先生，久仰。投资方派我来，做一次效率审计。" },
      { who: "米尔顿", t: "很简单。同一个需求，你，对它。日落之前交付。" }],
    ui: [{ type: "mission", at: "L2e", dur: 5.5, title: "正午对决", goals: ["在 AI 之前交付订单系统", "金牌条件：零缺陷"] }],
    sfx: [{ at: "L2e", name: "bell" }] },
  { id: "c3_b", sec: "ch3", min: 13, img: "noon_standoff", kb: [0.5, 0.5, 1.0, 0.5, 0.5, 1.22], fx: "dust", amb: "desert", ambVol: 0.8,
    lines: [
      { who: "达总", t: "老亚，让他们看看，什么叫手艺。" },
      { who: "老亚", t: "……开始吧。" }],
    ui: [{ type: "duel", at: "L2e", dur: 7 }],
    sfx: [{ at: 0.2, name: "whistle" }, { at: "L2e", name: "gunshot" }] },
  { id: "c3_c", sec: "ch3", min: 16, img: "hand_code", kb: [0.5, 0.5, 1.1, 0.5, 0.5, 1.25], amb: "none",
    ui: [{ type: "deadeye", at: 0.2 }],
    lines: [
      { who: "老亚", vo: true, gap: 4.0, t: "时区。" },
      { who: "老亚", vo: true, gap: 1.6, t: "并发。" },
      { who: "老亚", vo: true, gap: 1.6, t: "还有那个空指针。" }],
    sfx: [{ at: 0.2, name: "deadeye_in" }, { at: 0.5, name: "heartbeat", dur: 14 }, { at: "L1", name: "mark" }, { at: "L2", name: "mark" }, { at: "L3", name: "mark" }, { at: "end-2.4", name: "deadeye_out" }] },
  { id: "c3_d", sec: "ch3", min: 20, img: "milton", kb: [0.5, 0.4, 1.0, 0.5, 0.42, 1.2], fx: "dust", amb: "desert", ambVol: 0.4,
    lines: [
      { who: "米尔顿", t: "精彩。真的精彩。" },
      { who: "米尔顿", gap: 1.0, t: "不过……" },
      { who: "米尔顿", gap: 8.0, t: "它不会累，摩根先生。它不会记仇。它只会一次比一次好。" },
      { who: "米尔顿", t: "时代变了。" }],
    ui: [{ type: "ci", at: "L2e", dur: 7.5 }],
    sfx: [{ at: 0, name: "clap", dur: 3.2 }, { at: "L2e", name: "ticks", dur: 6.4 }, { at: "L2e+6.8", name: "success" }] },
  { id: "c3_e", sec: "ch3", min: 9, img: "noon_standoff", kb: [0.5, 0.5, 1.22, 0.5, 0.5, 1.3], grade: "bleach", amb: "desert", ambVol: 0.5,
    ui: [{ type: "complete", at: 0.3, dur: 5, title: "正午对决", medal: "银 牌", note: "你赢了这一局" }],
    lines: [{ who: "老亚", vo: true, gap: 5.2, t: "我赢了那一局。可所有人都看见了……第一百零一枪。" }],
    sfx: [{ at: 0.3, name: "complete" }] },

  // ───────── 第四章 咳嗽 ─────────
  { id: "c4_card", sec: "ch4", min: 5.5, img: "hr_room",
    ui: [{ type: "chapter", at: 0, num: "第 四 章", cn: "咳 嗽", en: "CHAPTER IV  ·  A COUGH" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c4_a", sec: "ch4", min: 16, img: "hr_room", kb: [0.5, 0.5, 1.0, 0.45, 0.5, 1.1], amb: "room", ambVol: 0.4,
    ui: [{ type: "hr", at: 0.5, stampAt: "L2" }],
    lines: [
      { who: "HR", gap: 1.5, t: "老亚，公司很感谢你这十五年。" },
      { who: "HR", t: "只是……你的技能栈，被系统标记成了遗产。" },
      { who: "老亚", gap: 1.2, t: "遗产。" },
      { who: "老亚", gap: 1.0, t: "听起来，像是给死人准备的词。" }],
    sfx: [{ at: "L2", name: "stamp" }] },
  { id: "c4_b", sec: "ch4", min: 14, img: "rain_exit", kb: [0.5, 0.5, 1.12, 0.5, 0.5, 1.0], fx: "rain", amb: "rain", ambVol: 0.9,
    lines: [{ who: "老亚", vo: true, gap: 6.5, t: "十五年熬过的夜，都在这两声咳嗽里了。" }],
    ui: [{ type: "hud", at: 1.0, until: "c4_b", loc: "金融街", drain: true },
         { type: "notify", at: 5.2, dur: 5, title: "状态更新", body: "长期熬夜 · 健康核心持续下降" }],
    sfx: [{ at: 1.6, name: "cough" }, { at: 3.4, name: "lighter" }, { at: 5.2, name: "notify" }, { at: 7.0, name: "thunder" }] },

  // ───────── 第五章 归途 ─────────
  { id: "c5_card", sec: "ch5", min: 5.5, img: "scooter_neon",
    ui: [{ type: "chapter", at: 0, num: "第 五 章", cn: "归 途", en: "CHAPTER V  ·  THE RIDE HOME" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c5_a", sec: "ch5", min: 7.5, img: "city_dusk", kb: [0.3, 0.5, 1.15, 0.7, 0.5, 1.15], amb: "city", ambVol: 0.4 },
  { id: "c5_b", sec: "ch5", min: 14, img: "scooter_neon", kb: [0.5, 0.5, 1.08, 0.5, 0.5, 1.16], fx: "neon", amb: "city", ambVol: 0.3,
    ui: [{ type: "billboards", at: 0 }],
    sfx: [{ at: 1.0, name: "whoosh" }, { at: 4.5, name: "whoosh" }, { at: 8.0, name: "whoosh" }, { at: 11.0, name: "whoosh" }] },
  { id: "c5_c", sec: "ch5", min: 12, img: "scooter_back", kb: [0.5, 0.5, 1.0, 0.5, 0.45, 1.15], amb: "city", ambVol: 0.2,
    lines: [
      { who: "老亚", vo: true, gap: 1.5, t: "我们是一群手艺人。" },
      { who: "老亚", vo: true, gap: 0.8, t: "活在一个已经不需要手艺的世界里。" }],
    ui: [{ type: "quote", at: "L1", text: ["我们是一群手艺人，", "活在一个已经不需要手艺的世界里。"] }] },
  { id: "c5_d", sec: "ch5", min: 12, img: "city_dusk", kb: [0.6, 0.45, 1.25, 0.5, 0.5, 1.02], amb: "city", ambVol: 0.2,
    lines: [
      { who: "老亚", vo: true, gap: 1.2, t: "可我不恨它。" },
      { who: "老亚", vo: true, gap: 0.8, t: "就像你没法去恨一场雪，恨一次日落。" }] },

  // ───────── 第六章 救赎 ─────────
  { id: "c6_card", sec: "ch6", min: 5.5, img: "team_split",
    ui: [{ type: "chapter", at: 0, num: "第 六 章", cn: "救 赎", en: "CHAPTER VI  ·  REDEMPTION" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "c6_a", sec: "ch6", min: 11, img: "mika", kb: [0.5, 0.5, 1.0, 0.5, 0.45, 1.15], amb: "room", ambVol: 0.3,
    ui: [{ type: "im", at: 0.5 }],
    lines: [{ who: "萨姐", gap: 7.6, t: "米卡。这条消息，是你发的？" }],
    sfx: [{ at: 1.0, name: "sent" }, { at: 3.6, name: "ping" }, { at: 6.2, name: "alarm" }] },
  { id: "c6_b", sec: "ch6", min: 10, img: "team_split", kb: [0.5, 0.5, 1.12, 0.5, 0.5, 1.0], fx: "rainglass", amb: "rain", ambVol: 0.4,
    lines: [
      { who: "米卡", t: "我只是比你们，早一步看清楚。" },
      { who: "达总", gap: 1.2, t: "……也许，他说得对。" },
      { who: "老亚", t: "达总，你的计划呢？" },
      { who: "达总", gap: 1.4, t: "我……我还在想。" }] },
  { id: "c6_c", sec: "ch6", min: 14, img: "notebook_hand", kb: [0.5, 0.5, 1.05, 0.5, 0.5, 1.18], amb: "rain", ambVol: 0.2,
    lines: [
      { who: "老亚", t: "阿迭，拿着。" },
      { who: "老亚", t: "这里面，是我十五年画过的每一张图。" },
      { who: "老亚", t: "去学它，用它。" },
      { who: "老亚", gap: 1.0, t: "别回头……别像我。" },
      { who: "马迭代", t: "老亚……" },
      { who: "老亚", t: "走吧，阿迭。走！" }] },
  { id: "c6_d", sec: "ch6", min: 13, img: "keyboard", kb: [0.5, 0.5, 1.15, 0.5, 0.5, 1.0], amb: "room", ambVol: 0.25,
    ui: [{ type: "commit", at: 0.5 }],
    lines: [{ who: "老亚", vo: true, gap: 8.6, t: "最后一次提交。谢谢你，老伙计。" }],
    sfx: [{ at: 0.6, name: "typing", dur: 4.4 }, { at: 5.2, name: "enter" }, { at: 6.4, name: "typing", dur: 1.2 }, { at: 7.8, name: "enter" }, { at: "end-1.5", name: "pat" }] },
  { id: "c6_e", sec: "ch6", min: 14, img: "rooftop_dawn", kb: [0.5, 0.55, 1.18, 0.5, 0.5, 1.0], fx: "mist", amb: "dawn", ambVol: 0.5,
    lines: [{ who: "老亚", vo: true, gap: 8.0, t: "天亮了。" }],
    sfx: [{ at: 1.5, name: "lidclose" }] },
  { id: "c6_f", sec: "ch6", min: 10, img: "rooftop_wide", kb: [0.5, 0.5, 1.35, 0.5, 0.5, 1.0], fx: "mist", amb: "dawn", ambVol: 0.4, fadeOut: 3 },

  // ───────── 尾声 比彻之希 ─────────
  { id: "ep_card", sec: "ep", min: 7, img: "studio_morning",
    ui: [{ type: "chapter", at: 0, num: "尾  声", cn: "比 彻 之 希", en: "EPILOGUE  ·  BEECHER'S HOPE", sub: "三 年 后" }],
    sfx: [{ at: 0.3, name: "inkhit" }] },
  { id: "ep_a", sec: "ep", min: 13, img: "studio_morning", kb: [0.4, 0.5, 1.1, 0.55, 0.5, 1.02], amb: "birds", ambVol: 0.6,
    ui: [{ type: "dash", at: 0.8 }],
    lines: [
      { who: "马迭代", vo: true, gap: 2.2, t: "老亚说过，别像他。" },
      { who: "马迭代", vo: true, gap: 0.8, t: "可我发现，我越来越像他了。" }],
    sfx: [{ at: 0.8, name: "notify" }] },
  { id: "ep_b", sec: "ep", min: 14, img: "old_notebook", kb: [0.5, 0.5, 1.02, 0.5, 0.52, 1.14], amb: "birds", ambVol: 0.4,
    ui: [{ type: "handcode", at: 1.0 }],
    lines: [{ who: "马迭代", vo: true, gap: 9.0, t: "这一行，我自己写。" }],
    sfx: [{ at: 1.0, name: "page" }, { at: 3.6, name: "typing", dur: 4.6 }] },
  { id: "ep_c", sec: "ep", min: 8, img: null, amb: "wind", ambVol: 0.2,
    ui: [{ type: "finale", at: 0.6 }] },
  { id: "ep_logo", sec: "logo", min: 8, img: null,
    ui: [{ type: "logo", at: 0.4 }],
    sfx: [{ at: 0.4, name: "slam" }] },
  { id: "ep_credits", sec: "credits", min: 22, img: null,
    ui: [{ type: "credits", at: 0 }] },
  { id: "ep_egg", sec: "egg", min: 10, img: "old_notebook", amb: "birds", ambVol: 0.3,
    ui: [{ type: "egg", at: 0.5 }],
    lines: [
      { who: "孩子", gap: 1.5, t: "爸爸，什么叫手写代码？" }],
    sfx: [{ at: "end-2.5", name: "laugh" }] },
];

const CAST = {
  "老亚": { color: "#c9a25a" }, "达总": { color: "#b86b4b" }, "马迭代": { color: "#7fa6c4" },
  "米卡": { color: "#9a9a6a" }, "萨姐": { color: "#c47f8f" }, "米尔顿": { color: "#b0b0b0" },
  "HR": { color: "#a0b4c0" }, "孩子": { color: "#d8c27a" },
};

if (typeof module !== "undefined") module.exports = { SCENES, CAST };
