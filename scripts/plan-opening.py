#!/usr/bin/env python3
"""Build the opening voice and edit manifests from the film's structured timeline."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS = 24


def main():
    tl = json.loads((ROOT / "audio/timeline.json").read_text())
    selected = json.loads((ROOT / "audio/dub-preview/minimax-elder-selected.json").read_text())
    voices = {"老亚": selected["selection"]["voice_id"],
              "萨姐": "female-yujie", "米卡": "Chinese (Mandarin)_Unrestrained_Young_Man",
              "达总": "Chinese (Mandarin)_Reliable_Executive", "马迭代": "male-qn-jingying"}
    jobs = []

    def add(key, text, who, start, end):
        jobs.append({"id": key, "text": text, "role": who, "voice_id": voices[who],
                     "speed": 1.05 if who == "老亚" else 1.0, "emotion": "calm",
                     "source_start": start, "source_end": end,
                     "output": f"audio/opening/generated/minimax-opening-{key}.wav"})

    for scene in tl["scenes"]:
        if scene["id"] == "c3_card":
            break
        for i, line in enumerate(scene["lines"]):
            end = scene["lines"][i + 1]["st"] - .16 if i + 1 < len(scene["lines"]) else scene["dur"] - .3
            add(line["key"], line["t"], line["who"], scene["t0"] + line["st"], scene["t0"] + end)
        for ui in scene["ui"]:
            if ui["type"] == "prologue":
                starts = [.5, 3.9, 7.4, 11.5, 15.7]
                for i, text in enumerate(ui["lines"]):
                    end = starts[i + 1] - .12 if i < 4 else 21.1
                    add(f"prologue_{i+1}", text, "老亚", scene["t0"] + starts[i], scene["t0"] + end)
            if ui["type"] == "journal":
                add("journal", "".join(ui["text"]), "老亚", scene["t0"] + 2.4, scene["t0"] + 14.5)
    # A brief voice bridge during the visible AI prompt makes the experiment legible by ear.
    scene = next(s for s in tl["scenes"] if s["id"] == "c2_d")
    add("ai_bridge", "那天夜里，阿迭偷偷打开了 AI。", "老亚", scene["t0"] + .9, scene["t0"] + 7.8)
    # Keep the source timeline stable so existing shots and the special epilogue remain reusable.
    cuts = [[round(a * FPS), round(b * FPS)] for a, b in [(25.5, 30), (51.5, 54), (57.5, 59.5), (129.2, 131.2)]]
    manifest = {"model": "speech-2.8-hd", "jobs": jobs, "fps": FPS, "removed_source_frames": cuts,
                "previous_cost_cny": 50.2302, "new_video_estimate_cny": 44, "budget_cny": 100}
    path = ROOT / "audio/opening/manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(jobs)} voice takes; {sum(len(j['text']) for j in jobs)} text characters; {sum(b-a for a,b in cuts)/FPS:.3f}s removed")


if __name__ == "__main__":
    main()
