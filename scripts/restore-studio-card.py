#!/usr/bin/env python3
"""Restore the full seven-second studio card in the approved full-dub edit."""
import hashlib
import json
import pathlib
import runpy
import subprocess
import wave

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "out/studio-card-edit"
OLD = ROOT / "out/red-error-final-v14-full-dub.mp4"
SOURCE = ROOT / "out/opening-edit/opening-source.mp4"
OUTPUT = ROOT / "out/red-error-final-v15-studio-card.mp4"
PREVIEW = ROOT / "out/video-preview/red-error-v15-first-three-minutes.mp4"
FPS = 24


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    helpers = runpy.run_path(str(ROOT / "scripts/render-opening.py"))
    probe, verify, mix = (helpers[k] for k in ("probe", "verify", "mix"))
    plan = json.loads((ROOT / "audio/full-dub/manifest.json").read_text())
    removed = [round(25.5 * FPS), 30 * FPS]
    if removed not in plan["removed_source_frames"]:
        raise ValueError("The expected studio-card shortening is absent")
    plan["removed_source_frames"].remove(removed)
    plan["version"] = "v15"
    plan["previous_cost_cny"] = json.loads((ROOT / "out/full-dub-edit/audio-verification.json").read_text())["total_estimate_cny"]
    for job in plan["jobs"]:
        job["generate"] = False
    plan.update(studio_card_seconds=7, restored_seconds=4.5, picture_source=str(OLD))
    (WORK / "manifest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    mix.__globals__["WORK"] = WORK
    total = int(probe(ROOT / "out/red-error-final-v12-h3.mp4")["nb_frames"])
    mixed = mix(plan, total)
    old_frames = int(probe(OLD)["nb_frames"])
    verify(OLD, total - sum(b - a for a, b in plan["removed_source_frames"]) - (removed[1] - removed[0]))
    parts = [(OLD, 0, 23 * FPS, False), (SOURCE, 23 * FPS, 30 * FPS, False),
             (OLD, removed[0], old_frames, True)]
    files = []
    for i, (source, begin, end, copy) in enumerate(parts):
        part = WORK / f"part-{i:02d}.mp4"
        files.append(part)
        codec = ["-c:v", "copy"] if copy else ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(begin / FPS), "-i", str(source),
             "-map", "0:v:0", "-an", "-frames:v", str(end - begin), *codec, str(part)])
        verify(part, end - begin)
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in files))
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(mixed), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(OUTPUT)])
    expected = old_frames + removed[1] - removed[0]
    verify(OUTPUT, expected)
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(OUTPUT), "-t", "180", "-frames:v", str(180 * FPS),
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", "-movflags", "+faststart", str(PREVIEW)])
    verify(PREVIEW, 180 * FPS)
    for path in (OUTPUT, PREVIEW):
        run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"])
    def tail_hash(path, start):
        return subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-i", str(path),
             "-map", "0:v:0", "-c:v", "copy", "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
    before, after = tail_hash(OLD, 25.5), tail_hash(OUTPUT, 30)
    if before != after:
        raise ValueError("Picture after the studio card changed")
    # Skip the old cut's 12 ms microfade; the remaining approved PCM must match exactly.
    with wave.open(str(ROOT / "out/full-dub-edit/mix-v14.wav")) as old, wave.open(str(mixed)) as new:
        old.setpos(round(25.52 * 48000))
        new.setpos(round(30.02 * 48000))
        if hashlib.sha256(old.readframes(old.getnframes())).digest() != hashlib.sha256(new.readframes(new.getnframes())).digest():
            raise ValueError("Approved audio after the studio card changed")
    report = {"output": str(OUTPUT), "preview": str(PREVIEW), "frames": expected, "duration": expected / FPS,
              "studio_card_source_seconds": [23, 30], "studio_card_duration": 7, "restored_seconds": 4.5,
              "subsequent_picture_packets_sha256": after, "subsequent_pcm_identical": True,
              "full_decode": "passed", "new_generation_cost_cny": 0}
    (WORK / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified:", OUTPUT, PREVIEW, flush=True)


if __name__ == "__main__":
    main()
