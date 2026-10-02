#!/usr/bin/env python3
"""Replace only H3 shot windows in v11, retaining its original audio packets."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK = ROOT / "out/h3-edit"
BASE = ROOT / "out/red-error-final-v11.mp4"
OUTPUT = ROOT / "out/red-error-final-v12-h3.mp4"
FPS = 24


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=nb_frames,width,height,r_frame_rate", "-of", "json", str(path)]))["streams"][0]


def check(path, count):
    info = probe(path)
    if (int(info["nb_frames"]), info["width"], info["height"], info["r_frame_rate"]) != (count, 1920, 1080, "24/1"):
        raise ValueError(f"Wrong segment dimensions or frame count: {path}")


def main():
    if OUTPUT.exists() and (WORK / "verification.json").exists():
        raise SystemExit(f"Refusing to overwrite verified movie {OUTPUT}")
    WORK.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((ROOT / "audio/timeline.json").read_text())
    spans = []
    for scene in timeline["scenes"]:
        shots = [{"at": 0, "clip": scene.get("clip")}] + scene["alt"]
        for i, shot in enumerate(shots):
            if not shot.get("clip"):
                continue
            end = shots[i + 1]["at"] if i + 1 < len(shots) else scene["dur"]
            # Include the outgoing transition so its previous layer uses the last video frame.
            transition = shots[i + 1].get("tr", "cut") if i + 1 < len(shots) else "dissolve"
            tail = .9 if transition == "dissolve" else .42 if transition == "whip" else 0
            spans.append((round((scene["t0"] + shot["at"]) * FPS),
                          round((scene["t0"] + end + tail) * FPS)))
    total = int(probe(BASE)["nb_frames"])
    merged = []
    for start, end in sorted(spans):
        end = min(end, total)
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    parts, cursor = [], 0
    for start, end in merged:
        if cursor < start:
            parts.append((cursor, start, False))
        parts.append((start, end, True))
        cursor = end
    if cursor < total:
        parts.append((cursor, total, False))
    state_path = WORK / "render-plan.json"
    # Cached segments are valid only for the exact same edit and renderer.
    import hashlib
    sources = ["web/engine.js", "web/clip-frames.js", "web/timeline.js", "web/video/clips.js", "scripts/capture.js"]
    digest = hashlib.sha256(b"".join((ROOT / s).read_bytes() for s in sources)).hexdigest()
    state = {"base": str(BASE), "base_size": BASE.stat().st_size, "renderer_sha256": digest,
             "frames": total, "parts": parts}
    old = json.loads(state_path.read_text()) if state_path.exists() else None
    reusable = old == json.loads(json.dumps(state))
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    files = []
    for index, (start, end, generated) in enumerate(parts):
        output = WORK / f"part-{index:02d}.mp4"
        files.append(output)
        count = end - start
        if output.exists() and reusable:
            check(output, count)
            continue
        print(f"Part {index + 1}/{len(parts)}: {start / FPS:.3f}-{end / FPS:.3f}s {'H3' if generated else 'v11'}", flush=True)
        if generated:
            subprocess.run(["node", "scripts/capture.js", str(start / FPS), str(end / FPS), str(output), "9338"], cwd=ROOT, check=True)
        else:
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(start / FPS),
                            "-i", str(BASE), "-map", "0:v:0", "-an", "-frames:v", str(count),
                            "-vf", "setsar=1", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                            "-pix_fmt", "yuv420p", "-r", str(FPS), str(output)], check=True)
        check(output, count)
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in files))
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(BASE), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
                    "-movflags", "+faststart", str(OUTPUT)], check=True)
    check(OUTPUT, total)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], check=True)
    # Hash compressed audio packets, which must be identical to v11.
    def audio_hash(path):
        return subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
            "-map", "0:a:0", "-c:a", "copy", "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
    original, result = audio_hash(BASE), audio_hash(OUTPUT)
    if original != result:
        raise ValueError("Audio packets changed")
    state.update(output=str(OUTPUT), audio_packets_sha256=result, full_decode="passed")
    (WORK / "verification.json").write_text(json.dumps(state, indent=2) + "\n")
    print("Verified movie with original v11 audio:", OUTPUT, flush=True)


if __name__ == "__main__":
    main()
