#!/usr/bin/env python3
"""Export equally normalized narration/dialogue samples for elder casting."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "audio/dub-preview/minimax-elder-ab.json"
OUT = ROOT / "out/voice-preview"


def main():
    plan = json.loads(MANIFEST.read_text())
    report = {"model": plan["model"], "variants": [], "billing_verified": False}
    usage = 0
    for variant in ("A", "B"):
        jobs = [j for j in plan["jobs"] if j["id"].startswith(f"elder-{variant}-")]
        paths = [ROOT / j["output"] for j in jobs]
        for path in paths:
            saved = json.loads(path.with_suffix(".json").read_text())
            if saved["audio_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError(f"Unverified input: {path}")
            usage += saved["usage"]["usage_characters"]
        output = OUT / f"minimax-elder-{variant}-casting.wav"
        if output.exists():
            raise SystemExit(f"Refusing to overwrite {output}")
        OUT.mkdir(parents=True, exist_ok=True)
        # Same loudness and a brief gap, so volume alone cannot decide the comparison.
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-i", str(paths[0]), "-i", str(paths[1]),
            "-filter_complex",
            "[0:a]apad=pad_dur=0.8[a0];[a0][1:a]concat=n=2:v=0:a=1,"
            "loudnorm=I=-19:TP=-2:LRA=8[a]",
            "-map", "[a]", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(output)
        ], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True)
        info = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(output)
        ]))
        report["variants"].append({
            "label": variant, "voice_id": jobs[0]["voice_id"],
            "speed": jobs[0]["speed"], "pitch": jobs[0]["pitch"], "emotion": jobs[0]["emotion"],
            "order": ["narration", "dialogue"], "output": str(output),
            "duration": float(info["format"]["duration"]), "full_decode": "passed",
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()
        })
        print("Verified:", output, flush=True)
    report.update(usage_characters=usage, estimated_cny=round(usage * 3.5 / 10000, 6))
    (OUT / "minimax-elder-casting.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("Estimated CNY:", report["estimated_cny"])


if __name__ == "__main__":
    main()
