"""Prepare audio-only auditions; never modify the approved mix or any video.

Requires numpy/scipy and source files in audio/voice-preview.
Default A/B: Microsoft Edge neural MP3s. --soft: approved Qwen3-TTS VoiceDesign WAV.
Source text: 你好，世界。 All are synthesized voices, not human recordings.
For new dry-voice generation, see gen-voice.py; this script only mixes existing audio.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--soft", action="store_true", help="Mix the Qwen voice-design audition only")
args = parser.parse_args()
OUT = ROOT / "out/voice-preview"
OUT.mkdir(parents=True, exist_ok=True)
SR = 48000
source = ROOT / "out/mix-v10.wav"
rate, baseline = wavfile.read(source)
assert rate == SR and baseline.dtype == np.int16 and baseline.shape[1] == 2
tl = json.loads((ROOT / "web/timeline.js").read_text().split("=", 1)[1].rstrip(";"))
scene = next(s for s in tl["scenes"] if s["id"] == "ep_c")
enter = scene["t0"] + next(s["at"] for s in scene["sfx"] if s["name"] == "enter")
start = enter + 0.55
scene_end = scene["t0"] + scene["dur"]
variants = [
    ("A", "yunjian", "zh-CN-YunjianNeural", "-16%", "-3Hz"),
    ("B", "yunxi", "zh-CN-YunxiNeural", "-14%", "-4Hz"),
]
if args.soft:
    variants = [("C-soft", "qwen-soft", "Qwen3-TTS VoiceDesign", "natural", "natural")]
report = {
    "status": "audio audition only; video integration pending user approval",
    "text": "你好，世界。",
    "source_mix": str(source),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "voice_start_seconds": round(start, 3),
    "preview_start_seconds": 488,
    "preview_end_seconds": 502,
    "variants": [],
}

for label, name, voice_id, speed, pitch in variants:
    mp3 = ROOT / f"audio/voice-preview/hello-world-{name}.{'wav' if args.soft else 'mp3'}"
    data = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(mp3), "-ar", str(SR),
        "-ac", "1", "-f", "f32le", "-",
    ])
    raw = np.frombuffer(data, dtype=np.float32).copy()
    # Retain soft consonants and natural breath; only trim leading/trailing silence.
    active = np.flatnonzero(np.abs(raw) > max(0.0003, np.max(np.abs(raw)) * 0.004))
    assert active.size, "Empty speech"
    a = max(0, active[0] - int(0.025 * SR))
    b = min(len(raw), active[-1] + int(0.08 * SR))
    dry = raw[a:b]
    dry = sosfilt(butter(2, 65, "highpass", fs=SR, output="sos"), dry)
    frame = int(.02 * SR)
    blocks = len(dry) // frame
    rms = np.sqrt(np.mean(dry[:blocks * frame].reshape(blocks, frame) ** 2, axis=1))
    speaking = rms[rms > rms.max() * .12]
    active_rms = np.sqrt(np.mean(speaking ** 2))
    target_db = -25 if args.soft else -22
    peak_db = -10 if args.soft else -7
    gain = min(10 ** (target_db / 20) / active_rms, 10 ** (peak_db / 20) / np.max(np.abs(dry)))
    dry *= gain
    fade = int(.008 * SR)
    dry[:fade] *= np.linspace(0, 1, fade)
    dry[-fade:] *= np.linspace(1, 0, fade)
    # Quiet, damped early room reflections. No synthetic hiss or obvious echo.
    wet = np.zeros((len(dry) + int(.2 * SR), 2), dtype=np.float64)
    wet[:len(dry)] += dry[:, None]
    damped = sosfilt(butter(2, 3000, "lowpass", fs=SR, output="sos"), dry)
    # The quiet close voice stays almost dry to preserve intimacy.
    reflections = [] if args.soft else [(.027, .025, .018), (.043, .013, .022), (.071, .009, .006), (.11, .004, .005)]
    for seconds, left, right in reflections:
        shift = round(seconds * SR)
        wet[shift:shift + len(dry), 0] += damped * left
        wet[shift:shift + len(dry), 1] += damped * right
    i = round(start * SR)
    end = i + len(wet)
    assert end < round((scene_end - .5) * SR), "Voice leaves insufficient pause before title"
    mixed = baseline.copy()
    region = baseline[i:end].astype(np.float64) / 32768 + wet
    assert np.max(np.abs(region)) < .95, "Clipping risk"
    mixed[i:end] = np.round(np.clip(region, -1, 32767 / 32768) * 32768).astype(np.int16)
    stem = OUT / f"hello-world-{label}-voice.wav"
    full = OUT / f"mix-v11-audition-{label}.wav"
    excerpt = OUT / f"ending-audition-{label}.wav"
    wavfile.write(stem, SR, np.round(wet * 32768).astype(np.int16))
    wavfile.write(full, SR, mixed)
    wavfile.write(excerpt, SR, mixed[488 * SR:502 * SR])
    assert np.array_equal(mixed[:i], baseline[:i])
    assert np.array_equal(mixed[end:], baseline[end:])
    record = {
        "variant": label, "provider": "Qwen official Hugging Face demo" if args.soft else "Microsoft Edge neural TTS", "voice": voice_id,
        "rate": speed, "pitch": pitch, "raw_audio": str(mp3),
        "stem": str(stem), "full_mix": str(full), "excerpt": str(excerpt),
        "speech_duration_seconds": round(len(dry) / SR, 3),
        "voice_end_seconds": round(end / SR, 3),
        "pause_before_title_seconds": round(scene_end - end / SR, 3),
        "mixed_region_peak_dbfs": round(20 * np.log10(np.max(np.abs(region))), 2),
        "outside_insert_bit_identical": True,
    }
    report["variants"].append(record)
    print(json.dumps(record, ensure_ascii=False))

(OUT / ("manifest-soft.json" if args.soft else "manifest.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
