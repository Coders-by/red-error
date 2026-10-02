# 语音生成脚本：Qwen3-TTS VoiceDesign

## Dialogue Corrections / v17 (2026-10-02)

Lao Ya's `c1_d_3` now reads “它还能跑就行。” in both the subtitle and a new take using the approved D voice. The daughter's `ep_c_1` question uses MiniMax's system voice `lovely_girl` (萌萌女童), calm emotion, speed 1.0 and pitch 0. The adult father's approved Qwen “你好，世界。” remains at its original position.

```bash
python3 scripts/gen-minimax-tts.py --manifest audio/line-fixes/generate.json
python3 scripts/render-line-fixes.py
```

The two takes report 33 billing characters, an estimated CNY 0.01155. The cumulative estimate is CNY 139.0238, within the existing CNY 144.64425 ceiling. `out/line-fixes-edit/manifest.json` records the revised full cast and audio plan. The renderer checks unchanged scene/line timing, recaptures the corrected subtitle scene and its outgoing dissolve, rebuilds the full mix from the clean v12 bed, and decodes the exports completely. Outputs are `out/red-error-final-v17-line-fixes.mp4` and `out/video-preview/red-error-v17-line-fixes.mp4`; earlier versions are retained.

## Milton Recasting / v16 (2026-10-02)

Milton's `Sincere_Adult` voice was replaced after feedback that it sounded too soft. `audio/emotion-edit/milton-design.json` describes an original thick low baritone with supported chest resonance, clear diction, restrained contempt and quiet authority. It avoids shouting, exaggerated villain acting and imitation of any actor. The resulting ID is `ttv-voice-2026100203030526-wN1IJUbX`. All six Milton lines are generated independently at pitch -1, speed 0.90–0.94, calm emotion; the mixer checks each against its subtitle slot before accepting playback.

```bash
python3 scripts/design-minimax-elder.py --manifest audio/emotion-edit/milton-design.json --report out/voice-preview/milton-heavy-design-report.json
python3 scripts/gen-minimax-tts.py --manifest audio/emotion-edit/milton-tts.json
python3 scripts/render-emotion.py --mix-only
```

The design preview estimate is CNY 0.0246. First TTS use reports `usage_voice_count: 1`, budgeted at CNY 9.90; six takes report 124 billing characters, CNY 0.0434 synthesis. Including CNY 34.40 video, this revision estimates CNY 44.368, below the additional CNY 50 authorized by the user. Other cast selections and the approved Qwen final greeting are reused. Prior v15 and earlier audition files remain available.

## Complete dub / v14 (2026-10-02)

Following feedback on v13, Sadie now uses `Chinese (Mandarin)_Wise_Women` (阅历姐姐), calm emotion, speed 0.97, pitch 0. All four Sadie lines are regenerated. The dark prologue's five UI paragraphs remain visible with music but have no narration; spoken character dialogue on intertitle cards is retained.

`scripts/plan-full-dub.py` builds `audio/full-dub/manifest.json` with every one of the timeline's 61 character lines, the journal paragraph and the AI-experiment bridge. It reuses 33 approved/cached takes and requests 30 new takes. Lao Ya keeps D, Dutch/Mika/Adie keep their v13 system voices, Milton uses `Chinese (Mandarin)_Sincere_Adult`, HR `female-chengshu`, and the child `clever_boy`. The existing Qwen “你好，世界。” stays at its original source position in the v12 bed; the father's earlier “来，爸爸教你。” and the child's question receive separate MiniMax takes.

```bash
python3 scripts/plan-full-dub.py
python3 scripts/gen-minimax-tts.py --manifest audio/full-dub/generate.json
python3 scripts/render-opening.py --full-dub
```

The complete mix starts from v12's clean soundtrack, avoiding leftover v13 prologue narration or doubled voices. It applies the same 11-second export edit, voice normalization and smooth ducking. It checks source text, cast, audio checksums, complete dialogue coverage, non-overlapping speech and unity gain over the approved final greeting. The v13 picture is copied without re-encoding; its compressed video hash must remain identical. Output is `out/red-error-final-v14-full-dub.mp4`, with the refreshed three-minute preview at `out/video-preview/red-error-v14-first-three-minutes.mp4`. Reports live in `out/full-dub-edit/` and are written only after the relevant checks pass. The new synthesis was budgeted at less than CNY 0.20; actual reported character usage and cumulative list-price estimate are recorded in `audio-verification.json`.

## Narrated opening / v13 (2026-10-02)

The revised first three minutes use 31 MiniMax takes: incident dialogue, Lao Ya's prologue, all existing first/second-chapter dialogue, the journal paragraph, and a short bridge explaining Adie's AI experiment. Lao Ya keeps the approved D voice, pitch 0, calm emotion, with synthesis speed 1.05. Sadie uses `female-yujie`, Mika `Chinese (Mandarin)_Unrestrained_Young_Man`, Dutch `Chinese (Mandarin)_Reliable_Executive`, and Adie `male-qn-jingying`. These supporting voices are first production takes, not separately approved casting choices.

`audio/opening/manifest.json` records each take's source timing and fixed voice ID. The API returned 684 billing characters, estimated CNY 0.2394. There was one explicit RPM rejection before generation; it produced no audio and was resumed after waiting. The TTS script now saves request intent, refuses ambiguous resubmissions, recovers accepted downloads, and only retries explicit rate-limit rejections. Cached takes are verified without another synthesis request.

```bash
node scripts/build-timeline.js
python3 scripts/plan-opening.py
python3 scripts/gen-minimax-tts.py --manifest audio/opening/manifest.json
python3 scripts/render-opening.py --mix-only
```

The v13 mixer verifies voice checksums, checks every voice against its available slot and export cuts, normalizes voices to -19 LUFS, and ducks the existing soundtrack by up to 58% with smooth attack/release. It preserves the original timeline for alignment and removes exactly 11 seconds only at export: studio hold, final prologue hold, and the first two chapter-card holds. The approved nine D lines in later chapters are also placed into the full film. The original epilogue soundtrack, including the Qwen “你好，世界。” performance, comes from v12 with unity gain. This is a fully spoken opening and selected later narration, not a complete dub of all later chapters or a lip-sync pass.

Mix timing, peak, source hashes and costs are recorded in `out/opening-edit/audio-verification.json`; the completed movie validation is written separately to `verification.json`. Estimated cumulative video/TTS/design usage is CNY 94.4696 against the CNY 100 cap, based on list prices rather than the account invoice.

## MiniMax TTS audition (2026-10-02)

### Elder recasting

The user selected **D** on 2026-10-02. The stable Lao Ya voice ID is `ttv-voice-2026100201312826-qQW2tFvf`; selection and settings are stored in `audio/dub-preview/minimax-elder-selected.json`. Use this selected voice for Lao Ya's subsequent dubbing. The original design has the intended timbre, so synthesis uses pitch 0 and speed 1.0 instead of additional pitch lowering.

Nine lines from the ride-home and notebook-handover scenes were synthesized individually with `speech-2.8-hd` and calm emotion. These report 117 billing characters and one voice activation (`usage_voice_count: 1` in the first response). Estimated cost is CNY 9.90 for first activation plus CNY 0.04095 for synthesis. Including the prior H3 shots, initial TTS, A/B takes and C/D design previews, the estimated project usage is CNY 50.23020, within the CNY 100 cap; the account invoice has not been queried.

```bash
python3 scripts/gen-minimax-tts.py --manifest audio/dub-preview/minimax-elder-selected.json
python3 scripts/mix-minimax-dub-audition.py --elder D
```

The revised audition is `out/video-preview/red-error-v12-minimax-dub-audition-D.mp4`, with companion audio `minimax-dub-audition-D.wav`. It uses the selected D voice at each line's existing subtitle start rather than speaking all narration at the start of a scene. HR and Adie's previous takes are retained. Voices are normalized to -19 LUFS and converted to stereo for mixing; the original v12 soundtrack and earlier auditions remain available. This is the selected-voice audition, not yet a full-film dub.

The subsequent feedback rejected A's nasal resonance and B's excessive age. A second casting step uses MiniMax's `/v1/voice_design` to create original Mandarin voices from descriptive prompts. The reference direction is a grounded, weathered, low-baritone dramatic performance with supported breath and clear oral resonance. No actor recording or game audio is submitted; this is descriptive voice design, not an actor clone.

`audio/dub-preview/minimax-elder-design.json` holds two designs using identical preview text:

- C: stronger chest resonance and a restrained gravelly texture, middle-aged and physically solid.
- D: full low-baritone resonance with lighter rasp, fatigue and warmth, avoiding nasal or elderly delivery.

`python3 scripts/design-minimax-elder.py` records intent before submitting, saves the returned voice ID and raw preview checksum, normalizes both previews to the same -19 LUFS target, and fully decodes the 48 kHz mono WAVs. Existing verified outputs are reused; an unresolved prior submission requires investigation before any new paid request. Preview-only use is priced at CNY 2.00 per 10,000 characters. The separate CNY 9.90 design fee is deferred until the first TTS synthesis using the new voice ID; this script does not activate either voice. Voice IDs are retained in the matching JSON sidecars for later selection.

The initial elder voice used `male-qn-qingse` (the official "young" system voice). Following feedback that Lao Ya sounded too young, two separate audition variants were generated in `audio/dub-preview/minimax-elder-ab.json`:

- A: `Chinese (Mandarin)_Gentleman` (official name: 温润男声), speed 0.90, pitch -2, calm emotion.
- B: `Chinese (Mandarin)_Humorous_Elder` (official name: 搞笑大爷), speed 0.92, pitch -1, calm emotion. Its age character is a candidate; the name does not guarantee suitability for serious drama.

Each variant uses the same narration and notebook-handover text. `scripts/preview-minimax-elder.py` joins narration then dialogue with a 0.8-second gap, applies the same -19 LUFS loudness target, and exports mono PCM auditions to `out/voice-preview/minimax-elder-A-casting.wav` and `minimax-elder-B-casting.wav`. No added reverb or artificial breath is used. These are casting candidates, not a newly approved full-film voice. The earlier voices and mixed audition are retained for comparison.

```bash
python3 scripts/gen-minimax-tts.py --manifest audio/dub-preview/minimax-elder-ab.json
python3 scripts/preview-minimax-elder.py
```

Four new takes report 234 billing characters, estimated at CNY 0.08190 for `speech-2.8-hd`; the account charge has not been queried. The casting report records settings, input/output checksums, durations and decode verification.

The repository now includes a separate MiniMax T2A audition path. It uses the official China endpoint `https://api.minimax.cn/v1/t2a_v2`, reads the existing raw key from `.minimax`, and never stores that key in metadata.

Four short takes were generated with `speech-2.8-hd`:

- `male-qn-qingse`: elder narration and elder dialogue
- `male-qn-jingying`: Adie's brief reply
- `female-chengshu`: HR's notification

The verified assets are in `audio/dub-preview/generated/`. `scripts/gen-minimax-tts.py` decodes the returned hexadecimal MP3, converts it to 48 kHz mono PCM WAV, records the provider usage and SHA-256, and refuses to overwrite a changed take. Re-running the command verifies the cached files without submitting another request:

```bash
python3 scripts/gen-minimax-tts.py
```

`out/video-preview/red-error-v12-minimax-dub-audition.mp4` is a 55.3-second proof-of-concept over three existing scene windows. It keeps the film bed at reduced level and places the four voices at the corresponding scene positions. The companion `minimax-dub-audition.wav` is the uncompressed audition mix. This is a voice/clarity test, not the full film dub: the narrator take intentionally joins the ride-home lines into one short passage, while the final version should generate each line or scene paragraph separately to preserve exact subtitle timing.

The four responses report 173 usage characters in total. MiniMax's current China pricing page lists `speech-2.8-hd` at CNY 3.50 per 10,000 input characters, so the list-price estimate is about CNY 0.061 (the account invoice is not queried here). The official API response is the billing source of record.

The official request shape is documented at [MiniMax synchronous T2A](https://platform.minimax.cn/docs/api-reference/speech-t2a-http). This audition uses `voice_setting` for voice, speed, pitch and calm/sad emotion, `audio_setting.format=mp3`, `language_boost=Chinese`, and `subtitle_enable=false`. Generated audio is mixed separately from the existing v12 film; it does not replace the current soundtrack.

> 跨项目复用版本已整理到 `/Users/ilike/Coding/codes/mvs/agent-city/audio-kit/`，先读其中的 `README.md`。新版本自带参考音频、制作流程和已核查的额度/费用说明，默认匿名、显式授权才使用账户 token。本目录保留原项目脚本与历史素材，避免破坏 red-error 的复现流程。

## red-error 尾声的实际来源

v11 的“你好，世界。”是 Qwen3-TTS VoiceDesign 合成的 C-soft 版本，不是真人录音或影视片段，也不是最初试听的 Edge Yunjian/Yunxi 版本。

- 原始请求：`audio/voice-preview/hello-world-soft-request.json`，保留当时的台词、Chinese 语言参数和完整表演描述。
- 原始干声：`audio/voice-preview/hello-world-qwen-soft.wav`（24 kHz、单声道、16-bit PCM，约 2.297 秒）。
- 来源记录：`out/voice-preview/manifest-soft.json`，provider 为 Qwen official Hugging Face demo。该记录的“待确认”状态是试听阶段的历史记录；之后已合入 v11。
- 混音脚本：`scripts/preview-hello-world.py --soft`。它不是语音生成器，而是读取已生成干声，修整首尾、调电平并插入 v10 混音。
- 使用原始生成声音，不额外添加假气声；成片轻声的感觉来自表演描述及后续电平处理，不只是降低音量。

当前默认使用官方综合演示中的 Voice Design：`https://huggingface.co/spaces/Qwen/Qwen3-TTS`。

另一个官方独立演示为 `https://huggingface.co/spaces/Qwen/Qwen3-TTS-Voice-Design`。本次独立演示接口可查询，但实际生成返回空错误，因此不将其作为默认服务。历史本地记录能确认模型与官方 Hugging Face 来源，没有保存当时的精确生成端点，不把浏览器曾打开的 ModelScope 页面当作下载来源证据。

本封装默认调用公开演示的 Gradio HTTP 接口，不依赖浏览器点击，也没有假设 Gemini 生图代理同时支持语音。

## 安装与最常用命令

需要 Python 3.9+ 和 `ffmpeg`；无第三方 Python 包。以下命令从项目根目录执行。

### 使用尾声的表演提示词生成新语音

```bash
python3 scripts/gen-voice.py \
  --text '你好，世界。' \
  --preset red-error-soft \
  --out audio/generated/hello-world.wav
```

输出同名 `.wav` 和 `.json`。默认 WAV 为 48 kHz、单声道、16-bit PCM；JSON 记录请求、接口版本、任务 ID、文件校验值、时长和采样率。不自动混音、加混响、强制响度归一化或替换视频。

### 自定义角色和表演

```bash
python3 scripts/gen-voice.py \
  --text '到了发消息。' \
  --instruct '成年女性，标准普通话，日常近距离交谈。对即将离家的弟弟说话，有不舍但不煽情，句尾收住，不要播音腔。只读台词。' \
  --out audio/generated/sister-01.wav
```

`--instruct` 完整替换预设描述，不是追加。可将角色描述加入 `voices.json`，再通过 `--preset` 选取。长文本可改用 `--text-file lines.txt`。对白制作优先逐句/短段生成、试听、记录 take，不推荐一次生成整部电影。

### 原封不动复用最终确认的声音

```bash
python3 scripts/gen-voice.py \
  --preset red-error-soft --reuse-approved \
  --out audio/generated/hello-world-approved.wav
```

完全不联网；复制原始 WAV，字节与采样率均保持不变。仅适用于已经确认的“你好，世界。”，不是换文本的声音克隆。不会复制含音乐的最终混音。

### 按台词表批量生成

`voices.example.tsv` 使用制表符分隔：`id / text / preset / instruct`；也可加 `language` 列。空 preset 继承命令行预设，非空 instruct 覆盖音色描述。示例中的姐弟声音只是表演起点，并非已确认角色选角。

```bash
# 整表生成
python3 scripts/gen-voice.py --batch voices.example.tsv

# 只生成指定镜头/台词 ID，类似 gen-shots.py
python3 scripts/gen-voice.py --batch voices.example.tsv sister_01 brother_01

# 先检查输入，不联网、不写文件
python3 scripts/gen-voice.py --batch voices.example.tsv --dry-run
```

默认批量目录为 `audio/generated/`，可用 `--out-dir` 修改。请求和 WAV 校验值都匹配时跳过已有结果；已有文件无元数据、输入改变或文件损坏时明确报错，不擅自覆盖。主动更换路径保存新 take，或使用 `--force` 明确替换。

## 接口方式与配置

`TTS_BASE` / `--base-url` 可指向兼容的自部署 Gradio 服务，默认：

```text
https://qwen-qwen3-tts.hf.space
```

两套官方演示的参数不同。综合演示是 `/generate_voice_design(text, language, voice_description)`，独立演示是 `/tts_interface(text, instruct)`。脚本读取 `/config` 和相应的 `/info`，识别带 Audio 输出的这两种形式，也兼容 `text, language, instruct`，按实际参数顺序提交。不会误选综合演示的 Voice Clone 或 CustomVoice 接口。

```bash
# 只检查当前接口，不发起语音生成
python3 scripts/gen-voice.py --inspect-api
```

发现多个兼容接口时，使用 `--api-name` 或 `TTS_API_NAME` 指定。服务没有 language 参数时，语言由输入文本决定，元数据记录为 `inferred from text`，不会声称显式控制了语言。生成调用为 `POST <api_prefix>/call/<api_name>`，随后读取任务 SSE 结果并下载音频。

其他选项：`--timeout 300`、`--sample-rate 24000|44100|48000`、`--presets /absolute/path/voices.json`。已有服务若需要 Hugging Face token，可通过 `HF_TOKEN` 提供；不要写进代码、台词表或命令参数。只把 token 用在你信任的服务器上。脚本拒绝跨域音频下载及跨域重定向，避免转发鉴权信息。

网络权限受限时需要允许脚本访问该服务。公共演示可能排队、限流、维护或改变接口，不能当作有可用性承诺的生产 API。超时/服务失败返回非零退出码，不会自动重发生成 POST，避免重复生成。批量任务逐条处理，失败即停，已经完成的文件保留；修复后重跑会跳过经验证的结果。

## 多角色电影的使用边界

VoiceDesign 的文字描述适合选角和表演探索，但同一描述重复生成不保证同一“演员”，也不能保证与 v11 完全一致。`red-error-soft` 保存的是表演预设，不是永久 speaker ID，包含专门针对“你好，世界”的停顿要求；改台词时应相应改写描述。

本脚本不实现声音克隆，也不冒充稳定的商业 TTS 接口。若《未完成》进入大量对白制作，应先确定角色参考音频，再选用经过验证的固定音色/参考音频方案或自部署推理服务，把角色一致性与情绪表现分别测试。不要逐句重新设计音色后直接拼成一部电影。

## 验证

```bash
python3 -m unittest discover -s tests -v
ffprobe -v error -show_entries format=duration:stream=codec_name,sample_rate,channels \
  -of json audio/generated/hello-world.wav
ffmpeg -v error -i audio/generated/hello-world.wav -f null -
```

离线测试覆盖历史/当前参数顺序、SSE 完成/错误、缺失输出、原音复用、缓存校验、防覆盖、批量输入和 dry-run。实际联网生成是否成功以脚本退出码、WAV 及元数据为准；离线测试通过不代表公共服务当时可用。

2026-10-01 实测：12 项离线测试通过；默认综合演示的 `/generate_voice_design` 实际生成成功，结果保存在 `out/voice-api-smoke/hello-world-new.wav`（约 3.097 秒、48 kHz、单声道 PCM），完整解码无报错。它只是接口验证样本，不是重新确认的表演版本，也没有合入视频。复用结果 `hello-world-approved.wav` 已与原始 C-soft 干声逐字节比对一致。
