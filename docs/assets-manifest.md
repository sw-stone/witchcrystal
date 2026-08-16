# 屿眠 Sleep Isle · 素材清单（assets-manifest）

> 生成时间：2026-08-16（Agent A 任务 1 / TODO-D7 关闭）
> 素材来源：飞书 wiki《【To Lin】内部协作文档For开发》（wiki token `OPbZwxsTliwGnykGIekclHCBncj` / docx `ELnFdlAIZotTzYxrtNIcztspnVc`）正文所列附件 + 本地已集成副本
> 落位根目录：`assets/sleep-isle/`

## 0. 下载说明（重要）

飞书 wiki 附件下载接口（`/open-apis/drive/v1/medias/<token>/download`）当前对 user/bot 双身份均返回 **HTTP 403**（应用侧媒体下载权限受限，且 252MB 大包超出 lark-cli 可下载范围，此前会话已验证）。本清单采用**本地已有副本归位**策略：wiki 所列附件中，凡本地（`backend/gateway/app/static/`、`PocketTarotCards-Rounded/` 等）已有等价物的，已复制入 `assets/sleep-isle/` 并在下表标注"本地归位"；仍缺失的标注"待补"。wiki 原始附件 token 一并记录，供后续手动导出（飞书网页端右键另存）使用。

## 1. 呼吸模块（breathing）

| 项 | 值 |
|---|---|
| 来源包 | `breathing-orbit-package.zip`（wiki token `EnOCbi3zBoTs33xCjnhc6BmXnKd`，163KB） |
| 本地落位 | `assets/sleep-isle/breathing/breathing-orbit.html`（8.7KB，已解包版）+ `breathin.mp3` / `breathout.mp3` 音效 |
| HTML 入口 | `breathing-orbit.html`（自包含，Canvas 轨道动画） |
| JS 接口 | `addEventListener('resize'/'pointerdown'/'click')`；无 fetch/postMessage 对外接口（纯本地动画） |
| 状态 | 本地归位 ✅（zip 原包受 403 限制未重新下载，功能等价） |

## 2. 白噪声模块（whitenoise）

| 项 | 值 |
|---|---|
| 来源包 | `witch-sleep-orb.zip`（wiki token `PKErbzOO9occoLxQMO3cFqYOn4f`，**252MB**） |
| 本地落位 | `assets/sleep-isle/whitenoise/whitenoise.html`（7.5KB，自建替代版） |
| HTML 入口 | `whitenoise.html` |
| JS 接口 | `SCENES` 五场景（rain雨/ocean海/forest林/fire火/space空）+ `load(sIdx,tIdx,silent)` + `ASSETS` 前缀变量；`<video id="vid">` 场景视频 + `new Audio()` 音轨循环 |
| 场景音轨清单 | rain: 窗上雨/远雷雨 · ocean: 深海 · forest: 林间溪/夜森林 · fire:（无音轨） · space: 深空/星际氛围 |
| 状态 | **替代版本地归位 ✅ / 原包未展开**（252MB zip 只登记清单：五场景视频 mp4 + 场景 mp3，文件名见 JS `pickVideo` map：rain-on-window / distant-thunder-rain / gentle-ocean-waves / deep-ocean / forest-stream / night-forest / campfire-night / deep-space / space-ambience）。`static/witch-sleep-orb/assets/` 目录为空壳 |
| 遗留缺口 | 原包视频/音频素材本体未入库（需飞书网页端手动下载或断网降级用 WebAudio 算法生成） |

## 3. 塔罗模块（tarot）

| 项 | 值 |
|---|---|
| 图片素材包 | `PocketTarotCards-Rounded.zip`（wiki token `DCwXbY5PooIqTIxqt5lcLHWQnlg`，82MB） |
| 本地落位 | `assets/sleep-isle/tarot/pocket-png/`（80 张 PNG：00-TheFool ~ 77-KingOfPentacles + card-back + _preview，来自本地已解包目录） |
| 线上 webp | `assets/sleep-isle/tarot/*.webp`（79 张：22 大阿卡纳带编号 `0-愚人`~`21-世界` + 56 小阿卡纳不带编号 `权杖1`~`星币国王` + `背面牌`） |
| 视觉模板 ×2 | `塔罗应用界面样机与组件规范_v4.html`（token `XkRWboQouojLFTxV5wcc4MQEnNc`，22KB）/ `塔罗应用设计令牌_v4_柔光舒缓版.html`（token `LUO1b3wXLoWQo5xziqqcCTN1nxc`，23KB）——**受 403 限制未下载，待补**（线上在用等价实现：`static/tarot.html` + `static/console.html`） |
| 状态 | PNG+webp 双套牌库本地归位 ✅；2 个 v4 规范 HTML 待补 |

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

1. **塔罗音效.mp4**：产品链路表 S6 塔罗路径引用「塔罗音效.mp4」，wiki 素材区未附此文件——需产品补素材或用 alarm-tone.mp3 类提示音替代
2. **witch-sleep-orb.zip（252MB）**：五场景视频+音频本体未入库，当前用自建 whitenoise.html（含场景定义+播放逻辑，素材路径已预留 `ASSETS+'video/'+key+'/'`）替代；断网兜底方案 = WebAudio 算法生成
3. **塔罗 v4 规范 HTML ×2**：受附件下载 403 限制未取得，线上 tarot.html 为等效实现
4. **附件下载通道**：lark-cli `docs +media-download` 对该 wiki 全部附件 403（user 已有 `docs:document.media:download` scope 仍被拒），建议人工在飞书网页端导出
