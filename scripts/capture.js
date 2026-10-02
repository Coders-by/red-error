// 用本机 Chrome 的 DevTools 协议逐帧截图（无第三方依赖），管道给 ffmpeg 编码
// 用法: node scripts/capture.js <start> <end> <out.mp4|dir> [port]    （dir 模式输出 jpg 预览）
const { spawn } = require("child_process");
const fs = require("fs"), path = require("path");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const [, , A, B, OUT, PORT = "9333"] = process.argv;
const FPS = 24, ROOT = path.resolve(__dirname, "..");
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  const prof = fs.mkdtempSync("/tmp/rechrome-");
  const ch = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${prof}`, "--allow-file-access-from-files",
    "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1920,1080", "--mute-audio", "about:blank"], { stdio: "ignore" });
  let list;
  for (let i = 0; i < 60; i++) { try { list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); if (list.find(x => x.type === "page")) break; } catch { } await sleep(250); }
  const ws = new WebSocket(list.find(x => x.type === "page").webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let id = 0; const pend = new Map();
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
  const cmd = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await cmd("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  await cmd("Page.enable");
  await cmd("Page.navigate", { url: "file://" + path.join(ROOT, "web/render.html") });
  const ev = async (e) => {
    const r = await cmd("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true });
    if (r.error || r.result?.exceptionDetails) throw new Error(JSON.stringify(r.error || r.result.exceptionDetails));
    return r;
  };
  let ready = false;
  for (let i = 0; i < 200; i++) { const r = await ev("window.READY"); if (r.result?.result?.value === true) { ready = true; break; } await sleep(200); }
  if (!ready) throw new Error("Renderer did not become ready");

  const f0 = Math.round(+A * FPS), f1 = Math.round(+B * FPS);
  const dirMode = !OUT.endsWith(".mp4");
  let ff;
  if (dirMode) fs.mkdirSync(OUT, { recursive: true });
  else ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(FPS), OUT], { stdio: ["pipe", "inherit", "inherit"] });
  const t0 = Date.now();
  const TIMES = process.env.AT ? process.env.AT.split(",").map(Number) : null;
  const N = TIMES ? TIMES.length : f1 - f0;
  for (let k = 0; k < N; k++) {
    const f = f0 + k, t = TIMES ? TIMES[k] : f / FPS;
    await ev(`renderFrame(${t})`);
    const r = await cmd("Page.captureScreenshot", { format: "jpeg", quality: 93, captureBeyondViewport: false });
    const buf = Buffer.from(r.result.data, "base64");
    if (dirMode) fs.writeFileSync(path.join(OUT, `${t.toFixed(2)}.jpg`), buf);
    else if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if ((f - f0) % 240 === 0) console.log(`[${A}-${B}] t=${t.toFixed(1)} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  if (ff) { ff.stdin.end(); await new Promise(r => ff.on("close", r)); }
  ws.close(); ch.kill(); await sleep(800); try { fs.rmSync(prof, { recursive: true, force: true }); } catch { }
  console.log("done", OUT);
})();
