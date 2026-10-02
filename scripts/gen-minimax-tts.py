#!/usr/bin/env python3
"""Generate small, resumable MiniMax T2A audition takes.

The API key is read from .minimax and never printed or stored in metadata.
"""
import argparse
import base64
import hashlib
import json
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = "https://api.minimax.cn"


class TtsError(Exception):
    pass


class TtsRateLimit(TtsError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request(key, payload):
    req = urllib.request.Request(
        BASE + "/v1/t2a_v2",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read(2048).decode(errors="replace").replace(key, "[REDACTED]")
        raise TtsError(f"HTTP {error.code}: {detail}") from None
    except urllib.error.URLError as error:
        raise TtsError(f"Network error: {error.reason}") from None
    base = result.get("base_resp", {})
    if base.get("status_code") == 1002:
        raise TtsRateLimit("Provider rejected request due to rate limit")
    if base.get("status_code", 0) != 0:
        raise TtsError(json.dumps(base, ensure_ascii=False))
    audio = result.get("data", {}).get("audio")
    if not isinstance(audio, str) or not audio:
        raise TtsError("T2A response did not contain hex audio")
    try:
        raw = bytes.fromhex(audio)
    except ValueError:
        raise TtsError("T2A response audio was not valid hex") from None
    if not raw:
        raise TtsError("T2A response contained empty audio")
    return raw, result.get("extra_info", {}), result.get("trace_id")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=pathlib.Path, default=ROOT / "audio/dub-preview/minimax-voices.json")
    ap.add_argument("--wait", action="store_true", help="kept for command symmetry; T2A is synchronous")
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text())
    key = (ROOT / ".minimax").read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise TtsError(".minimax must contain exactly one API key")
    total_chars = 0
    for job in manifest["jobs"]:
        out = ROOT / job["output"]
        meta = out.with_suffix(".json")
        payload = {
            "model": manifest.get("model", "speech-2.8-hd"),
            "text": job["text"],
            "stream": False,
            "voice_setting": {
                "voice_id": job["voice_id"],
                "speed": job.get("speed", 1.0),
                "vol": 1,
                "pitch": job.get("pitch", 0),
                "emotion": job.get("emotion", "calm"),
            },
            "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3", "channel": 1},
            "language_boost": "Chinese",
            "subtitle_enable": False,
        }
        fingerprint = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if out.exists() and meta.exists():
            saved = json.loads(meta.read_text())
            if saved.get("request_sha256") == fingerprint and saved.get("audio_sha256") == sha(out):
                print("Verified existing:", out)
                total_chars += len(job["text"])
                continue
            raise TtsError("Existing output differs; choose a new take filename: " + str(out))
        out.parent.mkdir(parents=True, exist_ok=True)
        temp = out.with_suffix(".download.mp3")
        intent = out.with_suffix(".request.json")
        if intent.exists():
            saved = json.loads(intent.read_text())
            if saved.get("request_sha256") != fingerprint or not temp.exists() or "usage" not in saved:
                raise TtsError("Unconfirmed prior request; refusing a duplicate charge: " + str(intent))
            usage, trace_id = saved["usage"], saved["trace_id"]
        else:
            if out.exists() or temp.exists():
                raise TtsError("Unverified existing take: " + str(out))
            intent.write_text(json.dumps({"request_sha256": fingerprint, "status": "submitting"}) + "\n")
            for attempt in range(10):
                try:
                    raw, usage, trace_id = request(key, payload)
                    break
                except TtsRateLimit:
                    if attempt == 9:
                        intent.unlink()
                        raise
                    print("Rate-limited before generation; waiting to resume", flush=True)
                    time.sleep(8)
            temp.write_bytes(raw)
            intent.write_text(json.dumps({"request_sha256": fingerprint, "status": "received",
                                          "usage": usage, "trace_id": trace_id}) + "\n")
        # Decode the provider MP3 fully before accepting the take.
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", str(temp),
                        "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", str(out)], check=True)
        temp.unlink(missing_ok=True)
        record = {
            "provider": "MiniMax official API",
            "base_url": BASE,
            "model": payload["model"],
            "voice_id": job["voice_id"],
            "voice_setting": payload["voice_setting"],
            "text": job["text"],
            "request_sha256": fingerprint,
            "trace_id": trace_id,
            "usage": usage,
            "audio": {"sample_rate": 48000, "channels": 1},
            "audio_sha256": sha(out),
        }
        meta.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        intent.unlink()
        total_chars += len(job["text"])
        print("Generated:", out, json.dumps(usage, ensure_ascii=False))
        time.sleep(6)
    print(f"Audition characters: {total_chars}")


if __name__ == "__main__":
    try:
        main()
    except (TtsError, OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit("Error: " + str(error))
