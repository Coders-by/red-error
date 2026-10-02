#!/usr/bin/env python3
"""MiniMax H3 image-to-video trial; credentials stay in .minimax.

Existing task metadata is resumed without submitting another paid request.
"""
import argparse
import base64
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASES = {"global": "https://api.minimax.io", "china": "https://api.minimax.cn"}


class VideoError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise VideoError("API redirect refused; credentials were not forwarded")


def api(path, key, payload=None, base=BASES["global"]):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(base + path, data=data, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read(4096).decode(errors="replace").replace(key, "[REDACTED]")
        raise VideoError(f"HTTP {error.code}: {detail}") from None
    except urllib.error.URLError as error:
        raise VideoError(f"Network error: {error.reason}") from None
    base = result.get("base_resp", {})
    if base.get("status_code", 0) != 0:
        raise VideoError(json.dumps(base).replace(key, "[REDACTED]"))
    return result


def image_input(path, role="first_frame"):
    raw = path.read_bytes()
    if not raw or len(raw) > 30 * 1024 * 1024:
        raise VideoError("Input image must be nonempty and no larger than 30 MB")
    suffix = path.suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        raise VideoError("Use a JPEG, PNG or WebP input")
    mime = "jpeg" if suffix in (".jpg", ".jpeg") else suffix[1:]
    return {"type": "image_url", "role": role,
            "image_url": {"url": f"data:image/{mime};base64," + base64.b64encode(raw).decode()}}


def save(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def download(url, output):
    if urllib.parse.urlsplit(url).scheme != "https":
        raise VideoError("Video download must use HTTPS")
    part = output.with_suffix(".part.mp4")
    # Media downloads use a separate request with no API credentials.
    with urllib.request.urlopen(url, timeout=60) as response, part.open("wb") as target:
        if urllib.parse.urlsplit(response.url).scheme != "https":
            raise VideoError("Insecure media redirect")
        shutil.copyfileobj(response, target)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                            "-of", "json", str(part)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    if not any(s.get("codec_type") == "video" for s in info["streams"]):
        raise VideoError("Downloaded file has no video stream")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(part),
                    "-f", "null", "-"], check=True)
    part.replace(output)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-file", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--key-file", type=pathlib.Path, default=ROOT / ".minimax")
    parser.add_argument("--region", choices=BASES, default="global")
    parser.add_argument("--duration", type=int, choices=range(4, 16), default=5)
    parser.add_argument("--resolution", choices=("768P", "2K"), default="768P")
    parser.add_argument("--wait", type=int, default=50, help="Polling window in seconds; pending exits 2")
    parser.add_argument("--submit-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.wait < 0 or args.out.suffix.lower() != ".mp4":
        raise VideoError("Use a nonnegative polling window and an .mp4 output")
    prompt = args.prompt_file.read_text().strip()
    if not prompt or len(prompt) > 7000:
        raise VideoError("Prompt must contain 1 to 7000 characters")
    payload = {"model": "MiniMax-H3", "content": [{"type": "text", "text": prompt},
               image_input(args.image)], "resolution": args.resolution,
               "duration": args.duration, "ratio": "adaptive"}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    base = BASES[args.region]
    record = {"provider": "MiniMax official API", "base_url": base,
              "model": payload["model"], "image": str(args.image.resolve()),
              "image_sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(),
              "prompt": prompt, "resolution": args.resolution, "duration": args.duration,
              "request_sha256": fingerprint,
              "estimated_output_cost": {"currency": "CNY" if args.region == "china" else "USD",
                  "amount": args.duration * ((.5 if args.resolution == "768P" else .8)
                             if args.region == "china" else (.08 if args.resolution == "768P" else .13))}}
    if args.dry_run:
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    if not all(shutil.which(command) for command in ("ffprobe", "ffmpeg")):
        raise VideoError("ffmpeg and ffprobe are required")
    key = args.key_file.read_text().strip()
    if not key or any(c.isspace() for c in key):
        raise VideoError("Key file must contain exactly one API key")
    meta = args.out.with_suffix(".json")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if meta.exists():
        record = json.loads(meta.read_text())
        if record.get("request_sha256") != fingerprint or record.get("base_url") != base:
            raise VideoError("Inputs changed; use a new output filename for a new take")
        if args.out.exists():
            if record.get("video_sha256") != hashlib.sha256(args.out.read_bytes()).hexdigest():
                raise VideoError("Existing video checksum does not match metadata")
            print("Verified existing video:", args.out)
            return 0
        if not record.get("task_id"):
            raise VideoError("Previous submission has no task ID; inspect its status before retrying")
    else:
        if args.out.exists():
            raise VideoError("Refusing to overwrite a video without task metadata")
        # Persist intent before POST: an ambiguous timeout must not create duplicate paid tasks.
        record.update(status="submitting", submitted_at=time.time())
        save(meta, record)
        try:
            result = api("/v2/video_generation", key, payload, base=base)
            task_id = result.get("task_id")
            if not isinstance(task_id, (str, int)) or not str(task_id).isalnum():
                raise VideoError("Create response did not contain a valid task ID")
        except (VideoError, TimeoutError, json.JSONDecodeError) as error:
            record.update(status="submission_unconfirmed", error=str(error).replace(key, "[REDACTED]"))
            save(meta, record)
            raise
        record.update(task_id=str(task_id), status="queued")
        save(meta, record)
        print("Submitted task:", task_id, flush=True)
    if args.submit_only:
        return 0
    deadline = time.monotonic() + args.wait
    while True:
        result = api("/v2/query/video_generation/" + record["task_id"], key, base=base)
        task = result.get("task", {})
        status = task.get("status")
        if status not in ("queued", "running", "succeeded", "failed", "cancelled"):
            raise VideoError("Unexpected task response")
        record.update(status=status, task=json.loads(json.dumps(task).replace(key, "[REDACTED]")))
        save(meta, record)
        print("Task status:", status, flush=True)
        if status in ("failed", "cancelled"):
            raise VideoError("Generation " + status + "; see task metadata")
        if status == "succeeded":
            url = task.get("content", {}).get("url")
            if not url:
                raise VideoError("Successful task has no video URL")
            record["probe"] = download(url, args.out)
            record["video_sha256"] = hashlib.sha256(args.out.read_bytes()).hexdigest()
            record["verified_at"] = time.time()
            save(meta, record)
            print("Decoded and verified:", args.out)
            return 0
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print("Still pending; rerun the same command to resume without another generation")
            return 2
        time.sleep(min(10, remaining))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (VideoError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print("Error:", error, file=sys.stderr)
        sys.exit(1)
