# 屿眠 Sleep Isle · 素材清单（assets-manifest）

> 生成时间：2026-08-16（Agent A 任务 1 / TODO-D7 关闭）；**同日 16:40 更新：附件下载通道已修复（应用侧开通媒体下载权限），全部原始附件已入库**
> 素材来源：飞书 wiki《【To Lin】内部协作文档For开发》（wiki token `OPbZwxsTliwGnykGIekclHCBncj` / docx `ELnFdlAIZotTzYxrtNIcztspnVc`）正文所列附件 + 本地已集成副本
> 落位根目录：`assets/sleep-isle/`

## 0. 下载说明（已解决）

初版清单曾因应用侧（cli_aaec51583021dd1c）未开通媒体下载权限全线 403。16:30 管理员开通后，`docs +media-download`（user）与 medias v1 直链全部恢复，**全部附件已按原始 token 下载入库**；此前"本地归位"副本保留不动。252MB 原包 `witch-sleep-orb-original.zip` 已存 `assets/sleep-isle/whitenoise/`（.gitignore 排除，超 GitHub 100MB 限制，需走 Releases/网盘分发）。

## 1. 呼吸模块（breathing）

| 项 | 值 |
|---|---|
| 来源包 | `breathing-orbit-package.zip`（wiki token `EnOCbi3zBoTs33xCjnhc6BmXnKd`，163KB） |
| 本地落位 | `assets/sleep-isle/breathing/breathing-orbit.html`（8.7KB）+ `breathin.mp3` / `breathout.mp3` + **原始包 breathing-orbit-package.zip（159KB，校验：3 文件同已解包版）** |
| HTML 入口 | `breathing-orbit.html`（自包含，Canvas 轨道动画） |
| JS 接口 | `addEventListener('resize'/'pointerdown'/'click')`；无 fetch/postMessage 对外接口（纯本地动画） |
| 状态 | **原包已下载 ✅**（与本地解包版一致） |

## 2. 白噪声模块（whitenoise）

| 项 | 值 |
|---|---|
| 来源包 | `witch-sleep-orb.zip`（wiki token `PKErbzOO9occoLxQMO3cFqYOn4f`，**252MB**） |
| 本地落位 | `assets/sleep-isle/whitenoise/whitenoise.html`（7.5KB，自建替代版） |
| HTML 入口 | `whitenoise.html` |
| JS 接口 | `SCENES` 五场景（rain雨/ocean海/forest林/fire火/space空）+ `load(sIdx,tIdx,silent)` + `ASSETS` 前缀变量；`<video id="vid">` 场景视频 + `new Audio()` 音轨循环 |
| 场景音轨清单 | rain: 窗上雨/远雷雨 · ocean: 深海 · forest: 林间溪/夜森林 · fire:（无音轨） · space: 深空/星际氛围 |
| 状态 | **原包已下载并解包 ✅**：`assets/sleep-isle/whitenoise/witch-sleep-orb/`（white noise.html + js/app.js + js/sounds.js + css/style.css + ASSET_MANIFEST.md + README.md）+ `assets/audio/*`（10 mp3）+ `assets/video/*`（10 mp4，168MB）；原 zip 保留为 witch-sleep-orb-original.zip（gitignore） |
| 音轨实测时长 | campfire 61s / cozy-fireplace 17s / forest-stream 210s / night-forest 200s / deep-ocean 425s / gentle-waves 61s / distant-thunder 384s / rain-on-window 760s / deep-space 185s / space-ambience 145s |
| 与自建 whitenoise.html 关系 | JS `pickVideo` map 文件名与原包完全对应；原包 fire 场景实际有 2 条音轨（自建版 fire 无音轨记录待同步） |

## 3. 塔罗模块（tarot）

| 项 | 值 |
|---|---|
| 图片素材包 | `PocketTarotCards-Rounded.zip`（wiki token `DCwXbY5PooIqTIxqt5lcLHWQnlg`，82MB） |
| 本地落位 | `assets/sleep-isle/tarot/pocket-png/`（80 张 PNG：00-TheFool ~ 77-KingOfPentacles + card-back + _preview，来自本地已解包目录） |
| 线上 webp | `assets/sleep-isle/tarot/*.webp`（79 张：22 大阿卡纳带编号 `0-愚人`~`21-世界` + 56 小阿卡纳不带编号 `权杖1`~`星币国王` + `背面牌`） |
| 视觉模板 ×2 | `assets/sleep-isle/tarot/塔罗应用界面样机与组件规范_v4.html`（22KB ✅ 已下载）/ `塔罗应用设计令牌_v4_柔光舒缓版.html`（23KB ✅ 已下载，网络重试 1 次成功） |
| 状态 | PNG+webp 双套牌库 ✅ + 2 个 v4 规范 HTML ✅ 全齐 |

## 4. 冥想模块（meditation）

| 课 | 文件 | 时长 |
|---|---|---|
| 1 Release the Day｜放下今天 · 仪式感反刍 | meditation1-release-the-day.mp3（wiki 原名 `1. Release the Day｜放下今天 · 仪式感反刍 (2).mp3`，token `SwpSbKZcloloiOxSGt1cUeEYntd`） | 110.4s |
| 2 Relax Your Body｜身体扫描 | meditation2-relax-your-body.mp3（token `WADKbYVumo21xOxiySPcSKO6nJg`） | 116.0s |
| 3 Breathe Into Sleep｜慢呼吸 | meditation3-breathe-into-sleep.mp3（token `AAaVbPlGao4q3CxQB0Rcf9gAnzg`） | 122.4s |
| 4 Soften the Tension｜渐进式肌肉放松 | meditation4-soften-the-tension.mp3（token `E5npbCojmoVzvCxoboTcrRjqngg`） | 126.0s |
| 5 You're Safe Here｜慈心与安全感 | meditation5-you-are-safe-here.mp3（token `IPNLbVWMPoKzPwxjjLpcz8e4nVe`） | 115.7s |

全部本地归位 ✅（合计 ~9.4MB）。文字版全文已备份至 `docs/feishu-backup/`。

## 5. 状态视频（videos）

| 视频用途 | 文件 | 大小 | wiki token |
|---|---|---|---|
| S1 首次引导 | 引入.mp4 | 22.5MB | QjJqbRJpCoWhsmxNG1ccCsm9njf |
| S3 手机锁定 | 锁定.mp4 | 15.6MB | T0nhb7VsIo6aWmxD03AcwbLInlc |
| S4 AI 待机循环 | AI待机.mp4 | 21.0MB | Wy7bbQ38No9b7mxUi8gcsL2cnce |
| S5 AI 说话 | AI说话.mp4 | 20.5MB | PSKmbRkqvopnkUxCPSDcCd7sn9d |
| S7 塔罗转场 | 塔罗转场.mp4 | 1.5MB | UQBHbKiihoDUfMxWwnIc9mMlnhh |
| S8 闹钟循环 | 闹钟.mp4 | 40.4MB | UphJbdBeComeW4xUIZjcnCJzn9g |
| S9 起床欢呼 | 欢呼.mp4 | 5.1MB | FSdjbdYFHon49cxgZ6echJ8zncd |

全部本地归位 ✅（含 alarm-tone.mp3）。

## 6. 遗留缺口汇总

1. ~~塔罗音效~~ **已替代生成**：wiki 确实未附。已用 ffmpeg 合成风铃双音（880→1320Hz，0.6s，aac）落位 `assets/sleep-isle/videos/塔罗音效.m4a`；产品后续可替换真人素材
2. ~~witch-sleep-orb 252MB~~ **已入库**（见第 2 节）；唯一跟进项：自建 whitenoise.html 的 fire 场景音轨表需补 campfire-night/cozy-fireplace 两条
3. ~~塔罗 v4 规范 HTML~~ **已下载入库**
4. ~~附件下载通道 403~~ **已修复**（管理员开通应用侧权限；期间发现网络对 23KB 文件偶发 connection reset，重试即过）
5. 新增小项：`assets/sleep-isle/` 总量 607MB/206 文件，其中 252MB 原包 zip 已 gitignore；若仓库要收全量素材，建议 GitHub Releases 挂 witch-sleep-orb-original.zip
