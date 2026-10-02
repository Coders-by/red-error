#!/usr/bin/env python3
"""参考图驱动的镜头生成：shots.tsv → refs/img/<ref_*>.jpg 与 web/img_hd/<id>.jpg → web/imgx_hd/<id>.jpg

shots.tsv 列：id <TAB> 画幅 <TAB> 参考图(逗号分隔 id，可为 -) <TAB> 提示词
  - id 以 ref_ 开头 = 角色/场景/道具参考，输出到 refs/img/，不进渲染
  - 参考图 id 指向 refs/img/<id>.jpg 或 web/img_hd/<id>.jpg，以 inlineData 真正随请求提交
用法：IMAGE_KEY=... scripts/gen-shots.py [id ...]   已存在则跳过（FORCE=1 强制重做）
"""
import base64, json, os, subprocess, sys, time, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)
KEY = os.environ.get("IMAGE_KEY") or sys.exit("IMAGE_KEY not set")
BASE = os.environ.get("IMAGE_BASE", "https://deepkey.top")
MODEL = "gemini-3-pro-image-preview"
TMP = pathlib.Path(os.environ.get("CLAUDE_JOB_DIR", "/tmp")) / "tmp"
TMP.mkdir(parents=True, exist_ok=True)
STYLE = ("cinematic film still, anamorphic widescreen, photorealistic, shot on ARRI Alexa 65, sharp focus, crisp fine detail, "
         "natural color grading, volumetric light, classic western film composition and dusty golden lighting, "
         "contemporary 2026 setting with modern clothes and modern computers, no text, no captions, no watermark")
REF_STYLE = "photorealistic character reference photo, neutral soft studio light, sharp focus, plain grey backdrop, no text, no watermark"


def load_shots():
    rows = []
    for line in (ROOT / "shots.tsv").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        sid, aspect, refs, prompt = line.split("\t", 3)
        rows.append((sid, aspect, [] if refs == "-" else refs.split(","), prompt))
    return rows


def out_path(sid):
    return ROOT / ("refs/img" if sid.startswith("ref_") else "web/img_hd") / f"{sid}.jpg"


def ref_bytes(rid):
    """参考图缩到长边 1280 的 JPEG，控制请求体积"""
    src = out_path(rid)
    if not src.exists():
        sys.exit(f"missing reference {rid}")
    small = TMP / f"ref_small_{rid}.jpg"
    if not small.exists() or small.stat().st_mtime < src.stat().st_mtime:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                        "scale='if(gt(iw,ih),1280,-2)':'if(gt(iw,ih),-2,1280)'", "-q:v", "3", str(small)], check=True)
    return small.read_bytes()


def generate(sid, aspect, refs, prompt):
    parts = []
    for r in refs:
        parts.append({"text": f"Reference image [{r}]:"})
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(ref_bytes(r)).decode()}})
    lead = ("Use the reference images above to keep the exact same faces, hair, facial hair, age, clothing, props and "
            "architecture. Do not copy their backgrounds or plain studio lighting unless asked. " if refs else "")
    style = REF_STYLE if sid.startswith("ref_") else STYLE
    parts.append({"text": f"{lead}{prompt}. {style}"})
    body = json.dumps({"contents": [{"role": "user", "parts": parts}],
                       "generationConfig": {"responseModalities": ["IMAGE"],
                                            "imageConfig": {"aspectRatio": aspect, "imageSize": "2K"}}}).encode()
    req = urllib.request.Request(f"{BASE}/v1beta/models/{MODEL}:generateContent", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=360) as r:
        data = json.load(r)
    imgs = [p for p in data["candidates"][0]["content"]["parts"] if "inlineData" in p and not p.get("thought")]
    if not imgs:
        raise RuntimeError("no image in response: " + json.dumps(data)[:300])
    return base64.b64decode(imgs[-1]["inlineData"]["data"])


def save(sid, raw):
    dst = out_path(sid)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = TMP / f"raw_{sid}"
    tmp.write_bytes(raw)
    # 统一转成高质量 JPEG
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-q:v", "1", str(dst)], check=True)
    tmp.unlink()
    for old in dst.parent.glob(f"{sid}.*"):
        if old != dst:
            old.unlink()
    if not sid.startswith("ref_"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(dst), "-vf",
                        "scale=2560:1088:force_original_aspect_ratio=increase:flags=lanczos,crop=2560:1088",
                        "-q:v", "2", f"web/imgx_hd/{sid}.jpg"], check=True)
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0:s=x", str(dst)], capture_output=True, text=True).stdout.strip()
    print(f"ok {sid} {wh}", flush=True)


def main():
    want = set(sys.argv[1:])
    for sid, aspect, refs, prompt in load_shots():
        if want and sid not in want:
            continue
        if not os.environ.get("FORCE") and out_path(sid).exists() and not want:
            print(f"skip {sid}", flush=True)
            continue
        for attempt in range(1, 5):
            try:
                save(sid, generate(sid, aspect, refs, prompt))
                break
            except (urllib.error.URLError, RuntimeError, KeyError, TimeoutError, json.JSONDecodeError) as e:
                msg = e.read().decode()[:200] if isinstance(e, urllib.error.HTTPError) else str(e)[:200]
                print(f"retry {sid} #{attempt}: {msg}", flush=True)
                time.sleep(15 * attempt)
        else:
            print(f"FAIL {sid}", flush=True)
    print("ALLDONE", flush=True)


if __name__ == "__main__":
    main()
