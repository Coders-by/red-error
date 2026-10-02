#!/usr/bin/env python3
"""Qwen VoiceDesign: text + acting instruction -> WAV, using the public Gradio API.

Python 3.9+ standard library; ffmpeg for output conversion. See VOICE_GENERATION.md.
No browser automation, embedded credentials, or automatic generation retries.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "https://qwen-qwen3-tts.hf.space"
MAX_AUDIO_BYTES = 100 * 1024 * 1024


class VoiceError(Exception):
    pass


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audio_info(path):
    with wave.open(str(path), "rb") as audio:
        if not audio.getnframes() or audio.getcomptype() != "NONE":
            raise VoiceError("Empty or unsupported PCM WAV")
        frames = audio.readframes(audio.getnframes())
        if len(frames) != audio.getnframes() * audio.getnchannels() * audio.getsampwidth():
            raise VoiceError("Truncated WAV")
        return {"sample_rate": audio.getframerate(), "channels": audio.getnchannels(),
                "sample_width": audio.getsampwidth(),
                "duration_seconds": round(audio.getnframes() / audio.getframerate(), 6)}


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    """Do not forward credentials or generated-text requests to another host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        old = urllib.parse.urlsplit(req.full_url)
        new = urllib.parse.urlsplit(newurl)
        if (old.scheme, old.netloc) != (new.scheme, new.netloc):
            raise VoiceError("Cross-origin redirect refused; configure the direct endpoint")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GradioVoice:
    def __init__(self, base, timeout=300, api_name=None, speaker=None):
        self.base = base.rstrip("/")
        parsed = urllib.parse.urlsplit(self.base)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise VoiceError("Base URL must not contain credentials, query or fragment")
        if not parsed.hostname or not (parsed.scheme == "https" or
                parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
            raise VoiceError("Use HTTPS (HTTP is allowed only for localhost testing)")
        self.timeout, self.api_name = timeout, api_name or ("generate_custom_voice" if speaker else None)
        self.speaker = speaker
        self.token = os.environ.get("HF_TOKEN", "")
        self.opener = urllib.request.build_opener(SameOriginRedirect())
        self.schema = None

    def open(self, path, payload=None, timeout=None):
        url = path if path.startswith(("https://", "http://")) else self.base + path
        if urllib.parse.urlsplit(url)[:2] != urllib.parse.urlsplit(self.base)[:2]:
            raise VoiceError("Audio URL has a different origin; download refused")
        headers = {"User-Agent": "red-error-voice-cli/1.0"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=None if payload is None else json_bytes(payload), headers=headers)
        return self.opener.open(req, timeout=timeout or self.timeout)

    def get_json(self, path, payload=None):
        with self.open(path, payload) as response:
            return json.load(response)

    def discover(self):
        config = self.get_json("/config")
        prefix = config.get("api_prefix", "/gradio_api").rstrip("/")
        if prefix and not re.fullmatch(r"/[A-Za-z0-9_/-]+", prefix):
            raise VoiceError("Unrecognized Gradio API prefix")
        endpoints = self.get_json(prefix + "/info")["named_endpoints"]
        candidates = []
        for name, endpoint in endpoints.items():
            params = [p["parameter_name"] for p in endpoint["parameters"]]
            if self.api_name and name != "/" + self.api_name.strip("/"):
                continue
            canonical = ["instruct" if p == "voice_description" else p for p in params]
            accepted = ({"text", "language", "speaker", "instruct", "model_size"},) if self.speaker else (
                {"text", "instruct"}, {"text", "language", "instruct"})
            if len(canonical) != len(set(canonical)) or set(canonical) not in accepted:
                continue
            if self.speaker:
                allowed = next(p for p in endpoint["parameters"] if p["parameter_name"] == "speaker").get("type", {}).get("enum")
                if allowed and self.speaker not in allowed:
                    raise VoiceError("Speaker not offered by this endpoint: " + self.speaker)
            if not any(r.get("component", "").lower() == "audio" for r in endpoint.get("returns", [])):
                continue
            if not re.fullmatch(r"/[A-Za-z0-9_-]+", name):
                continue
            candidates.append({"api_name": name, "parameters": params,
                               "prefix": prefix, "gradio_version": config.get("version")})
        if len(candidates) != 1:
            raise VoiceError("Expected one text/instruct -> audio endpoint; use --api-name or inspect server schema")
        self.schema = candidates[0]
        return self.schema

    def synthesize(self, text, instruct, language, destination):
        schema = self.schema or self.discover()
        values = {"text": text, "instruct": instruct, "voice_description": instruct, "language": language,
                  "speaker": self.speaker, "model_size": "1.7B"}
        route = schema["prefix"] + "/call" + schema["api_name"]
        submission = self.get_json(route, {"data": [values[p] for p in schema["parameters"]]})
        event_id = submission.get("event_id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", event_id):
            raise VoiceError("Server did not return a valid generation event ID")
        print("submitted event=" + event_id + " (no automatic POST retry)", file=sys.stderr, flush=True)
        deadline = time.monotonic() + self.timeout
        result = None
        event, data = "", []
        with self.open(route + "/" + event_id) as response:
            for line in response:
                if time.monotonic() > deadline:
                    raise VoiceError("Generation timed out; event=" + event_id)
                line = line.decode("utf-8").rstrip("\r\n")
                if line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip())
                elif not line:
                    if event in {"complete", "error"}:
                        body = json.loads("\n".join(data)) if data else None
                        if event == "error":
                            raise VoiceError("Generation failed (event=" + event_id + "): " + str(body)[:500])
                        result = body
                        break
                    event, data = "", []
        if not isinstance(result, list):
            raise VoiceError("Stream closed without audio; event=" + event_id)
        files = [item for item in result if isinstance(item, dict) and (item.get("url") or item.get("path"))]
        if len(files) != 1:
            raise VoiceError("Expected one generated audio file, received: " + str(result)[:300])
        file = files[0]
        url = file.get("url") or (schema["prefix"] + "/file=" + urllib.parse.quote(file["path"], safe="/"))
        if not url.startswith(("https://", "http://", "/")):
            raise VoiceError("Invalid audio URL")
        total = 0
        with self.open(url) as response, destination.open("wb") as audio:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise VoiceError("Audio exceeds 100 MiB safety limit")
                audio.write(chunk)
        if not total:
            raise VoiceError("Downloaded empty audio")
        return {**schema, "event_id": event_id,
                "language_control": "explicit" if "language" in schema["parameters"] else "inferred from text"}


def resolve_job(text, preset, instruct, language, presets, reuse=False):
    if preset and preset not in presets:
        raise VoiceError("Unknown preset: " + preset)
    profile = presets.get(preset, {})
    text = (text or (profile.get("approved_text", "") if reuse else "")).strip()
    instruction = (instruct or profile.get("instruct", "")).strip()
    if not text or not instruction:
        raise VoiceError("Provide non-empty text and --preset or --instruct")
    if reuse and (text != profile.get("approved_text") or not profile.get("approved_audio") or instruct or language):
        raise VoiceError("--reuse-approved requires the unchanged approved text/preset, without instruction/language overrides")
    return {"text": text, "preset": preset or None, "instruct": instruction,
            "language": language or profile.get("language", "Chinese"),
            "approved_audio": profile.get("approved_audio") if reuse else None}


def render(job, out, client, presets_path, sample_rate=48000, force=False, dry_run=False):
    out = out.expanduser().resolve()
    if out.suffix.lower() != ".wav":
        raise VoiceError("Output must have a .wav extension")
    approved = job.get("approved_audio")
    source = (presets_path.parent / approved).resolve() if approved else None
    if source and source == out:
        raise VoiceError("Never overwrite the approved source audio")
    request = {**job, "mode": "reuse-approved" if source else "generate",
               "base_url": None if source else client.base,
               "api_name": None if source else client.api_name,
               "sample_rate": None if source else sample_rate,
               "source_sha256": digest(source) if source else None}
    if client.speaker and not source:
        request.update(speaker=client.speaker, model_size="1.7B")
    sidecar = out.with_suffix(".json")
    if dry_run:
        print(json.dumps({"dry_run": True, "output": str(out), "request": request}, ensure_ascii=False))
        return "dry-run"
    if (out.exists() or sidecar.exists()) and not force:
        try:
            saved = json.loads(sidecar.read_text())
            if saved.get("request") == request and saved.get("sha256") == digest(out):
                audio_info(out)
                print("skip " + str(out), file=sys.stderr)
                return "skip"
        except (OSError, ValueError, wave.Error, VoiceError):
            pass
        raise VoiceError("Existing output differs or lacks verified metadata; choose another --out or use --force: " + str(out))
    if not source and not shutil.which("ffmpeg"):
        raise VoiceError("ffmpeg is required to export 48 kHz PCM WAV")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".voice-", dir=out.parent) as temp:
        temp = Path(temp)
        wav = temp / "voice.wav"
        if source:
            shutil.copyfile(source, wav)
            provenance = {"source": str(source), "note": "Byte-identical approved asset; no network call"}
        else:
            raw = temp / "download.audio"
            provenance = client.synthesize(job["text"], job["instruct"], job["language"], raw)
            result = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(raw),
                                     "-map", "0:a:0", "-ac", "1", "-ar", str(sample_rate),
                                     "-c:a", "pcm_s16le", str(wav)], capture_output=True, text=True)
            if result.returncode:
                raise VoiceError("Audio conversion failed: " + result.stderr[-600:])
            provenance["download_sha256"] = digest(raw)
        metadata = {"created_at": datetime.now(timezone.utc).isoformat(), "request": request,
                    "provenance": provenance, "audio": audio_info(wav), "sha256": digest(wav)}
        meta = temp / "voice.json"
        meta.write_bytes(json_bytes(metadata))
        os.replace(wav, out)
        os.replace(meta, sidecar)
    print(json.dumps({"output": str(out), **metadata["audio"], "sha256": metadata["sha256"]}, ensure_ascii=False))
    return "created"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    source.add_argument("--batch", type=Path, help="TSV: id, text, preset, instruct; optional language")
    parser.add_argument("ids", nargs="*", help="Selected batch IDs, like gen-shots.py")
    parser.add_argument("--preset", default="red-error-soft")
    parser.add_argument("--presets", type=Path, default=ROOT / "voices.json")
    parser.add_argument("--instruct", help="Full voice/acting instruction; overrides preset")
    parser.add_argument("--language", help="Used only if the server exposes a language parameter")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "audio/generated")
    parser.add_argument("--base-url", default=os.environ.get("TTS_BASE", DEFAULT_BASE))
    parser.add_argument("--api-name", default=os.environ.get("TTS_API_NAME"))
    parser.add_argument("--speaker", help="Fixed Qwen CustomVoice speaker; selects the CustomVoice endpoint")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--sample-rate", type=int, choices=[24000, 44100, 48000], default=48000)
    parser.add_argument("--reuse-approved", action="store_true", help="Copy approved recording exactly, no synthesis")
    parser.add_argument("--inspect-api", action="store_true", help="Read endpoint definition only, no generation")
    parser.add_argument("--dry-run", action="store_true", help="Validate local requests without writing or network")
    parser.add_argument("--force", action="store_true", help="Explicitly replace output WAV and metadata")
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0:
            raise VoiceError("--timeout must be positive")
        client = GradioVoice(args.base_url, args.timeout, args.api_name, speaker=args.speaker)
        if args.inspect_api:
            if args.dry_run:
                raise VoiceError("--inspect-api needs network; do not combine with --dry-run")
            print(json.dumps(client.discover(), ensure_ascii=False, indent=2))
            return 0
        presets_path = args.presets.expanduser().resolve()
        presets = json.loads(presets_path.read_text(encoding="utf-8"))
        jobs = []
        if args.batch:
            if args.out or args.reuse_approved or args.instruct or args.language:
                raise VoiceError("Batch uses --out-dir and row-level instruct/language; no --out or --reuse-approved")
            with args.batch.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, delimiter="\t")
                if not {"id", "text"}.issubset(reader.fieldnames or []):
                    raise VoiceError("Batch TSV needs id and text headers")
                seen = set()
                for row in reader:
                    sid = (row.get("id") or "").strip()
                    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", sid) or sid in seen:
                        raise VoiceError("Invalid or duplicate batch ID: " + sid)
                    seen.add(sid)
                    if args.ids and sid not in args.ids:
                        continue
                    job = resolve_job(row.get("text"), row.get("preset") or args.preset,
                                      row.get("instruct"), row.get("language"), presets)
                    jobs.append((job, args.out_dir / (sid + ".wav")))
                if set(args.ids) - seen:
                    raise VoiceError("Unknown batch IDs: " + ", ".join(sorted(set(args.ids) - seen)))
            if not jobs:
                raise VoiceError("No batch rows selected")
        else:
            if args.ids or not args.out:
                raise VoiceError("Single generation needs --out; positional IDs require --batch")
            text = args.text_file.read_text(encoding="utf-8") if args.text_file else args.text
            job = resolve_job(text, args.preset, args.instruct, args.language, presets, args.reuse_approved)
            jobs.append((job, args.out))
        if args.reuse_approved and args.speaker:
            raise VoiceError("--speaker cannot change an approved reused recording")
        for job, out in jobs:
            render(job, out, client, presets_path, args.sample_rate, args.force, args.dry_run)
        return 0
    except (VoiceError, OSError, ValueError, KeyError, TypeError, wave.Error) as exc:
        message = str(exc)
        if os.environ.get("HF_TOKEN"):
            message = message.replace(os.environ["HF_TOKEN"], "[redacted]")
        print("ERROR: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
