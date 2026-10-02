#!/usr/bin/env python3
"""Create a short reel of the edited shots with the original film sound."""
import json
import argparse
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK = ROOT / "out/h3-edit"
MOVIE = ROOT / "out/red-error-final-v12-h3.mp4"
OUTPUT = ROOT / "out/video-preview/h3-key-shots-reel.mp4"


def main():
    global WORK, MOVIE, OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emotion", action="store_true")
    args = parser.parse_args()
    if args.emotion:
        WORK = ROOT / "out/emotion-edit"
        MOVIE = ROOT / "out/red-error-final-v16-emotion.mp4"
        OUTPUT = ROOT / "out/video-preview/red-error-v16-emotion-reel.mp4"
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite {OUTPUT}")
    plan = json.loads((WORK / "verification.json").read_text())
    if args.emotion:
        parts = json.loads((WORK / "picture-plan.json").read_text())
        scenes = {s["id"]: s for s in json.loads((ROOT / "audio/timeline.json").read_text())["scenes"]}
        frames = json.loads((WORK / "manifest.json").read_text())["removed_source_frames"]
        def edited(time):
            frame = round(time * 24)
            return frame - sum(max(0, min(frame, b) - a) for a, b in frames if frame > a)
        spans = []
        for start, end, generated in parts:
            if not generated:
                continue
            if not spans:
                start = edited(scenes["c3_a"]["t0"])
            elif start / 24 > 465:
                start = edited(scenes["ep_c"]["t0"])
                end = edited(scenes["ep_c"]["t0"] + scenes["ep_c"]["dur"])
            elif 380 < start / 24 < 400:
                start = edited(scenes["c6_c"]["t0"])
                end = edited(scenes["c6_c"]["t0"] + scenes["c6_c"]["dur"])
            else:
                start = max(0, start - 6)
            spans.append((start, end, True))
        plan = {"parts": spans}
    inputs, filters, streams = [], [], []
    for start, end, generated in plan["parts"]:
        if not generated:
            continue
        # The epilogue reel begins when typing starts, after the dialogue cards.
        if not args.emotion and start / 24 > 470:
            start += round(10.68 * 24)
        n = len(streams)
        inputs += ["-ss", str(start / 24), "-t", str((end - start) / 24), "-i", str(MOVIE)]
        filters += [f"[{n}:v]setpts=PTS-STARTPTS[v{n}]",
                    f"[{n}:a]atrim=duration={(end - start) / 24},asetpts=PTS-STARTPTS[a{n}]"]
        streams.append(f"[v{n}][a{n}]")
    filters.append("".join(streams) + f"concat=n={len(streams)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUTPUT)], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(OUTPUT), "-f", "null", "-"], check=True)
    print("Verified reel:", OUTPUT)


if __name__ == "__main__":
    main()
