#!/usr/bin/env python3
"""Submit or resume the approved H3 shot manifest with a conservative CNY cap."""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "out/video-preview"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit-only", action="store_true")
    parser.add_argument("--wait", type=int, default=20)
    parser.add_argument("--manifest", type=pathlib.Path, default=MEDIA / "h3-key-shots.json")
    args = parser.parse_args()
    plan = json.loads(args.manifest.read_text())
    # Include all China submission records, including an ambiguous submission.
    committed = plan.get("other_committed_cost", 0)
    existing = set()
    for meta in MEDIA.glob("*.json"):
        item = json.loads(meta.read_text())
        if item.get("base_url") != "https://api.minimax.cn":
            continue
        cost = item.get("estimated_output_cost", {})
        if cost.get("currency") == "CNY":
            committed += cost["amount"]
            existing.add(meta.stem)
    extra = sum(job["duration"] * plan["price_per_second"]
                for job in plan["jobs"] if job["name"] not in existing)
    if committed + extra > plan["budget"] + 1e-6:
        raise SystemExit(f"Budget exceeded: {committed + extra:.2f} CNY")
    print(f"Conservative total commitment: {committed + extra:.2f}/{plan['budget']} CNY", flush=True)
    pending = False
    for job in plan["jobs"]:
        command = [sys.executable, str(ROOT / "scripts/gen-video.py"), "--region", "china",
                   "--image", str(ROOT / "web/img_hd" / (job["image"] + ".jpg")),
                   "--prompt-file", str(MEDIA / (job["name"] + ".prompt.txt")),
                   "--out", str(MEDIA / (job["name"] + ".mp4")),
                   "--duration", str(job["duration"]), "--resolution", plan["resolution"],
                   "--wait", str(args.wait)]
        if args.submit_only:
            command.append("--submit-only")
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode not in (0, 2):
            return result.returncode
        pending |= result.returncode == 2
    return 2 if pending else 0


if __name__ == "__main__":
    sys.exit(main())
