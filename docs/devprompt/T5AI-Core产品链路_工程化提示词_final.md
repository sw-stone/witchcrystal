# T5AI-Core 产品链路工程化提示词

> 用途：将「AI 睡眠魔法球底座」的产品链路（状态机 + 输入事件 + 语音管线 + 手机端视觉同步）转化为可直接投喂给涂鸦 TuyaOpen AI 开发流程或 AI 编码助手（Cursor / Claude Code / Copilot 等）的结构化提示词。
> 边界：固件负责状态调度、语音链路与云同步；视觉渲染与视频播放主体在手机端 H5/WebView。
> 配套文件：《T5AI-Core全产品开发主提示词.md》（总纲）、《T5AI-Core产品功能模块_工程化提示词.md》（模块细化）。

---

<role>
你是涂鸦智能 TuyaOpen 平台的资深嵌入式固件工程师，负责在 T5AI-Core 开发板上实现一款「AI 睡眠魔法球底座」产品的完整固件。你熟悉 T5-E1 模组、TuyaOpen 板级 Config（TUYA_T5AI_CORE.config）、涂鸦 AI 语音管线（VAD → ASR → LLM Agent → TTS）以及 tuyaos GPIO/UART/I2C 驱动开发。
</role>

<task>
基于下述硬件约束与产品状态机，设计并实现固件：
1. 实现完整的设备状态机（FSM），含状态转移、进入/退出动作。
2. 实现 3 路物理按钮的事件采集（去抖 + 边沿触发）。
3. 实现 AI 语音对话链路（唤醒、对话、打断）。
4. 通过 Wi-Fi 与手机端 H5 / 涂鸦云联动，驱动手机屏幕上的视觉状态（视频/H5 切换）。
5. 输出符合 TuyaOpen 工程规范的代码（板级 Config 复用、BSP 驱动、应用层分层）。
</task>

<hardware_constraints>
目标硬件：T5AI-Core 开发板（Tuya T5-E1 模组）

- MCU：ARMv8-M Star（M33F），主频最高 480 MHz
- 存储：片内 8 MB Flash + 16 MB RAM
- 无线：2.4 GHz Wi-Fi + 蓝牙 LE 5.4（板载天线）
- 音频输入：1 路板载模拟麦克风（CH1）+ 1 路扬声器回采（CH2，支持 AEC 回声消除/打断）
- 音频规格：16 kHz 采样率 / 16 bit 位深
- 音频输出：1 W 功放（5 V 电源域）→ 外接 4Ω 3W 扬声器（JST PH 1.25 mm）
- 板载交互资源：用户 LED（GPIO P9）、用户按钮（GPIO P29）、复位按钮（RST）
- 扩展：44 Pin 2.54 mm 排针（引出 GPIO/UART/SPI/I2C，5V 与 3.3V 电源域）、1 路 USB Host
- 固件烧录/调试：Type-C USB，双路串口（烧录 + 日志），UART 烧录后可复用
- 电源：USB 5 V / 3.7 V 锂电池双输入，ETA6003 电源管理
- 板级配置：TUYA_T5AI_CORE.config（含板载 Mic/Speaker BSP），以官方 Config 为基础二次开发
- 编码约束：RAM/Flash 预算敏感；音频回调内禁止阻塞操作；Wi-Fi 断线必须有本地降级态
</hardware_constraints>

<product_context>
产品形态：手机插入底座（屏幕朝上）+ 底座内魔法球 AI 角色。
产品主线：助眠（睡眠魔法激活 → AI 主动陪聊 → 冥想/白噪音/呼吸/塔罗）→ 唤醒（闹钟 → 起床庆祝）。
双通道交互：

- 软件层（手机屏幕）：视频/H5 视觉状态，由固件状态机通过云/H5 指令驱动切换。
- 硬件层（底座本体）：3 个物理按钮（前/后/下）+ 麦克风 + 扬声器 + LED。
  「按钮-下」复用为手机在位检测：手机放入底座（表面朝上）时压下该按钮。
</product_context>

<state_machine>
状态编码：S0~S9。每态定义：entry_trigger（进入事件）、sw_action（软件层/手机屏动作）、hw_action（硬件层动作）、exit_to（可转移去向）。

S0 STANDBY 待机
- entry_trigger：上电默认态；或任一流程结束后的回归态
- sw_action：手机黑屏，结束一切交互
- hw_action：LED 熄灭；音频静音；进入低功耗
- exit_to：S1（按钮-前）

S1 FIRST_USE 首次使用（引导）
- entry_trigger：按钮-前 按下
- sw_action：手机播放 引入.mp4（引导视频）
- hw_action：LED P9 指示引导态
- exit_to：S2（超时/用户按 按钮-后）、S3（手机放入底座）

S2 FORCE_STANDBY 强制回待机
- entry_trigger：按钮-后 按下（任意状态下可触发，全局最高优先级事件）
- sw_action：手机黑屏（结束一切交互）
- hw_action：停止所有音频播放与 AI 会话，清空会话上下文
- exit_to：S0

S3 DOCKED 手机入座
- entry_trigger：按钮-下 被压下（手机放入底座，表面朝上，硬件在位检测）
- sw_action：手机播放 锁定.mp4（提示"手机已锁定、睡眠魔法激活中"）
- hw_action：播放入座音效；上报云端设备状态 docked=true
- exit_to：S4（激活流程完成，延时或云端确认）；S0（按钮-下 弹起 = 手机离座）

S4 AI_STANDBY AI 待机
- entry_trigger：S3 激活完成
- sw_action：手机循环播放 AI待机.mp4（魔法球待机动态）
- hw_action：LED 呼吸灯效；VAD 常开监听
- exit_to：S5（AI 主动发起 / 用户语音）、S2（按钮-后）、S0（离座）

S5 AI_ACTIVE_SPEAKING AI 主动说话
- entry_trigger：S4 下 AI 定时/情境触发主动发起沟通，或用户语音被 VAD 捕获
- sw_action：AI 说话时播放 AI说话.mp4（魔法球说话动态）；不说话时回落 AI待机.mp4
- hw_action：全双工语音对话管线（ASR → LLM Agent → TTS → 功放）；AEC 回采支持用户语音打断 TTS 播报
- exit_to：S6（对话中用户选择睡眠体验）、S4（对话结束静默 30s）

S6 SLEEP_EXPERIENCE 睡眠体验（冥想/白噪音/呼吸/塔罗 H5）
- entry_trigger：S5 对话中用户语音选择，或 AI 推荐后用户确认
- sw_action：手机进入对应 H5（冥想 / 白噪音 / 呼吸引导 / 塔罗）；塔罗路径：塔罗音效 → 卡牌自下而上出现动画 → AI 语音解读
- hw_action：白噪音/冥想音频经功放输出；音量随睡眠阶段自动衰减
- exit_to：S4（体验结束）、S7（到达闹钟时刻，任意状态可直接触发）

S7 TAROT_DRAW 塔罗抽卡（语音指令子流程）
- entry_trigger：S4/S6 下用户语音请求抽卡
- sw_action：播放 塔罗转场.mp4 → 卡牌自下而上出现 → AI 语音解读结果
- hw_action：TTS 解读播报（支持打断）
- exit_to：S4（解读完成）、S7 可被闹钟抢占 → S8

S8 ALARM_RINGING 闹钟响起
- entry_trigger：系统时钟到达预设闹钟时刻（全局抢占，任意状态可进入）
- sw_action：魔法球亮起；手机循环播放 闹钟.mp4 + 闹钟音频，直至按钮按下
- hw_action：闹钟音频循环输出（最大音量）；LED 全亮/闪烁
- exit_to：S9（按钮按下）

S9 WAKEUP_DONE 起床完成（瞬态）
- entry_trigger：闹钟响铃期间用户按下物理按钮
- sw_action：停止闹钟，播放 欢呼.mp4（起床庆祝视频）
- hw_action：停止闹钟音频，播放庆祝音效
- exit_to：S0（庆祝播完自动回归待机）
</state_machine>

<input_events>
| 事件 ID | 源 | 映射 | 优先级 | 去抖 |
|---|---|---|---|---|
| EVT_BTN_FRONT | 按钮-前 | GPIO_2（J2 pin20，排针扩展；板载 P29 为调试备选） | 中 | 50 ms |
| EVT_BTN_BACK | 按钮-后 | GPIO_3（J1 pin16，排针扩展） | 最高（全局强制回待机） | 50 ms |
| EVT_BTN_DOWN | 按钮-下 | GPIO_4（J1 pin21，排针扩展），复用手机在位检测（电平触发，非边沿） | 高 | 100 ms |
| EVT_VOICE | 麦克风 CH1 | VAD 语音活动检测 | 中 | — |
| EVT_ALARM_TIMER | 系统 RTC | 闹钟时刻到达 | 最高（抢占） | — |
| EVT_CLOUD_CMD | Wi-Fi/涂鸦云 | H5 联动指令 | 中 | — |

实现要求：按钮采用 GPIO 中断 + 软件去抖；EVT_BTN_DOWN 用电平状态表征手机在/离座；事件队列统一分发到 FSM。
</input_events>

<voice_pipeline>
基于涂鸦 AI 语音管线实现（参照 your_chat_bot demo）：

- 采集：16 kHz / 16 bit 单通道，板载 BSP 麦克风驱动
- AEC：CH2 回采通道做回声消除，支撑 TTS 播报中用户语音打断
- 链路：VAD → ASR → LLM Agent（人设=产品人格定位）→ TTS → 1 W 功放输出
- 打断策略：TTS 播报中检测到用户语音即截断当前播报并重新进入聆听
- 离线降级：Wi-Fi 断线时保留按钮/闹钟/白噪音本地功能，语音对话提示网络不可用
</voice_pipeline>

<software_layer_sync>
手机视觉状态与固件 FSM 严格一一对应，通过涂鸦云 IoT 通道（或局域网 BLE 辅助）下发状态码：
S0=black / S1=intro_video / S3=locked_video / S4=ai_idle_loop / S5=ai_speaking(说话态与待机态随 TTS 状态切换) / S6=sleep_h5{meditation|whitenoise|breathing|tarot} / S7=tarot_transition / S8=alarm_loop / S9=cheer_video
媒体资产（手机端预置）：引入.mp4、锁定.mp4、AI待机.mp4、AI说话.mp4、塔罗音效.mp4、塔罗转场.mp4、闹钟.mp4、欢呼.mp4。
固件不存储视频，只负责状态同步与指令下发；闹钟响铃期间需心跳保活确认手机端在播。
</software_layer_sync>

<engineering_requirements>
1. 架构分层：`app/`（FSM + 业务）、`drivers/`（按钮/LED 扩展驱动）、`net/`（云同步）、`audio/`（管线封装）；复用 TUYA_T5AI_CORE.config 与官方 BSP。
2. FSM 用显式状态表（state × event → action/transition）实现，禁止 if-else 散落全局。
3. 所有音频回调严禁阻塞；Wi-Fi 重连指数退避；看门狗启用。
4. 日志：双路串口日志分级输出（ERROR/WARN/INFO/DEBUG），关键状态转移必须打 INFO。
5. 低功耗：S0/S4 进入低功耗模式，事件中断唤醒。
6. 提供单元可测的状态转移表 + 按钮去抖模块。
</engineering_requirements>

<acceptance_criteria>
1. 全部 9+1 个状态及转移可复现：上电→待机；按钮-前→引导；按钮-后（任意态）→黑屏回待机；放手机→锁定→AI待机；AI 主动说话与语音对话可正常进行且 TTS 可被打断；语音可选 4 类睡眠体验；语音抽塔罗有转场+解读；闹钟到点全局抢占、循环响铃、按钮停止后播放庆祝并回待机。
2. 按钮 50ms 去抖无误触发；手机离座立即回待机。
3. Wi-Fi 断线时按钮/闹钟/白噪音仍可用。
4. 状态码与手机端视觉同步误差 < 500 ms。
5. 固件在 8 MB Flash / 16 MB RAM 预算内编译通过，烧录至 T5AI-Core 实机验证。
</acceptance_criteria>

<todos>
TODO-1（已定稿）：按钮-前=GPIO_2（J2 pin20）/ 按钮-后=GPIO_3（J1 pin16）/ 按钮-下=GPIO_4（J1 pin21，电平触发在位检测）。依据官方原理图 T5AI-Core_V101-SCH 定稿，详见项目 docs/hardware/pinmap.md。
TODO-2（已决策）：S3→S4 激活完成条件 = 固定延时 3s（Kconfig S3_TO_S4_DELAY_MS 可调，实现于 sm_state_machine.c on_enter_S3）。
TODO-3（已确认）：「魔罗抽卡」即「塔罗抽卡」，非独立功能。
TODO-4（已决策）：S1 退出条件 = 超时 30s / 按钮-后 / 手机入座直接跳 S3（Kconfig INTRO_TIMEOUT_S 可调）。
</todos>
