# MiniMax H3 video workflow

## Emotional Performance / v16 (2026-10-02)

The user authorized an additional CNY 50. Six new H3 2K clips total 43 generated seconds: Milton's slow clap and restrained contempt (6s), Lao Ya's listening reaction (8s), the HR meeting (8s), Dutch avoiding eye contact (8s), Adie's restrained grief (7s), and the father's response to his child (6s). Official reported output seconds match the requested lengths, estimated CNY 34.40. Prompt/task/checksum files are under `out/video-preview/h3-emotion-*`; the plan's conservative cap is previous estimated usage plus the additional 50, CNY 144.64425.

Lao Ya's close-up is reused during the challenge, AI result and bittersweet victory narration. “别像我。” becomes an ordinary subtitle over Adie's reaction instead of a full-screen card; its explicit 2.34-second duration preserves all subsequent source timings. Generated sound is discarded. The approved 7-second studio card, silent prologue and complete dub remain in place.

```bash
python3 scripts/gen-key-shots.py --manifest out/video-preview/h3-emotion-shots.json --wait 20
python3 scripts/prepare-video-frames.py
node scripts/build-timeline.js
python3 scripts/render-emotion.py
python3 scripts/h3-reel.py --emotion
```

The final movie is `out/red-error-final-v16-emotion.mp4` (520.625 seconds / 12495 frames / 24 fps). `out/video-preview/red-error-v16-emotion-reel.mp4` includes dialogue and surrounding picture to judge performances. The renderer recaptures affected windows plus outgoing dissolves, retains the v15 picture elsewhere, and rebuilds the verified full dub with the new Milton takes. `out/emotion-edit/verification.json` records successful full decode, and `audio-verification.json` records complete 61-line coverage, timing, peak and unchanged gain over the approved final greeting. New generation cost is estimated CNY 44.368, cumulative CNY 139.01225; these are list-price estimates, not an account invoice.

## Studio-card pacing / v15 (2026-10-02)

The studio credit now retains its original seven-second scene (source seconds 23–30). The v13/v14 export had removed seconds 25.5–30, which cut off its hold and fade-out. `scripts/restore-studio-card.py` restores those 4.5 seconds from the already captured opening and rebuilds the approved full dub with the matching edit. The music follows the original continuous lead-in to the silent prologue. Other export cuts remain as in v14; no video or voice generation is requested.

```bash
python3 scripts/restore-studio-card.py
```

Latest full film: `out/red-error-final-v15-studio-card.mp4` (520.625 seconds, 12495 frames, 24 fps). The three-minute preview is `out/video-preview/red-error-v15-first-three-minutes.mp4`; `red-error-v15-intro-transition.mp4` is a 43-second excerpt of final seconds 18–61. `out/studio-card-edit/verification.json` records full decode and exact downstream picture-packet/PCM preservation, excluding the previous audio cut's 12 ms microfade. The cumulative estimated generation cost stays CNY 94.64425.

## Opening revision / v13 (2026-10-02)

The first three minutes add six action takes from the existing first-frame images: emergency repairs (4s), exhausted team at dawn (7s), moving van interior (6s), hands warming at the server (8s), Dutch addressing the team (15s), and Adie's nighttime AI experiment (15s). The plan is `out/video-preview/h3-opening-shots.json`, totaling 55 seconds at the 2K tier, estimated CNY 44. Each scene explicitly references its own clip; returning van shots use offsets instead of replaying the action. Generated audio is discarded, with dialogue synthesized separately.

The budget guard accepts `--manifest` and adds the plan's non-video commitment/reserve to all recorded China video submissions. The full estimated project usage including previous video, voice design/activation and the new TTS is CNY 94.4696. Remaining budget is approximately CNY 5.53; invoice charges have not been queried.

```bash
python3 scripts/gen-key-shots.py --manifest out/video-preview/h3-opening-shots.json --submit-only
python3 scripts/gen-key-shots.py --manifest out/video-preview/h3-opening-shots.json --wait 20
python3 scripts/prepare-video-frames.py
node scripts/build-timeline.js
python3 scripts/render-opening.py
```

Frame preparation includes both the earlier shots and the opening manifest. `render-opening.py` captures source seconds 0–191, exports the shorter opening with identical audio/video cuts, and joins it to v12's remaining picture. Source seconds and subtitle timing stay stable. Output files are `out/red-error-final-v13-opening.mp4` and `out/video-preview/red-error-v13-first-three-minutes.mp4`. The export checks 1920x1080, 24 fps, exact frame counts and full audio/video decode; verification is recorded in `out/opening-edit/verification.json` only after those checks pass. The full cut is 516.125 seconds and the focused preview is exactly 180 seconds.

## Key shots (2026-10-01)

Six additional first-frame H3 takes were generated at the China `2K` tier. All returned 2944x1248 video at 24 fps and passed full decode. No retakes were submitted.

| Take | Requested/API output seconds | Estimated CNY |
| --- | ---: | ---: |
| Snow-road van | 5 | 4.00 |
| Programmer's hands | 4 | 3.20 |
| Rainy cigarette | 6 | 4.80 |
| Bridge scooter | 11 | 8.80 |
| Notebook handover | 9 | 7.20 |
| Father and child typing | 12 | 9.60 |
| New shots total | 47 | 37.60 |
| Including earlier rooftop trial | 52 | 40.10 |

The cap is CNY 100. These are official list-price estimates using the API's `usage.output_seconds`, not a verified billing receipt. Container lengths include small extra tails; they are not used to calculate this estimate. `out/video-preview/h3-key-shots.json` records the approved plan; each take has its own prompt, task metadata, checksums, original MP4 and contact sheet. `scripts/gen-key-shots.py` conservatively counts existing China submissions before submitting the remaining jobs and refuses to exceed the cap. Resuming does not incur another generation charge.

```bash
python3 scripts/gen-key-shots.py --submit-only
python3 scripts/gen-key-shots.py --wait 20
python3 scripts/prepare-video-frames.py
node scripts/build-timeline.js
python3 scripts/render-h3.py
python3 scripts/h3-reel.py
```

The assembled output is `out/red-error-final-v12-h3.mp4`. The edit keeps v11's frame count and copies its original AAC packets, including the separately inserted epilogue voice. `out/h3-edit/verification.json` records full decode and the identical audio packet hash. The original v11 remains available. The render script refuses to overwrite its finished output.

## Verified result (2026-10-01)

- Official China API: `https://api.minimax.cn/v2/video_generation`.
- Key file: `.minimax`, containing one raw API key. Never include it in a commit or share it with generated assets.
- Model: `MiniMax-H3`; first frame: `web/img_hd/rooftop_close.jpg`.
- Task: `447743203164445`; requested 5 seconds, `768P`.
- Output: `out/video-preview/h3-rooftop-close-v1-cn.mp4`.
- Actual video: H.264, 1568x672, 24 fps; container duration 5.167 seconds, AAC stereo 32 kHz audio included.
- `768P` is the service tier, not a guarantee of 768-pixel height for a widescreen input.
- Full FFmpeg decode passed. One-second samples show the lid closing and the hands withdrawing, with the laptop and rooftop remaining broadly consistent. This is a first take, not a frame-by-frame acceptance review.
- Usage: 5 output seconds, 1 input image. Official list-price estimate: CNY 2.50 (0.50/second); not a verified account invoice.
- The international API returned HTTP 401 for this key; the China API accepted it.
- Generation uses HTTP directly. No MCP server was installed. The rooftop trial is now included with the six new takes in v12.

## Generate or resume

Python 3 standard library, FFmpeg and ffprobe are required. Run from the project root:

```bash
python3 scripts/gen-video.py \
  --region china \
  --image web/img_hd/rooftop_close.jpg \
  --prompt-file out/video-preview/h3-rooftop-close-v1.prompt.txt \
  --out out/video-preview/h3-rooftop-close-v1-cn.mp4
```

The existing verified result is reused. To generate another take, use a new output filename. `--resolution 2K` is supported; the China list price is 0.80/second. `--duration` accepts 4 through 15 seconds. `--dry-run` checks inputs and prints the request summary without reading credentials, writing files, or calling the service.

`--submit-only` submits once and saves the task ID. The default polling window is 50 seconds; exit code 2 means pending. Rerun the same command to query the saved task without another paid POST. Failed or ambiguous submissions are not automatically retried; inspect the metadata and platform task history first, especially after a timeout. Successful results are downloaded without forwarding API credentials, fully decoded, and recorded with a SHA-256 checksum.

The JSON beside the MP4 records the source image checksum, prompt, requested settings, task response, usage, output checksum and ffprobe data. It excludes the API key but may contain a temporary media download URL; save the local MP4 rather than relying on that URL.

## Film integration

`scripts/prepare-video-frames.py` verifies each source checksum and extracts muted 1920x816 JPEG frames at 24 fps. `web/video/clips.js` maps take IDs to these sequences. Each scene or alternate shot opts in with `clip: { id, start?, offset?, rate? }`; static uses of the same image stay independent. `start` holds frame zero until the dialogue finishes, `offset` resumes a later frame on a returning shot, and `rate` adjusts action timing. Clips hold their last frame without looping. The browser's `renderFrame(t)` waits for visible images to decode before capture; generated shots use a stable crop and their own movement instead of another Ken Burns pan or particle layer.

The notebook's returning shot holds its completed handover. Father/child action starts at scene-local 10.68 seconds, after the spoken answer. The short programming take is trimmed to the existing 2.6-second cut. The rooftop trial plays at 1.4x through the existing dissolve. Only affected shot windows and outgoing transitions are recaptured; the other windows use v11's video, re-encoded for compatible concatenation. Generated audio is excluded throughout.

Contact sheets and rendered boundary screenshots were inspected for obvious anatomy, identity and transition problems. This is a sampled visual review, not a guarantee that every generated frame is artifact-free.

## Sources

- [Official H3 create API](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)
- [Official pricing](https://platform.minimax.cn/docs/pricing/overview)

```bash
python3 -m unittest discover -s tests -p 'test_gen_video.py' -v
node --test tests/test_clip_frames.js
```
