#!/usr/bin/env python3
"""Generate and verify custom elder voice-design previews without activating TTS."""
import hashlib
import argparse
import json
import pathlib
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENDPOINT = "https://api.minimax.cn/v1/voice_design"
PLAN = ROOT / "audio/dub-preview/minimax-elder-design.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Refusing to forward credentials on redirect")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=pathlib.Path, default=PLAN)
    parser.add_argument("--report", type=pathlib.Path, default=ROOT / "out/voice-preview/minimax-elder-design-report.json")
    args = parser.parse_args()
    plan = json.loads(args.manifest.read_text())
    key = (ROOT / ".minimax").read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise ValueError("Key file must contain one API key")
    report = {"provider": "MiniMax voice design", "endpoint": ENDPOINT, "variants": []}
    for variant in plan["variants"]:
        out = ROOT / variant["output"]
        meta = out.with_suffix(".json")
        raw = out.with_suffix(".trial.mp3")
        payload = {"prompt": variant["prompt"], "preview_text": plan["preview_text"]}
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if meta.exists():
            record = json.loads(meta.read_text())
            if record["request_sha256"] != fingerprint:
                raise ValueError("Changed design requires a new output filename")
            if out.exists():
                if record.get("sha256") != digest(out):
                    raise ValueError("Preview checksum mismatch")
                print("Verified existing:", out, flush=True)
                report["variants"].append(record)
                continue
            if not record.get("voice_id") or not raw.exists() or record.get("raw_sha256") != digest(raw):
                raise ValueError("Prior submission unresolved; inspect platform history before retrying")
        else:
            if out.exists() or raw.exists():
                raise ValueError("Refusing to overwrite a preview without metadata")
            out.parent.mkdir(parents=True, exist_ok=True)
            # Record intent before POST, preventing an ambiguous response from creating duplicates.
            record = {"label": variant["label"], "request": payload, "request_sha256": fingerprint,
                      "status": "submitting", "submitted_at": time.time(), "output": str(out)}
            save(meta, record)
            request = urllib.request.Request(ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
            try:
                with urllib.request.build_opener(NoRedirect()).open(request, timeout=120) as response:
                    result = json.load(response)
                if result.get("base_resp", {}).get("status_code", 0) != 0:
                    raise ValueError(json.dumps(result.get("base_resp"), ensure_ascii=False))
                voice_id, audio = result.get("voice_id"), result.get("trial_audio")
                if not isinstance(voice_id, str) or not voice_id or not isinstance(audio, str):
                    raise ValueError("Voice design response is missing voice ID or preview")
                data = bytes.fromhex(audio)
                if not data:
                    raise ValueError("Empty voice preview")
                raw.write_bytes(data)
                record.update(status="designed", voice_id=voice_id, raw_sha256=digest(raw))
                save(meta, record)
            except Exception as error:
                record.update(status="submission_unconfirmed", error=str(error).replace(key, "[REDACTED]"))
                save(meta, record)
                raise ValueError(record["error"]) from None
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(raw),
            "-af", "loudnorm=I=-19:TP=-2:LRA=8", "-ac", "1", "-ar", "48000",
            "-c:a", "pcm_s16le", str(out)], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(out), "-f", "null", "-"], check=True)
        info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "json", str(out)]))
        text = plan["preview_text"]
        characters = len(text) + len(re.findall(r"[\u4e00-\u9fff]", text))
        record.update(status="verified", sha256=digest(out), duration=float(info["format"]["duration"]),
            full_decode="passed", loudness_target_lufs=-19, sample_rate=48000, channels=1,
            estimated_preview_cny=round(characters * 2 / 10000, 6),
            billing_note="Estimated character count, no billing receipt. Design activation fee: 9.90 CNY on first TTS use; not activated by this script.")
        save(meta, record)
        report["variants"].append(record)
        print("Verified design", variant["label"], "duration", record["duration"], "voice_id", record["voice_id"], flush=True)
    report.update(estimated_preview_cny=sum(r["estimated_preview_cny"] for r in report["variants"]),
        tts_activation_count=0, billing_verified=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    save(args.report, report)
    print("Preview estimate CNY:", report["estimated_preview_cny"], flush=True)


if __name__ == "__main__":
    main()
