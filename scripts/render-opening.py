#!/usr/bin/env python3
"""Render the revised opening, mix verified voices, and retain the v12 remainder."""
import argparse
import array
import hashlib
import json
import math
import pathlib
import subprocess
import wave

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "out/opening-edit"
BASE = ROOT / "out/red-error-final-v12-h3.mp4"
OUTPUT = ROOT / "out/red-error-final-v13-opening.mp4"
PREVIEW = ROOT / "out/video-preview/red-error-v13-first-three-minutes.mp4"
FPS, RATE, PREFIX = 24, 48000, 191 * 24


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=nb_frames,width,height,r_frame_rate", "-of", "json", str(path)]))["streams"][0]


def verify(path, frames):
    info = probe(path)
    if (int(info["nb_frames"]), info["width"], info["height"], info["r_frame_rate"]) != (frames, 1920, 1080, "24/1"):
        raise ValueError(f"Unexpected video geometry or frame count: {path}")


def read_floats(command):
    samples = array.array("f")
    samples.frombytes(subprocess.check_output(command))
    return samples


def mix(plan, total):
    target = WORK / f"mix-{plan.get('version', 'v13')}.wav"
    tl = json.loads((ROOT / "audio/timeline.json").read_text())
    jobs = list(plan["jobs"])
    selected = json.loads((ROOT / "audio/dub-preview/minimax-elder-selected.json").read_text())
    for job in selected["jobs"] if plan.get("append_selected_jobs", True) else []:
        scene = next(s for s in tl["scenes"] if any(l["key"] == job["id"] for l in s["lines"]))
        index = next(i for i, l in enumerate(scene["lines"]) if l["key"] == job["id"])
        line = scene["lines"][index]
        end = scene["lines"][index + 1]["st"] - .16 if index + 1 < len(scene["lines"]) else scene["dur"] - .3
        jobs.append({**job, "source_start": scene["t0"] + line["st"], "source_end": scene["t0"] + end})
    signature = hashlib.sha256(json.dumps(plan, sort_keys=True).encode() + BASE.stat().st_size.to_bytes(8, "big"))
    for job in jobs:
        path = ROOT / job["output"]
        record = json.loads(path.with_suffix(".json").read_text())
        if record["audio_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"Unverified voice: {path}")
        if record["text"] != job["text"] or record["voice_id"] != job["voice_id"]:
            raise ValueError(f"Voice does not match planned text or cast: {job['id']}")
        signature.update(path.read_bytes())
    signature.update(pathlib.Path(__file__).read_bytes())
    state = WORK / "audio-verification.json"
    if target.exists() and state.exists() and json.loads(state.read_text())["input_sha256"] == signature.hexdigest():
        return target
    bed = read_floats(["ffmpeg", "-nostdin", "-v", "error", "-i", str(BASE), "-map", "0:a:0",
                       "-ar", str(RATE), "-ac", "2", "-f", "f32le", "-"])
    sample_frames = total * RATE // FPS
    del bed[sample_frames * 2:]
    bed.extend([0.0] * (sample_frames * 2 - len(bed)))
    duck = array.array("f", [1.0]) * sample_frames
    voices, timing = [], []
    previous_stop = 0
    for job in sorted(jobs, key=lambda j: j["source_start"]):
        path = ROOT / job["output"]
        with wave.open(str(path)) as audio:
            duration = audio.getnframes() / audio.getframerate()
        slot = job["source_end"] - job["source_start"]
        tempo = max(1.0, duration / slot)
        if tempo > 1.25:
            raise ValueError(f"Voice needs a new edit rather than rushed playback: {job['id']} ({tempo:.2f})")
        samples = read_floats(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-af",
            f"atempo={tempo},loudnorm=I=-19:TP=-2:LRA=8,aresample={RATE}", "-ac", "1", "-f", "f32le", "-"])
        start = round(job["source_start"] * RATE)
        stop = start + len(samples)
        if start < previous_stop or stop > sample_frames:
            raise ValueError(f"Overlapping or out-of-range voice: {job['id']}")
        for a, b in plan["removed_source_frames"]:
            if start < b * RATE // FPS and stop > a * RATE // FPS:
                raise ValueError(f"Voice crosses an export cut: {job['id']}")
        previous_stop = stop
        voices.append((start, samples))
        attack, release = round(.18 * RATE), round(.45 * RATE)
        for frame in range(max(0, start - attack), min(sample_frames, stop + release)):
            if frame < start:
                k = (frame - start + attack) / attack
            elif frame >= stop:
                k = 1 - (frame - stop) / release
            else:
                k = 1
            duck[frame] = min(duck[frame], 1 - .58 * k)
        timing.append({"id": job["id"], "start": start / RATE, "end": stop / RATE, "tempo": tempo})
    for frame, gain in enumerate(duck):
        if gain < 1:
            bed[frame * 2] *= gain
            bed[frame * 2 + 1] *= gain
    for start, samples in voices:
        for i, value in enumerate(samples):
            bed[(start + i) * 2] += value
            bed[(start + i) * 2 + 1] += value
    # Equal-power microfades prevent clicks at the shortened titles without shifting either track.
    spans, cursor = [], 0
    for begin, end in plan["removed_source_frames"]:
        spans.append((cursor, begin))
        cursor = end
    spans.append((cursor, total))
    pcm = array.array("h")
    peak, clipped = 0.0, 0
    fade = round(.012 * RATE)
    for n, (begin, end) in enumerate(spans):
        a, b = begin * RATE // FPS, end * RATE // FPS
        for frame in range(a, b):
            gain = 1.0
            if n and frame < a + fade:
                gain *= math.sin((frame - a) / fade * math.pi / 2)
            if n < len(spans) - 1 and frame >= b - fade:
                gain *= math.sin((b - frame) / fade * math.pi / 2)
            for channel in (0, 1):
                value = bed[frame * 2 + channel] * gain
                peak = max(peak, abs(value))
                clipped += abs(value) > .98
                pcm.append(round(max(-.98, min(.98, value)) * 32767))
    if clipped:
        raise ValueError(f"Mix would clip {clipped} samples; adjust the voice/bed balance")
    with wave.open(str(target), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(pcm.tobytes())
    usage = sum(json.loads((ROOT / j["output"]).with_suffix(".json").read_text())["usage"].get("usage_characters", 0)
                for j in plan["jobs"] if j.get("generate", True))
    report = {"input_sha256": signature.hexdigest(), "voices": timing, "peak_dbfs": 20 * math.log10(peak),
              "clipped_samples": clipped, "duration": len(pcm) / (2 * RATE), "new_tts_usage_characters": usage,
              "new_tts_estimate_cny": usage * 3.5 / 10000,
              "total_estimate_cny": plan["previous_cost_cny"] + plan["new_video_estimate_cny"] + usage * 3.5 / 10000,
              "epilogue_source": str(BASE), "epilogue_mix_gain": 1.0}
    if "dialogue_line_count" in plan:
        report.pop("epilogue_mix_gain")
        expected = {line["key"] for scene in tl["scenes"] for line in scene["lines"]}
        covered = {job["id"] for job in jobs}
        if expected - covered or any(job["id"].startswith("prologue_") for job in jobs):
            raise ValueError("Incomplete dialogue or an unwanted prologue voice")
        greeting_start, greeting_end = (round(t * RATE) for t in plan["preserved_hello_world_source_seconds"])
        if any(gain != 1.0 for gain in duck[greeting_start:greeting_end]):
            raise ValueError("New voices change the approved greeting's mix")
        report.update(dialogue_lines_covered=len(expected), missing_dialogue_lines=[],
                      prologue_voice=False, hello_world_mix_gain=1.0)
    state.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Verified mix:", report["duration"], "seconds; peak", report["peak_dbfs"], "dBFS; cost", report["total_estimate_cny"], flush=True)
    return target


def main():
    global WORK, OUTPUT, PREVIEW
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mix-only", action="store_true")
    parser.add_argument("--full-dub", action="store_true", help="Use the full-dub plan over the existing v13 picture")
    args = parser.parse_args()
    if args.full_dub:
        WORK = ROOT / "out/full-dub-edit"
        OUTPUT = ROOT / "out/red-error-final-v14-full-dub.mp4"
        PREVIEW = ROOT / "out/video-preview/red-error-v14-first-three-minutes.mp4"
    WORK.mkdir(parents=True, exist_ok=True)
    plan = json.loads((ROOT / ("audio/full-dub/manifest.json" if args.full_dub else "audio/opening/manifest.json")).read_text())
    total = int(probe(BASE)["nb_frames"])
    mixed = mix(plan, total)
    if args.mix_only:
        return
    if args.full_dub:
        expected = total - sum(b - a for a, b in plan["removed_source_frames"])
        picture = ROOT / plan["picture_source"]
        verify(picture, expected)
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(picture), "-i", str(mixed),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(OUTPUT)])
        verify(OUTPUT, expected)
        # Reuse the verified preview picture to avoid another video encode.
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(ROOT / "out/video-preview/red-error-v13-first-three-minutes.mp4"),
             "-i", str(OUTPUT), "-map", "0:v:0", "-map", "1:a:0", "-t", "180", "-c", "copy",
             "-movflags", "+faststart", str(PREVIEW)])
        verify(PREVIEW, 180 * FPS)
        for path in (OUTPUT, PREVIEW):
            run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"])
        def picture_hash(path):
            return subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                "-map", "0:v:0", "-c:v", "copy", "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
        before, after = picture_hash(picture), picture_hash(OUTPUT)
        if before != after:
            raise ValueError("Picture packets changed during dubbing")
        report = {"output": str(OUTPUT), "preview": str(PREVIEW), "frames": expected, "duration": expected / FPS,
                  "full_decode": "passed", "picture_packets_sha256": after, "dialogue_lines": plan["dialogue_line_count"],
                  "prologue_voice": False, "hello_world_preserved": True}
        (WORK / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print("Verified:", OUTPUT, PREVIEW, flush=True)
        return
    source = WORK / "opening-source.mp4"
    sources = ["web/engine.js", "web/ui.js", "web/timeline.js", "web/video/clips.js", "scripts/capture.js"]
    signature = hashlib.sha256(b"".join((ROOT / p).read_bytes() for p in sources)).hexdigest()
    state = WORK / "picture-source.json"
    if not (source.exists() and state.exists() and json.loads(state.read_text()).get("sha256") == signature):
        run(["node", "scripts/capture.js", "0", str(PREFIX / FPS), str(source), "9341"])
        verify(source, PREFIX)
        state.write_text(json.dumps({"sha256": signature}) + "\n")
    spans, cursor = [], 0
    for begin, end in plan["removed_source_frames"]:
        spans.append((cursor, begin, source))
        cursor = end
    spans += [(cursor, PREFIX, source), (PREFIX, total, BASE)]
    files = []
    for i, (begin, end, video) in enumerate(spans):
        part = WORK / f"part-{i:02d}.mp4"
        files.append(part)
        run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(begin / FPS), "-i", str(video),
             "-map", "0:v:0", "-an", "-frames:v", str(end - begin), "-vf", "setsar=1",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(part)])
        verify(part, end - begin)
    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in files))
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(mixed), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(OUTPUT)])
    expected = total - sum(b - a for a, b in plan["removed_source_frames"])
    verify(OUTPUT, expected)
    run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(OUTPUT), "-t", "180", "-frames:v", str(180 * FPS),
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy",
         "-movflags", "+faststart", str(PREVIEW)])
    verify(PREVIEW, 180 * FPS)
    for path in (OUTPUT, PREVIEW):
        run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"])
    report = {"output": str(OUTPUT), "preview": str(PREVIEW), "frames": expected, "duration": expected / FPS,
              "source_removed_seconds": (total - expected) / FPS, "full_decode": "passed"}
    (WORK / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified:", OUTPUT, PREVIEW, flush=True)


if __name__ == "__main__":
    main()
