#!/usr/bin/env python3
"""Update the server line and the daughter's voice over the v16 film."""
import json
import pathlib
import runpy
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "out/line-fixes-edit"
BASE = ROOT / "out/red-error-final-v16-emotion.mp4"
OUTPUT = ROOT / "out/red-error-final-v17-line-fixes.mp4"
PREVIEW = ROOT / "out/video-preview/red-error-v17-line-fixes.mp4"
FPS = 24


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    if OUTPUT.exists():
        raise ValueError("Finished export exists; refusing to overwrite it")
    WORK.mkdir(parents=True, exist_ok=True)
    timeline_path = ROOT / "audio/timeline.json"
    before = json.loads(timeline_path.read_text())
    run(["node", "scripts/build-timeline.js"])
    after = json.loads(timeline_path.read_text())
    def timing(timeline):
        return [(s["id"], s["t0"], s["dur"], [(l["key"], l["st"], l["en"]) for l in s["lines"]])
                for s in timeline["scenes"]]
    if timing(before) != timing(after):
        raise ValueError("Dialogue correction changed the timeline")
    helpers = runpy.run_path(str(ROOT / "scripts/render-opening.py"))
    probe, verify, mix = (helpers[k] for k in ("probe", "verify", "mix"))
    plan = json.loads((ROOT / "out/emotion-edit/manifest.json").read_text())
    replacement = {j["id"]: j for j in json.loads((ROOT / "audio/line-fixes/generate.json").read_text())["jobs"]}
    for job in plan["jobs"]:
        job["generate"] = job["id"] in replacement
        if job["generate"]:
            job.update(replacement[job["id"]])
    plan.update(version="v17", previous_cost_cny=json.loads((ROOT / "out/emotion-edit/audio-verification.json").read_text())["total_estimate_cny"],
                new_video_estimate_cny=0, picture_source=str(BASE))
    plan["cast"]["孩子"] = "lovely_girl"
    usage = sum(json.loads((ROOT / j["output"]).with_suffix(".json").read_text())["usage"]["usage_characters"] for j in replacement.values())
    if plan["previous_cost_cny"] + usage * 3.5 / 10000 > plan["budget_cny"]:
        raise ValueError("Revised dub exceeds the remaining budget")
    (WORK / "manifest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    mix.__globals__["WORK"] = WORK
    original_frames = int(probe(ROOT / "out/red-error-final-v12-h3.mp4")["nb_frames"])
    audio = mix(plan, original_frames)
    total = int(probe(BASE)["nb_frames"])
    def edited(frame):
        return frame - sum(max(0, min(frame, b) - a) for a, b in plan["removed_source_frames"] if frame > a)
    scene = next(s for s in after["scenes"] if s["id"] == "c1_d")
    a, b = round(scene["t0"] * FPS), round((scene["t0"] + scene["dur"] + .9) * FPS)
    parts = [(0, edited(a), None), (edited(a), edited(b), (a, b)), (edited(b), total, None)]
    files = []
    for i, (start, end, source) in enumerate(parts):
        part = WORK / f"part-{i:02d}.mp4"
        files.append(part)
        print(f"Picture part {i + 1}/3: {start/FPS:.2f}-{end/FPS:.2f}", flush=True)
        if source:
            run(["node", "scripts/capture.js", str(source[0]/FPS), str(source[1]/FPS), str(part), "9347"])
        else:
            run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(start/FPS), "-i", str(BASE),
                 "-map", "0:v:0", "-an", "-frames:v", str(end-start), "-vf", "setsar=1",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "24", str(part)])
        verify(part, end-start)
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in files))
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(OUTPUT)])
    verify(OUTPUT, total)
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"])
    epilogue = next(s for s in after["scenes"] if s["id"] == "ep_c")
    previews = []
    for i, s in enumerate((scene, epilogue)):
        preview = WORK / f"preview-{i}.mp4"
        frames = round(s["dur"] * FPS)
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(edited(round(s["t0"]*FPS))/FPS),
             "-i", str(OUTPUT), "-frames:v", str(frames), "-t", str(frames/FPS),
             "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-c:a", "aac", "-b:a", "192k", str(preview)])
        verify(preview, frames)
        previews.append(preview)
    preview_concat = WORK / "preview-concat.txt"
    preview_concat.write_text("".join(f"file '{p.name}'\n" for p in previews))
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(preview_concat),
         "-c", "copy", "-movflags", "+faststart", str(PREVIEW)])
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(PREVIEW), "-f", "null", "-"])
    (WORK / "verification.json").write_text(json.dumps({"output": str(OUTPUT), "preview": str(PREVIEW),
        "frames": total, "duration": total/FPS, "full_decode": "passed", "timeline_unchanged": True,
        "replacement_ids": list(replacement), "new_tts_usage_characters": usage,
        "new_estimate_cny": usage*3.5/10000, "studio_card_seconds": 7}, indent=2) + "\n")
    print("Verified:", OUTPUT, PREVIEW, flush=True)


if __name__ == "__main__":
    main()
