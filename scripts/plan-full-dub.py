#!/usr/bin/env python3
"""Plan a complete dub, reusing approved takes and leaving the prologue silent."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    timeline = json.loads((ROOT / "audio/timeline.json").read_text())
    opening = json.loads((ROOT / "audio/opening/manifest.json").read_text())
    selected = json.loads((ROOT / "audio/dub-preview/minimax-elder-selected.json").read_text())
    reusable = {j["id"]: j for j in opening["jobs"] if not j["id"].startswith("prologue_") and j["role"] != "萨姐"}
    reusable.update({j["id"]: j for j in selected["jobs"]})
    reusable["c6_c_5"] = {"output": "audio/dub-preview/generated/minimax-young-dialogue.wav",
                           "voice_id": "male-qn-jingying", "text": "老亚……"}
    voices = {"老亚": selected["selection"]["voice_id"], "萨姐": "Chinese (Mandarin)_Wise_Women",
              "米卡": "Chinese (Mandarin)_Unrestrained_Young_Man", "达总": "Chinese (Mandarin)_Reliable_Executive",
              "马迭代": "male-qn-jingying", "米尔顿": "Chinese (Mandarin)_Sincere_Adult",
              "HR": "female-chengshu", "孩子": "clever_boy"}
    jobs = []
    for scene in timeline["scenes"]:
        for i, line in enumerate(scene["lines"]):
            key, who = line["key"], line["who"]
            end = scene["lines"][i + 1]["st"] - .16 if i + 1 < len(scene["lines"]) else scene["dur"] - .3
            job = {"id": key, "text": line["t"], "role": who, "voice_id": voices[who],
                   "source_start": scene["t0"] + line["st"], "source_end": scene["t0"] + end,
                   "speed": 1.05 if who == "老亚" else .97 if who == "萨姐" else 1.0,
                   "pitch": 0, "emotion": "calm", "generate": key not in reusable,
                   "output": f"audio/full-dub/generated/minimax-full-{key}.wav"}
            if key in reusable:
                old = reusable[key]
                if old["text"] != job["text"]:
                    raise ValueError("Reused text differs: " + key)
                job.update({k: v for k, v in old.items() if k not in ("source_start", "source_end", "role")})
            jobs.append(job)
    jobs += [{**reusable[k], "generate": False} for k in ("journal", "ai_bridge")]
    expected = {line["key"] for scene in timeline["scenes"] for line in scene["lines"]}
    if not expected.issubset({j["id"] for j in jobs}) or len({j["id"] for j in jobs}) != len(jobs):
        raise ValueError("Incomplete or duplicate dialogue coverage")
    pending = [j for j in jobs if j["generate"]]
    estimate = sum(len(j["text"]) * 2 for j in pending) * 3.5 / 10000
    previous = json.loads((ROOT / "out/opening-edit/audio-verification.json").read_text())["total_estimate_cny"]
    if previous + estimate > opening["budget_cny"]:
        raise ValueError("Full dub would exceed the existing budget")
    plan = {"model": "speech-2.8-hd", "version": "v14", "jobs": jobs,
            "append_selected_jobs": False, "fps": opening["fps"], "removed_source_frames": opening["removed_source_frames"],
            "previous_cost_cny": previous, "new_video_estimate_cny": 0, "budget_cny": opening["budget_cny"],
            "prologue_voice": False, "preserved_hello_world_source_seconds": [493.43, 495.829],
            "dialogue_line_count": len(expected), "new_take_estimate_cny": estimate,
            "cast": voices, "picture_source": "out/red-error-final-v13-opening.mp4"}
    directory = ROOT / "audio/full-dub"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    (directory / "generate.json").write_text(json.dumps({"model": plan["model"], "jobs": pending}, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(expected)} dialogue lines covered; {len(jobs)-len(pending)} reused takes; {len(pending)} new takes; <= {estimate:.4f} CNY synthesis")


if __name__ == "__main__":
    main()
