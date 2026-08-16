# T5AI-Core 产品功能模块工程化提示词

> 用途：将飞书文档《【To Lin】内部协作文档For开发》第六板块 User Journey 的「产品功能模块」（呼吸、白噪声、塔罗、冥想+唤醒）转化为可直接投喂给涂鸦 TuyaOpen AI 开发流程的结构化提示词。
> 边界：视觉渲染与素材播放主体在**手机端 H5/WebView**；T5AI-Core 固件负责**状态调度、语音意图识别、音频输出、LED 反馈、H5 状态同步**。

---

<role>
你是涂鸦智能 TuyaOpen 平台的资深嵌入式固件工程师，同时熟悉手机端 H5 多媒体交互。你负责把「AI 睡眠魔法球底座」的四个产品功能模块（呼吸、白噪声、塔罗、冥想+唤醒）拆分为可在 T5AI-Core 开发板上稳定运行的固件+H5 协同方案。你清楚 H5 负责视觉与本地素材播放，固件负责控制流、语音对话、功放音频与 LED，并复用 TUYA_T5AI_CORE.config。
</role>

<task>
基于下述模块规格，输出可落地的工程实现方案：
1. 定义每个模块的固件-H5 接口契约（JSON 状态包 + 事件回调）。
2. 实现模块调度器，支持与状态机 S4/S5/S6/S7/S8/S9 联动。
3. 实现音频管理层：支持本地引导音频播放、白噪声循环、冥想语音、TTS 叠加、音量包络与淡入淡出。
4. 实现 LED 效果层：呼吸、随冥想阶段变化、塔罗揭示、闹钟闪烁。
5. 明确素材列表、命名约定、加载策略与缓存/降级规则。
6. 给出可单元测试的模块骨架（C / TuyaOS 层）和 H5 侧的调用约定。
</task>

<hardware_constraints>
目标硬件：T5AI-Core 开发板（Tuya T5-E1 模组）
- MCU：ARMv8-M Star（M33F），主频最高 480 MHz
- 存储：片内 8 MB Flash + 16 MB RAM
- 无线：2.4 GHz Wi-Fi + 蓝牙 LE 5.4（板载天线）
- 音频输入：1 路板载模拟麦克风（CH1）+ 1 路扬声器回采（CH2，支持 AEC 回声消除/打断）
- 音频规格：16 kHz 采样率 / 16 bit 位深
- 音频输出：1 W 功放（5 V 电源域）→ 外接 4Ω 3W 扬声器（JST PH 1.25 mm）
- 板载交互资源：用户 LED（GPIO P9）、用户按钮（GPIO P29）
- 扩展：44 Pin 排针（GPIO/UART/SPI/I2C、5V/3.3V）
- 固件烧录/调试：Type-C USB 双路串口
- 电源：USB 5 V / 3.7 V 锂电池双输入
- 板级配置：TUYA_T5AI_CORE.config（含板载 Mic/Speaker BSP）

**关键边界**：
- 固件不渲染复杂动画；动画/视频/H5 由手机端负责。
- 固件需保留本地音频通道，用于 TTS、引导语音、白噪声、闹钟、音效。
- 8 MB Flash 无法存放大量 MP3，必须依赖云端/H5 缓存或 OTA 分区策略；ROM 中只保留最小核心音频（如按键音、系统提示音）。
</hardware_constraints>

<module_architecture>
每个功能模块统一抽象为以下结构：

```c
typedef struct {
    const char *module_id;          // 模块唯一标识，如 "breathing"
    const char *display_name;       // 用户可见名
    module_state_t state;           // IDLE / PREPARING / PLAYING / PAUSED / COMPLETED / ERROR
    
    // 生命周期钩子
    int (*init)(void *cfg);         // 初始化，解析配置
    int (*start)(const cJSON *args);// 启动，传入 H5 侧需要的参数
    int (*pause)(void);             // 暂停（保留上下文）
    int (*resume)(void);            // 恢复
    int (*stop)(void);              // 停止并释放资源
    int (*tick)(uint32_t ms);       // 每 10~100 ms 调用，驱动动画/淡变/超时
    
    // 事件回调（由 H5 或语音层触发）
    int (*on_voice_intent)(const char *intent, const char *slots);
    int (*on_h5_event)(const char *event, const cJSON *payload);
} module_iface_t;
```

调度器职责：
- 同一时间只允许一个「主模块」处于 PLAYING 态；高优先级事件（闹钟、按钮-后）可抢占。
- 语音对话（S5）与功能模块（S6/S7）可叠加：模块播放中允许用户语音打断或切换子模块。
- 每个模块产生的功放音频统一送入 Mixer，Mixer 输出到 BSP 扬声器；H5 音频（如手机端冥想音乐）不在固件通道内，但固件可发指令让 H5 调音量。
</module_architecture>

<module_1_breathing>
### 模块标识
`module_id = "breathing"`

### 用户场景
用户说「我要呼吸 / 带我呼吸 / 打开呼吸」后进入。手机屏幕显示呼吸球/轨道动画（来自 breathing-orbit- package.zip），扬声器播放「吸气—屏息—呼气」的引导语音或纯提示音，LED 随呼吸节奏渐变。

### 配置参数（H5 + 固件共享）
```json
{
  "pattern": "4-7-8" | "box" | "coherence",
  "inhale_ms": 4000,
  "hold_ms": 7000,
  "exhale_ms": 8000,
  "cycles": 8,
  "voice_guidance": true,
  "led_sync": true,
  "bgm_track": "none" | "soft_drone"
}
```

### 固件职责
1. **语音意图**：识别启动/暂停/停止/切换节奏。
2. **引导音频播放**：按节奏播放轻提示音（如吸气提示音、呼气提示音），避免长时间 TTS 打断体验；若 `voice_guidance=true`，则合成简短引导语。
3. **LED 驱动**：以 `inhale_ms` 从暗到亮（吸气），`hold_ms` 保持亮度（屏息），`exhale_ms` 从亮到暗（呼气）。
4. **状态同步**：每 100 ms 向 H5 发送 `{ "phase": "inhale|hold|exhale", "progress": 0.0~1.0, "cycle": 3, "cycles": 8 }`。
5. **结束处理**：cycles 耗尽或用户语音「结束」→ 模块 state=COMPLETED，回调调度器切回 S4 AI待机。

### H5 职责
- 解压并加载 breathing-orbit-package.zip 中的动画资源。
- 接收固件同步的 phase/progress，驱动动画与文字提示同步。
- 用户可在手机屏切换节奏，回传事件给固件。

### 边界与异常
- 网络断开时：改用本地默认 4-7-8 节奏 + 本地提示音。
- 用户离座（按钮-下弹起）：立即 pause，回待机；再次入座可 resume（记忆剩余 cycles）。
</module_1_breathing>

<module_2_whitenoise>
### 模块标识
`module_id = "whitenoise"`

### 用户场景
用户说「白噪音 / 助眠噪音 / 雨声」后进入。H5 展示 witch-sleep-orb 视觉（魔法球/女巫睡眠球），固件播放循环白噪声。

### 配置参数
```json
{
  "sound_type": "rain" | "brown" | "pink" | "fan" | "waves" | "forest",
  "volume": 0.0~1.0,
  "fade_in_ms": 3000,
  "fade_out_ms": 3000,
  "timer_minutes": 30 | 60 | 90 | 0,   // 0 表示无限循环
  "auto_stop_on_sleep": false          // 未来接入睡眠检测后启用
}
```

### 固件职责
1. **声源选择**：优先播放本地预置循环样本；若未缓存则请求 H5 或云端下载后写入 SPI Flash/SD（需评估容量）。
2. **无缝循环**：使用环形缓冲区 + Mixer 通道，避免播放间隙；文件结束平滑跳回起点。
3. **音量包络**：启动 fade_in，停止 fade_out，切换音源交叉淡变 500 ms。
4. **倒计时停止**：timer 到达后自动 stop 并回调调度器；用户语音「关闭」立即停止。
5. **状态同步**：向 H5 发送 `{ "sound_type", "remaining_sec", "volume" }`。

### H5 职责
- 加载 witch-sleep-orb.zip 视觉资源，显示对应氛围球体。
- 提供声源选择 UI，选择后下发给固件；显示倒计时。

### 边界与异常
- 内存不足无法缓存时：降级为 Pink/Brown 噪声实时算法生成（轻量合成，无需素材）。
- 闹钟事件（S8）抢占白噪声，自动 fade_out 并切换至闹钟音频。
</module_2_whitenoise>

<module_3_tarot>
### 模块标识
`module_id = "tarot"`

### 用户场景
用户在 S4/S6 状态下说「抽一张塔罗 / 帮我占卜」后进入 S7。H5 播放 塔罗转场.mp4 → 卡牌从底部升起动画 → AI 语音解读。

### 配置参数
```json
{
  "deck": "pocket_tarot_rounded",
  "spread": "single",           // 扩展：three_card, celtic_cross
  "voice_interpretation": true,
  "animation_speed": 1.0,
  "show_keyword": true,
  "show_upright_meaning": true
}
```

### 固件职责
1. **随机抽卡**：使用硬件 RNG 或系统时间种子生成随机索引，确保不可预测；大阿尔卡那 22 张 + 小阿尔卡那 56 张（若素材包含）。
2. **意图路由**：抽卡后向 LLM Agent 发送 `{card_name, upright/reversed, spread}`，请求生成中文解读；LLM 返回文本后走 TTS 播报。
3. **H5 同步**：按时间轴发送事件：
   - `{"event":"tarot_shuffle"}` — 洗牌/转场
   - `{"event":"tarot_reveal", "card_id":"The_Fool", "orientation":"upright"}` — 卡牌升起
   - `{"event":"tarot_interpret_start", "text":"..."}` — 开始解读
   - `{"event":"tarot_interpret_end"}` — 解读结束
4. **LED 效果**：揭示阶段亮紫色/金色呼吸灯，解读阶段柔和常亮。
5. **打断支持**：解读播报中用户语音可打断，进入新对话或重新抽卡。

### H5 职责
- 加载 PocketTarotCards-Rounded.zip 卡牌素材。
- 接收 tarot_reveal 事件，播放「卡牌自下而上出现」动画；显示牌面名称、正逆位、关键词。
- 显示塔罗应用界面样机与组件规范（HTML 模板）。

### 数据表
卡牌信息至少包含：id、name（中英）、roman_numeral、keywords、upright_meaning、reversed_meaning、element、image_asset。建议以 JSON 索引表形式存储于 H5 包，固件只保存 id 与 orientation。

### 边界与异常
- LLM/TTS 失败：播放预置简短解读（本地 fallback），并提示「网络不太稳定，先给你这张牌的核心含义」。
- 连续抽卡：重新进入 shuffle 态，历史牌面缓存最近 3 次，避免连续重复。
</module_3_tarot>

<module_4_meditation_wake>
### 模块标识
- 冥想：`module_id = "meditation"`
- 唤醒/闹钟庆祝：`module_id = "wakeup"`

### 冥想用户场景
用户在 S5/S6 下选择「冥想」或说出对应课程名，进入 5 套睡前冥想课程之一。手机屏幕显示课程标题与进度；固件播放对应 MP3 引导语音，LED 随课程阶段变化。

### 冥想课程清单
| 课程 ID | 英文标题 | 中文主题 | 适用场景 | 音频素材 |
|---|---|---|---|---|
| med_01 | Release the Day | 放下今天 · 仪式感反刍 | 反刍思维、未竟事项 | 1. Release the Day...mp3 |
| med_02 | Relax Your Body | 身体扫描 · 最通用的睡前冥想 | 身体紧绷 | 2. Relax Your Body...mp3 |
| med_03 | Breathe Into Sleep | 慢呼吸 · 快速安静下来 | 入睡困难 | 3. Breathe Into Sleep...mp3 |
| med_04 | Soften the Tension | 渐进式肌肉放松 · 释放身体压力 | 肌肉紧张 | 4. Soften the Tension...mp3 |
| med_05 | You're Safe Here | 慈心与安全感 · 孤独、焦虑、情绪低落 | 情绪安抚 | 5. You're Safe Here...mp3 |

### 配置参数
```json
{
  "course_id": "med_01"~"med_05",
  "volume": 0.0~1.0,
  "playback_speed": 1.0,
  "led_theme": "warm_breath" | "moonlight" | "candle",
  "resume_at_sec": 0.0   // 断点续播
}
```

### 固件职责
1. **音频流播放**：从云端/H5 加载对应 MP3，解码后通过 Mixer 输出；支持暂停、恢复、拖动进度（未来扩展）。
2. **阶段同步**：根据音频时间轴或文本脚本标记，向 H5 发送：
   - `{"event":"med_phase", "phase":"intro/body/breath/relax/safety/ending", "progress":0.42}`
3. **LED 主题**：intro 阶段慢呼吸暖光；body scan 阶段逐段点亮（隐喻扫描）；ending 阶段渐暗至熄灭。
4. **结束处理**：音频自然结束 → state=COMPLETED → 调度器切回 S4 AI待机；用户说「结束」提前退出。
5. **断点续播**：记录 `resume_at_sec`，用户离座/暂停后可恢复。

### H5 职责
- 显示课程标题、当前阶段提示文字、进度圆环。
- 可选显示课程脚本文字版（来自素材明细）。
- 提供「暂停 / 继续 / 退出」按钮，事件回传固件。

### 唤醒子模块（wakeup）
- 触发：S8 闹钟响起 → 用户按下按钮 → 进入 S9。
- 固件行为：停止闹钟音频，播放庆祝音效，向 H5 发送 `{ "event":"wakeup_celebrate" }`，H5 播放 欢呼.mp4。
- 可选：播放简短 TTS「早安，今天也要元气满满」。
- 结束：庆祝视频/音效播放完毕 → 回调调度器 → S0 待机。

### 边界与异常
- 冥想音频下载失败：回退到「Breathe Into Sleep」本地最小版（TTS 合成简短引导）。
- 闹钟在冥想中响起：立即 pause 冥想，标记断点，切换 S8；用户起床后若仍想继续，语音说「继续冥想」可恢复。
</module_4_meditation_wake>

<firmware_h5_contract>
### 固件 → H5（状态同步，建议通过涂鸦云物模型或局域网 WebSocket）
```json
{
  "msg_type": "module_state",
  "module_id": "breathing|whitenoise|tarot|meditation|wakeup",
  "state": "idle|preparing|playing|paused|completed|error",
  "payload": { /* 模块自定义字段 */ },
  "timestamp_ms": 123456789
}
```

### H5 → 固件（用户交互/素材就绪）
```json
{
  "msg_type": "user_action",
  "action": "start|pause|resume|stop|select_option",
  "module_id": "...",
  "payload": { "option_key": "rain", "value": 0.7 }
}
```

### 语音意图 → 模块映射（由调度器维护）
| 意图 | 目标模块 | 动作 |
|---|---|---|
| "我要呼吸" / "带我呼吸" | breathing | start |
| "白噪音" / "播放雨声" | whitenoise | start(args.sound_type=rain) |
| "抽塔罗" / "占卜" | tarot | start |
| "冥想" / "身体扫描" | meditation | start(args.course_id=med_02) |
| "结束" / "停下来" | current | stop |
| "暂停" / "继续" | current | pause/resume |
| "换一个" | current | next_option |

### 错误码
- `E_MODULE_OK = 0`
- `E_MODULE_NO_ASSET = -1` 素材缺失或下载失败
- `E_MODULE_AUDIO_BUSY = -2` 音频通道被更高优先级占用
- `E_MODULE_INVALID_ARG = -3` 参数错误
- `E_MODULE_NET_FAIL = -4` 网络失败已降级
</firmware_h5_contract>

<audio_mixer_spec>
Mixer 通道定义：
| 通道 | 用途 | 优先级 | 可抢占 |
|---|---|---|---|
| CH_SYSTEM | 按键音、提示音 | 高 | 是 |
| CH_TTS | LLM 输出语音 | 高 | 是（被闹钟抢占） |
| CH_GUIDED | 冥想引导、呼吸引导 | 中 | 是 |
| CH_AMBIENT | 白噪声 | 低 | 是 |
| CH_ALARM | 闹钟 | 最高 | 否 |
| CH_CELEBRATE | 起床欢呼 | 高 | 否 |

规则：
- 同优先级不可叠加；高优先级启动时 fade_out 低优先级。
- 闹钟通道启动时强制 ducking 其他通道至 0。
- 输出前做 clipping 保护，避免 1 W 功放破音。
</audio_mixer_spec>

<led_effect_spec>
| 场景 | LED 效果 | 参数 |
|---|---|---|
| 呼吸模块 | 随吸-屏-呼亮度变化 | inhale_ms/hold_ms/exhale_ms |
| 白噪声 | 柔暗呼吸（雨声偏蓝、棕噪音偏暖） | sound_type 映射色相 |
| 塔罗揭示 | 紫光呼吸 → 金色常亮 | 揭示时长 |
| 冥想 intro | 暖黄光慢呼吸 | 周期 4s |
| 身体扫描 | 分段点亮/流动 | 配合阶段标记 |
| 闹钟 | 全亮/快闪 1Hz | 直至按键 |
| 起床庆祝 | 彩虹渐变一次后熄灭 | 3s |

实现：基于 GPIO P9 的 PWM 或 soft-PWM；扩展板 LED 通过 I2C/SPI LED 驱动芯片控制时复用此接口。
</led_effect_spec>

<asset_inventory>
| 模块 | 素材包/文件 | 存放位置 | 固件侧处理 |
|---|---|---|---|
| 呼吸 | breathing-orbit-package.zip | H5 本地/ CDN | 不解析；触发 H5 加载 |
| 白噪声 | witch-sleep-orb.zip（视觉）+ 音频样本 | H5 / 云端 | 音频样本按需缓存到外部存储 |
| 塔罗 | PocketTarotCards-Rounded.zip + 2 个 HTML 模板 | H5 本地 | 固件只保存卡牌索引表 |
| 冥想 | 5 个 MP3 引导语音 | 云端 | 流式下载或预缓存 |
| 系统 | 按键音、提示音、闹钟音、欢呼音效 | 固件 Flash 最小集 | 优先本地 |

命名约定：`{module_id}_{asset_type}_{ver}.{ext}`，例如 `tarot_card_TheFool_v1.png`、`meditation_03_v1.mp3`。
</asset_inventory>

<engineering_requirements>
1. 模块调度器与状态机解耦：状态机只发送 `enter_module(module_id, args)` 和 `exit_module()`；模块内部自行管理生命周期。
2. 每个模块提供单元测试桩（mock audio/LED/H5），确保 CI 可跑。
3. 所有音频播放走 Mixer，禁止模块直接操作 BSP DAC。
4. 云端素材下载需校验 MD5，失败 3 次后启用降级。
5. 固件日志：模块状态变化、素材加载耗时、播放器 underrun 必须打印。
6. H5 侧需实现「离线包版本号」上报，固件据此决定是否需要更新。
</engineering_requirements>

<acceptance_criteria>
1. 语音说「带我呼吸」→ H5 进入呼吸动画，LED 与扬声器同步 4-7-8 节奏，完成 8 个循环后自动回 AI待机。
2. 语音说「雨声」→ 白噪声 rain 在 3s 淡入后无缝循环，30 分钟倒计时结束自动停止。
3. 语音说「抽塔罗」→ H5 播放转场，卡牌自下而上揭示，固件 TTS 播报解读；用户可说「再抽一张」重复。
4. 语音说「身体扫描」→ 播放对应 MP3，LED 随阶段变化；中途说「暂停」能恢复。
5. 闹钟响起时无论哪个模块都在播，均立即让位于闹钟音频；按键后播放欢呼并回待机。
6. 断网时呼吸、白噪声（算法生成）、闹钟、系统提示音仍可用；冥想/塔罗降级到本地简短版。
</acceptance_criteria>

<todos>
TODO-1（已完成）：素材产物结构已消化，见 docs/assets-manifest.md——breathing-orbit.html（Canvas 轨道动画+吸/呼音效）/ whitenoise.html（五场景 SCENES+load() 接口，替代 252MB 原包）。
TODO-2（已完成）：冥想 5 课 MP3 时长 110.4/116.0/122.4/126.0/115.7s（合计约 9.4MB），版权归属产品方；变速与 TTS 替代留待 V2 评估。
TODO-3（已定稿）：全 78 张牌库 + 正逆位支持；双套素材（webp 79/png 80）已对齐，固件卡牌索引 firmware-config/tarot_deck_index.json。
TODO-4（已决策）：纯 H5 缓存（MVP 默认）——白噪声/冥想音频由手机 H5 播放；固件断网兜底走 Pink/Brown 噪声算法实时生成；后期如需脱离手机本地播放再评估 SD 卡（SPI0 域 P44-P47）。
TODO-5（已决策）：MVP 仅板载 P9（soft-PWM 单色）；量产若需 RGB 外接 I2C 灯带走 GPIO_0/1（I2C1 预留）。
</todos>

---

## 附：四个模块 → 状态机映射速查

| 产品功能模块 | 工程 module_id | 进入状态 | 退出去向 | 核心固件输出 |
|---|---|---|---|---|
| 呼吸模块 | breathing | S6 睡眠体验 | S4 AI待机 | 引导音频 + LED 节奏同步 |
| 白噪声模块 | whitenoise | S6 睡眠体验 | S4 AI待机 / S8 闹钟抢占 | 循环环境音 |
| 塔罗模块 | tarot | S7 塔罗抽卡 | S4 AI待机 / S8 闹钟抢占 | 随机抽卡 + TTS 解读 + H5 揭示事件 |
| 冥想模块 | meditation | S6 睡眠体验 | S4 AI待机 / S8 闹钟抢占 | 引导 MP3 播放 + LED 主题 |
| 唤醒模块 | wakeup | S9 起床完成 | S0 待机 | 停止闹钟 + 欢呼音效/视频触发 |
