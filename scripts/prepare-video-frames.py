#!/usr/bin/env python3
"""Prepare muted deterministic JPEG frame sequences from verified H3 outputs."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "out/video-preview"
TARGET = ROOT / "web/video"


def main():
    plan = json.loads((MEDIA / "h3-key-shots.json").read_text())
    jobs = plan["jobs"] + [{"name": "h3-rooftop-close-v1-cn", "duration": 5}]
    opening = MEDIA / "h3-opening-shots.json"
    if opening.exists():
        jobs += json.loads(opening.read_text())["jobs"]
    emotion = MEDIA / "h3-emotion-shots.json"
    if emotion.exists():
        jobs += json.loads(emotion.read_text())["jobs"]
    manifest = {}
    for job in jobs:
        name = job["name"]
        video = MEDIA / (name + ".mp4")
        meta = json.loads(video.with_suffix(".json").read_text())
        digest = hashlib.sha256(video.read_bytes()).hexdigest()
        if meta.get("status") != "succeeded" or meta.get("video_sha256") != digest:
            raise ValueError(f"Unverified video: {name}")
        directory = TARGET / name
        count = job["duration"] * 24
        state = directory / "source.json"
        expected = {"sha256": digest, "frames": count, "fps": 24, "width": 1920, "height": 816}
        cached = state.exists() and json.loads(state.read_text()) == expected
        if not cached or len(list(directory.glob("*.jpg"))) != count:
            directory.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(video),
                            "-an", "-vf", "fps=24,scale=1920:816:force_original_aspect_ratio=increase,crop=1920:816",
                            "-frames:v", str(count), "-q:v", "2", "-start_number", "0",
                            str(directory / "%05d.jpg")], check=True)
            if len(list(directory.glob("*.jpg"))) != count:
                raise ValueError(f"Incomplete frames: {name}")
            state.write_text(json.dumps(expected, indent=2) + "\n")
        manifest[name] = {"dir": "video/" + name, "fps": 24, "frames": count}
        print(name, count, "frames", flush=True)
    (TARGET / "clips.js").write_text("window.CLIPS=" + json.dumps(manifest) + ";\n")


if __name__ == "__main__":
    main()
