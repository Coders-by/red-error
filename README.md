# 红色报错：救赎

把《荒野大镖客：救赎 2》的人物关系与时代落幕主题，迁移到 AI/Agent 改变软件行业的世界。制作采用参考图、选择性的图生视频、角色配音，以及代码控制的时间轴、画面合成与混音。

当前交付版本为 [v17 完整成片](out/red-error-final-v17-line-fixes.mp4)：1920×1080、24 fps、520.625 秒。工程源时间轴与导出时间轴不同，见学习笔记。

## 学习与分享

- [可复用制作笔记与架构](docs/AI_FILMMAKING_NOTES.md)：实际文件、数据流、设计取舍、预算、验证、复用步骤与下一部项目模板。
- [经验分享提纲](docs/MAKING_OF_OUTLINE.md)：围绕“用 Agent 制作一部讲 Agent 的电影”组织讲述，附可展示的证据与画面。
- [学习卡图片与新封面](docs/PUBLISHING_ARTIFACTS.md)：四张卷轴学习卡、正午对决封面、标题建议和可编辑排版源。
- [视频生成记录](VIDEO_GENERATION.md)：MiniMax H3 请求、镜头批次、价格估算与整合方式。
- [语音生成记录](VOICE_GENERATION.md)：选角、稳定 voice ID、MiniMax/Qwen 流程与配音修订。
- [图像一致性复盘](IMAGE_CONSISTENCY_REVIEW.md)：历史审查与修复规格；其中的默片要求属于当时版本，不是当前配音版规格。

## 工程入口

`web/scenes.js` 是分镜源文件；`scripts/build-timeline.js` 生成 `web/timeline.js` 与 `audio/timeline.json`。`web/render.html`、`web/engine.js` 和 `web/ui.js` 负责画面，`scripts/capture.js` 按时间采帧，FFmpeg 编码、混音并导出。

最新配音计划在 `out/line-fixes-edit/manifest.json`，验证报告在同目录。历史版本脚本有固定的素材、预算与输出路径，不能把 `scripts/render.sh` 当成 v17 的一键重建入口。复用前先阅读笔记中的运行边界。

`.minimax` 是本地凭据，不属于可分享资产。项目中的预算为记录范围内的 API 标价估算，不是整部影片包含人工、图片生成和设备的总成本。
