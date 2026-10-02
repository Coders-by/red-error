#!/usr/bin/env python3
"""Build a short visual audition with MiniMax voices over the existing v12 mix."""
import argparse
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIDEO = ROOT / "out/red-error-final-v12-h3.mp4"
OUT = ROOT / "out/video-preview"
VOICE = ROOT / "audio/dub-preview/generated"
FPS = 24

# Keep enough surrounding picture to judge whether spoken narration improves comprehension.
segments = [(272.7, 16.72), (332.02, 22.0), (386.62, 16.58)]
voice_starts = [1.5, 16.72 + 1.5, 16.72 + 22.0 + 0.8, 16.72 + 22.0 + 12.32]
voice_files = [
    VOICE / "minimax-hr-dialogue.wav",
    VOICE / "minimax-elder-narration.wav",
    VOICE / "minimax-elder-dialogue.wav",
    VOICE / "minimax-young-dialogue.wav",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elder", choices=("original", "D"), default="original")
    args = parser.parse_args()
    files, starts = list(voice_files), list(voice_starts)
    suffix = ""
    if args.elder == "D":
        suffix = "-D"
        plan = json.loads((ROOT / "audio/dub-preview/minimax-elder-selected.json").read_text())
        timeline = json.loads((ROOT / "audio/timeline.json").read_text())
        files = [voice_files[0], voice_files[3]]
        starts = [voice_starts[0], voice_starts[3]]
        for job in plan["jobs"]:
            scene = next(s for s in timeline["scenes"] if any(l["key"] == job["id"] for l in s["lines"]))
            line = next(l for l in scene["lines"] if l["key"] == job["id"])
            absolute = scene["t0"] + line["st"]
            offset = 0
            for begin, duration in segments:
                if begin <= absolute < begin + duration:
                    files.append(ROOT / job["output"])
                    starts.append(offset + absolute - begin)
                    break
                offset += duration
            else:
                raise ValueError("Line falls outside audition windows: " + job["id"])
        for path in files:
            record = json.loads(path.with_suffix(".json").read_text())
            if record["audio_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError("Unverified input: " + str(path))
    for path in [VIDEO, *files]:
        if not path.exists():
            raise SystemExit("Missing verified input: " + str(path))
    wav = OUT / f"minimax-dub-audition{suffix}.wav"
    mp4 = OUT / f"red-error-v12-minimax-dub-audition{suffix}.mp4"
    if wav.exists() and wav.stat().st_size > 0 or mp4.exists():
        raise SystemExit("Refusing to overwrite existing audition outputs")
    inputs = []
    for start, duration in segments:
        inputs += ["-ss", str(start), "-t", str(duration), "-i", str(VIDEO)]
    for path in files:
        inputs += ["-i", str(path)]
    filters = []
    for i in range(3):
        filters += [f"[{i}:v]setpts=PTS-STARTPTS[v{i}]",
                    f"[{i}:a]atrim=duration={segments[i][1]},asetpts=PTS-STARTPTS[a{i}]"]
    filters.append("[v0][v1][v2]concat=n=3:v=1:a=0[v]")
    filters.append("[a0][a1][a2]concat=n=3:v=0:a=1[base]")
    voice_labels = []
    for i, (path, start) in enumerate(zip(files, starts), 3):
        label = f"voice{i}"
        delay = round(start * 1000)
        level = "loudnorm=I=-19:TP=-2:LRA=8," if args.elder == "D" else "volume=1.12,"
        filters.append(f"[{i}:a]{level}aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay}[{label}]")
        voice_labels.append(f"[{label}]")
    filters.append("[base]volume=0.72[bed]")
    filters.append("[bed]" + "".join(voice_labels) +
                   f"amix=inputs={len(voice_labels)+1}:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.92[a]")
    graph = ";".join(filters)
    # Render the picture and the mixed audition audio together, then export a PCM copy.
    command = ["ffmpeg", "-nostdin", "-y", "-v", "error", *inputs,
               "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
               "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)]
    subprocess.run(command, check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(mp4),
                    "-map", "0:a:0", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav)], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(wav), "-f", "null", "-"], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(mp4), "-f", "null", "-"], check=True)
    report = {"elder": args.elder, "segments": segments, "voice_starts": starts,
              "voices": [str(p) for p in files], "duration": sum(d for _, d in segments),
              "video": str(mp4), "audio": str(wav), "full_decode": "passed"}
    (OUT / f"minimax-dub-audition{suffix}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Verified:", mp4)


if __name__ == "__main__":
    main()
