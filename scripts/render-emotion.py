#!/usr/bin/env python3
"""Integrate emotional H3 shots and the heavier Milton voice into the v15 edit."""
import hashlib
import json
import pathlib
import runpy
import subprocess
import argparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "out/emotion-edit"
BASE = ROOT / "out/red-error-final-v15-studio-card.mp4"
OUTPUT = ROOT / "out/red-error-final-v16-emotion.mp4"
FPS = 24


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mix-only", action="store_true")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    helpers = runpy.run_path(str(ROOT / "scripts/render-opening.py"))
    probe, verify, mix = (helpers[k] for k in ("probe", "verify", "mix"))
    plan = json.loads((ROOT / "out/studio-card-edit/manifest.json").read_text())
    new = json.loads((ROOT / "audio/emotion-edit/milton-tts.json").read_text())
    replacement = {j["id"]: j for j in new["jobs"]}
    for job in plan["jobs"]:
        job["generate"] = job["id"] in replacement
        if job["generate"]:
            job.update(replacement[job["id"]])
    preview_fee = json.loads((ROOT / "out/voice-preview/milton-heavy-design-report.json").read_text())["estimated_preview_cny"]
    base_cost = json.loads((ROOT / "out/studio-card-edit/audio-verification.json").read_text())["total_estimate_cny"]
    plan.update(version="v16", previous_cost_cny=base_cost + preview_fee + 9.9,
                new_video_estimate_cny=34.4, budget_cny=144.64425,
                picture_source=str(BASE))
    estimated = plan["previous_cost_cny"] + 34.4 + sum(len(j["text"])*2 for j in new["jobs"]) * 3.5 / 10000
    if estimated > plan["budget_cny"]:
        raise ValueError("New generation exceeds the authorized additional 50 CNY")
    (WORK / "manifest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    mix.__globals__["WORK"] = WORK
    original_frames = int(probe(ROOT / "out/red-error-final-v12-h3.mp4")["nb_frames"])
    audio = mix(plan, original_frames)
    if args.mix_only:
        return
    total = int(probe(BASE)["nb_frames"])
    tl = json.loads((ROOT / "audio/timeline.json").read_text())
    def edited(frame):
        return frame - sum(max(0, min(frame, b) - a) for a, b in plan["removed_source_frames"] if frame > a)
    spans = []
    for scene in tl["scenes"]:
        shots = [{"at": 0, "clip": scene.get("clip")}] + scene["alt"]
        for i, shot in enumerate(shots):
            if not (shot.get("clip") or {}).get("id", "").startswith("h3-emotion-"):
                continue
            end = shots[i+1]["at"] if i+1 < len(shots) else scene["dur"]
            tail = .9 if i+1 == len(shots) or shots[i+1].get("tr", "cut") == "dissolve" else 0
            spans.append((round((scene["t0"]+shot["at"])*FPS), round((scene["t0"]+end+tail)*FPS)))
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a,b))
    parts, cursor = [], 0
    for a,b in merged:
        if cursor < edited(a):
            parts.append((cursor, edited(a), None))
        parts.append((edited(a), edited(b), (a,b)))
        cursor = edited(b)
    if cursor < total:
        parts.append((cursor,total,None))
    (WORK / "picture-plan.json").write_text(json.dumps(parts, indent=2) + "\n")
    files = []
    for i,(a,b,source) in enumerate(parts):
        output = WORK / f"part-{i:02d}.mp4"
        files.append(output)
        print(f"Part {i+1}/{len(parts)} {a/FPS:.2f}-{b/FPS:.2f} {'new action' if source else 'v15'}", flush=True)
        if source:
            run(["node", "scripts/capture.js", str(source[0]/FPS), str(source[1]/FPS), str(output), "9345"])
        else:
            run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(a/FPS), "-i", str(BASE),
                 "-map", "0:v:0", "-an", "-frames:v", str(b-a), "-vf", "setsar=1", "-c:v", "libx264",
                 "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", str(output)])
        verify(output,b-a)
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in files))
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(OUTPUT)])
    verify(OUTPUT,total)
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"])
    (WORK / "verification.json").write_text(json.dumps({"output":str(OUTPUT), "frames":total,
         "duration":total/FPS, "new_video_seconds":43, "full_decode":"passed", "studio_card_seconds":7,
         "budget_cny":plan["budget_cny"]}, indent=2)+"\n")
    print("Verified:",OUTPUT,flush=True)


if __name__ == "__main__":
    main()
