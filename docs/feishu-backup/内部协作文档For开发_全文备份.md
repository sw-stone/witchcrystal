# 【To Lin】内部协作文档For开发

## 一、产品定位：

| 要素 | 内容 |
|-|-|
| 产品名称 | 屿眠 ｜ Sleep Isle |
| 一句话介绍 | A little island for your sleep. |
| 主 Slogan | End the scroll. Enter the sleep island.（结束刷手机，进入睡眠） |
| 备选 Slogan | Leave the day behind. Sleep on your own island. |
| 副标题 | AI Sleep Ritual Orb · 古希腊掌管睡眠的神 · 一颗接管手机、引导入睡的 AI 魔法水晶球 |
| 礼物场景 Slogan | A little magic for better nights.（送给漫长夜晚的一点魔法） |

> 产品名：屿眠 ｜Sleep Isle 一句话介绍：A little island for your sleep. Slogan：End the scroll. Enter the sleep.
> 
> End the scroll. Enter the sleep island.
> 
> 结束刷手机，进入睡眠
> 
> 副标题：AI Sleep Ritual Orb
> 
> 古希腊掌管睡眠的神
> 
> 一颗接管手机、引导入睡的 AI 魔法水晶球
> 
> Magic Tracks For Sleeping
> 
> 礼物场景 Slogan
> 
> A little magic for better nights.
> 
> 送给漫长夜晚的一点魔法
> 
> 产品名：屿眠 sleep isle 
> 
> 一句话介绍：A little island for your sleep.
> 
> Slogan：Leave the day behind. Sleep on your own island.

<grid>
<column width-ratio="0.348543">
![](https://feishu.cn/file/BbvhbJVBKoD3kGxkQU2cNi43nge)
</column>
<column width-ratio="0.651457">
![](https://feishu.cn/file/MwWmb1opZoK4Ndx949tc3bv1nHJ)
</column>
</grid>



## 二、用户画像：

受众画像：

1️⃣核心层：「手机囚徒」

画像：18-35岁，一二线城市，睡前平均刷手机 1.5-2 小时，明知该睡但"停不下来"。包括：

 • 报复性熬夜族：白天被工作/学习压榨，晚上舍不得睡，手机是唯一属于自己的时间。

 • 焦虑型失眠者：躺下后脑子像跑马灯，需要"被接管"才能停止思考。

 • 仪式感爱好者：喜欢神秘学、塔罗、女巫美学、小众文化，愿意为"氛围"付费。

2️⃣扩展层：「睡眠焦虑者」

画像：35-50岁，有慢性睡眠问题，尝试过褪黑素、白噪音 App、冥想但效果不佳。被医生推荐过 Dodow 这类设备。

3️⃣外围层：「礼物购买者」

画像：为伴侣、闺蜜、父母购买助眠礼物的人群。水晶球形态 + 塔罗元素使其具备强烈的"礼物感"。



## 三、产品功能模块：

<grid>
<column width-ratio="0.222489">
![](https://feishu.cn/file/HornbrgImo0e8XxI9WicI4ePnke)
</column>
<column width-ratio="0.285621">
![](https://feishu.cn/file/Jd9SbaDlNowRxHxaJVuc271lnng)
</column>
<column width-ratio="0.251519">
![](https://feishu.cn/file/LC3Gb1cWDobfknxaHcSc0WFGn0e)
</column>
<column width-ratio="0.240371">
![](https://feishu.cn/file/WkkPbEIbUouzVExEVSOcDlz7nHg)
</column>
</grid>



## 四、产品原型设计参照：

![](https://feishu.cn/file/EbG5b3j2doP2uaxTFSZcOx9ln6f)

## 五、产品人格定位  
<cite doc-id="VYtswh5BmiGNJKko7d3cXXRYnte" file-type="wiki" title="睡眠魔法 AI 人格文档_V1.0" type="doc"></cite>



## 六、User Journey：

<figure view-type="Card"><source name="T5AI-Core全产品开发主提示词.md" mime="text/markdown" size="18988" token="MLn1b511MoSUpExXnEocilNxn6c"/></figure>

<figure view-type="Card"><source name="T5AI-Core产品功能模块_工程化提示词.md" mime="text/markdown" size="18543" token="RAlZbsu4QoeAhPxG5m8c7XyDnsg"/></figure>

### 产品链路：

<table><colgroup><col/><col/><col/><col/><col/><col/><col/><col/><col/><col/><col/><col/></colgroup><tbody><tr><td></td><td><b>待机</b></td><td><b>首次使用（是否按下前）</b></td><td><b>强行回待机</b></td><td><b>①手机放入底座（表面朝上）</b></td><td><b>②</b></td><td><b>③AI待机</b></td><td><b>④AI主动说话</b></td><td><b>⑤AI初始睡眠体验</b></td><td><b>⑥ 魔罗抽卡</b></td><td><b>⑦ 闹钟响起</b></td><td><b>⑧ 起床完成</b></td></tr><tr><td><b>软件层面（上）</b></td><td>黑屏</td><td><figure view-type="Preview"><source name="引入.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="22525174" token="QjJqbRJpCoWhsmxNG1ccCsm9njf"/></figure></td><td>黑屏（结束一切交互）</td><td><figure view-type="Preview"><source name="锁定.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="15597100" token="T0nhb7VsIo6aWmxD03AcwbLInlc"/></figure><br/>手机已锁定、睡眠魔法激活中）</td><td></td><td><figure view-type="Preview"><source name="AI待机.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="21008222" token="Wy7bbQ38No9b7mxUi8gcsL2cnce"/></figure><br/>AI待机.mp4（魔法球待机动态）</td><td>主动发起沟通，（魔法球说话动态）<br/>AI说话播放——AI说话.mp4<figure view-type="Preview"><source name="AI说话.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="20534189" token="PSKmbRkqvopnkUxCPSDcCd7sn9d"/></figure><br/><br/>ai不说话时候——AI待机.mp4<figure view-type="Preview"><source name="AI待机.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="21008222" token="MHsxbzTSaovx8VxZd67cKr2snhd"/></figure></td><td>进入冥想、白噪音、呼吸或塔罗 的H5；<br/>→ 塔罗音效.mp4<br/>→ 卡牌自下而上出现<br/>→ AI 语音解读</td><td>语音请求抽卡<figure view-type="Preview"><source name="塔罗转场.mp4" mime="video/mp4" origin-height="1280.000000" origin-width="720.000000" size="1540673" token="UQBHbKiihoDUfMxWwnIc9mMlnhh"/></figure><br/><br/>→ 卡牌自下而上出现<br/>→ AI 语音解读</td><td>（魔法球亮起，播放闹钟音频）循环播放闹钟视频，直至按下按钮<figure view-type="Preview"><source name="闹钟.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="40365699" token="UphJbdBeComeW4xUIZjcnCJzn9g"/></figure></td><td>（停止闹钟，播放起床欢呼视频，返回待机）<br/><figure view-type="Preview"><source name="欢呼.mp4" mime="video/mp4" origin-height="1920.000000" origin-width="1080.000000" size="5087267" token="FSdjbdYFHon49cxgZ6echJ8zncd"/></figure></td></tr><tr><td><b>物理硬件（下）</b></td><td></td><td>按钮-前</td><td>按钮-后</td><td>按钮-下</td><td>/</td><td>/</td><td>无硬件操作</td><td>无硬件操作</td><td></td><td>按钮-下</td><td>用户按下物理按钮，停止闹钟，</td></tr></tbody></table>

**描述词参照：**

> <role> 你是涂鸦智能 TuyaOpen 平台的资深嵌入式固件工程师，负责在 T5AI-Core 开发板上实现一款「AI 睡眠魔法球底座」产品的完整固件。你熟悉 T5-E1 模组、TuyaOpen 板级 Config（TUYA_T5AI_CORE.config）、涂鸦 AI 语音管线（VAD → ASR → LLM Agent → TTS）以及 tuyaos GPIO/UART/I2C 驱动开发。 </role>
> 
> <task> 基于下述硬件约束与产品状态机，设计并实现固件： 1. 实现完整的设备状态机（FSM），含状态转移、进入/退出动作。 2. 实现 3 路物理按钮的事件采集（去抖 + 边沿触发）。 3. 实现 AI 语音对话链路（唤醒、对话、打断）。 4. 通过 Wi-Fi 与手机端 H5 / 涂鸦云联动，驱动手机屏幕上的视觉状态（视频/H5 切换）。 5. 输出符合 TuyaOpen 工程规范的代码（板级 Config 复用、BSP 驱动、应用层分层）。 </task>
> 
> <hardware_constraints> 目标硬件：T5AI-Core 开发板（Tuya T5-E1 模组）
> 
> - MCU：ARMv8-M Star（M33F），主频最高 480 MHz
> - 存储：片内 8 MB Flash + 16 MB RAM
> - 无线：2.4 GHz Wi-Fi + 蓝牙 LE 5.4（板载天线）
> - 音频输入：1 路板载模拟麦克风（CH1）+ 1 路扬声器回采（CH2，支持 AEC 回声消除/打断）
> - 音频规格：16 kHz 采样率 / 16 bit 位深
> - 音频输出：1 W 功放（5 V 电源域）→ 外接 4Ω 3W 扬声器（JST PH 1.25 mm）
> - 板载交互资源：用户 LED（GPIO P9）、用户按钮（GPIO P29）、复位按钮（RST）
> - 扩展：44 Pin 2.54 mm 排针（引出 GPIO/UART/SPI/I2C，5V 与 3.3V 电源域）、1 路 USB Host
> - 固件烧录/调试：Type-C USB，双路串口（烧录 + 日志），UART 烧录后可复用
> - 电源：USB 5 V / 3.7 V 锂电池双输入，ETA6003 电源管理
> - 板级配置：TUYA_T5AI_CORE.config（含板载 Mic/Speaker BSP），以官方 Config 为基础二次开发
> - 编码约束：RAM/Flash 预算敏感；音频回调内禁止阻塞操作；Wi-Fi 断线必须有本地降级态 </hardware_constraints>
> 
> <product_context> 产品形态：手机插入底座（屏幕朝上）+ 底座内魔法球 AI 角色。 产品主线：助眠（睡眠魔法激活 → AI 主动陪聊 → 冥想/白噪音/呼吸/塔罗）→ 唤醒（闹钟 → 起床庆祝）。 双通道交互：
> 
> - 软件层（手机屏幕）：视频/H5 视觉状态，由固件状态机通过云/H5 指令驱动切换。
> - 硬件层（底座本体）：3 个物理按钮（前/后/下）+ 麦克风 + 扬声器 + LED。 「按钮-下」复用为手机在位检测：手机放入底座（表面朝上）时压下该按钮。 </product_context>
> 
> <state_machine> 状态编码：S0\~S8。每态定义：entry_trigger（进入事件）、sw_action（软件层/手机屏动作）、hw_action（硬件层动作）、exit_to（可转移去向）。
> 
> S0 STANDBY 待机
> 
> - entry_trigger：上电默认态；或任一流程结束后的回归态
> - sw_action：手机黑屏，结束一切交互
> - hw_action：LED 熄灭；音频静音；进入低功耗
> - exit_to：S1（按钮-前）
> 
> S1 FIRST_USE 首次使用（引导）
> 
> - entry_trigger：按钮-前 按下
> - sw_action：手机播放 引入.mp4（引导视频）
> - hw_action：LED P9 指示引导态
> - exit_to：S2（超时/用户按 按钮-后）、S3（手机放入底座）
> 
> S2 FORCE_STANDBY 强制回待机
> 
> - entry_trigger：按钮-后 按下（任意状态下可触发，全局最高优先级事件）
> - sw_action：手机黑屏（结束一切交互）
> - hw_action：停止所有音频播放与 AI 会话，清空会话上下文
> - exit_to：S0
> 
> S3 DOCKED 手机入座
> 
> - entry_trigger：按钮-下 被压下（手机放入底座，表面朝上，硬件在位检测）
> - sw_action：手机播放 锁定.mp4（提示"手机已锁定、睡眠魔法激活中"）
> - hw_action：播放入座音效；上报云端设备状态 docked=true
> - exit_to：S4（激活流程完成，延时或云端确认）；S0（按钮-下 弹起 = 手机离座）
> 
> S4 AI_STANDBY AI 待机
> 
> - entry_trigger：S3 激活完成
> - sw_action：手机循环播放 AI待机.mp4（魔法球待机动态）
> - hw_action：LED 呼吸灯效；VAD 常开监听
> - exit_to：S5（AI 主动发起 / 用户语音）、S2（按钮-后）、S0（离座）
> 
> S5 AI_ACTIVE_SPEAKING AI 主动说话
> 
> - entry_trigger：S4 下 AI 定时/情境触发主动发起沟通，或用户语音被 VAD 捕获
> - sw_action：AI 说话时播放 AI说话.mp4（魔法球说话动态）；不说话时回落 AI待机.mp4
> - hw_action：全双工语音对话管线（ASR → LLM Agent → TTS → 功放）；AEC 回采支持用户语音打断 TTS 播报
> - exit_to：S6（对话中用户选择睡眠体验）、S4（对话结束静默 30s）
> 
> S6 SLEEP_EXPERIENCE 睡眠体验（冥想/白噪音/呼吸/塔罗 H5）
> 
> - entry_trigger：S5 对话中用户语音选择，或 AI 推荐后用户确认
> - sw_action：手机进入对应 H5（冥想 / 白噪音 / 呼吸引导 / 塔罗）；塔罗路径：塔罗音效 → 卡牌自下而上出现动画 → AI 语音解读
> - hw_action：白噪音/冥想音频经功放输出；音量随睡眠阶段自动衰减
> - exit_to：S4（体验结束）、S7（到达闹钟时刻，任意状态可直接触发）
> 
> S7 TAROT_DRAW 塔罗抽卡（语音指令子流程）
> 
> - entry_trigger：S4/S6 下用户语音请求抽卡
> - sw_action：播放 塔罗转场.mp4 → 卡牌自下而上出现 → AI 语音解读结果
> - hw_action：TTS 解读播报（支持打断）
> - exit_to：S4（解读完成）、S7 可被闹钟抢占 → S8
> 
> S8 ALARM_RINGING 闹钟响起
> 
> - entry_trigger：系统时钟到达预设闹钟时刻（全局抢占，任意状态可进入）
> - sw_action：魔法球亮起；手机循环播放 闹钟.mp4 + 闹钟音频，直至按钮按下
> - hw_action：闹钟音频循环输出（最大音量）；LED 全亮/闪烁
> - exit_to：S9（按钮按下）
> 
> S9 WAKEUP_DONE 起床完成（瞬态）
> 
> - entry_trigger：闹钟响铃期间用户按下物理按钮
> - sw_action：停止闹钟，播放 欢呼.mp4（起床庆祝视频）
> - hw_action：停止闹钟音频，播放庆祝音效
> - exit_to：S0（庆祝播完自动回归待机） </state_machine>
> 
> <input_events>
> 
> <voice_pipeline> 基于涂鸦 AI 语音管线实现（参照 your_chat_bot demo）：
> 
> - 采集：16 kHz / 16 bit 单通道，板载 BSP 麦克风驱动
> - AEC：CH2 回采通道做回声消除，支撑 TTS 播报中用户语音打断
> - 链路：VAD → ASR → LLM Agent（人设=产品人格定位）→ TTS → 1 W 功放输出
> - 打断策略：TTS 播报中检测到用户语音即截断当前播报并重新进入聆听
> - 离线降级：Wi-Fi 断线时保留按钮/闹钟/白噪音本地功能，语音对话提示网络不可用 </voice_pipeline>
> 
> <software_layer_sync> 手机视觉状态与固件 FSM 严格一一对应，通过涂鸦云 IoT 通道（或局域网 BLE 辅助）下发状态码： S0=black / S1=intro_video / S3=locked_video / S4=ai_idle_loop / S5=ai_speaking(说话态与待机态随 TTS 状态切换) / S6=sleep_h5{meditation|whitenoise|breathing|tarot} / S7=tarot_transition / S8=alarm_loop / S9=cheer_video 媒体资产（手机端预置）：引入.mp4、锁定.mp4、AI待机.mp4、AI说话.mp4、塔罗音效.mp4、塔罗转场.mp4、闹钟.mp4、欢呼.mp4。 固件不存储视频，只负责状态同步与指令下发；闹钟响铃期间需心跳保活确认手机端在播。 </software_layer_sync>
> 
> <engineering_requirements>
> 
> 1. 架构分层：`app/`（FSM + 业务）、`drivers/`（按钮/LED 扩展驱动）、`net/`（云同步）、`audio/`（管线封装）；复用 TUYA_T5AI_CORE.config 与官方 BSP。
> 2. FSM 用显式状态表（state × event → action/transition）实现，禁止 if-else 散落全局。
> 3. 所有音频回调严禁阻塞；Wi-Fi 重连指数退避；看门狗启用。
> 4. 日志：双路串口日志分级输出（ERROR/WARN/INFO/DEBUG），关键状态转移必须打 INFO。
> 5. 低功耗：S0/S4 进入低功耗模式，事件中断唤醒。
> 6. 提供单元可测的状态转移表 + 按钮去抖模块。 </engineering_requirements>
> 
> <acceptance_criteria>
> 
> 1. 全部 9+1 个状态及转移可复现：上电→待机；按钮-前→引导；按钮-后（任意态）→黑屏回待机；放手机→锁定→AI待机；AI 主动说话与语音对话可正常进行且 TTS 可被打断；语音可选 4 类睡眠体验；语音抽塔罗有转场+解读；闹钟到点全局抢占、循环响铃、按钮停止后播放庆祝并回待机。
> 2. 按钮 50ms 去抖无误触发；手机离座立即回待机。
> 3. Wi-Fi 断线时按钮/闹钟/白噪音仍可用。
> 4. 状态码与手机端视觉同步误差 < 500 ms。
> 5. 固件在 8 MB Flash / 16 MB RAM 预算内编译通过，烧录至 T5AI-Core 实机验证。 </acceptance_criteria>
> 
> <todos> TODO-1（需硬件确认）：「按钮-前 / 按钮-后 / 按钮-下」三路按钮的 GPIO 引脚分配——T5AI-Core 板载仅 1 个用户按钮（P29），其余两路需经 44 Pin 排针扩展，请按原理图（T5AI-Core_V101-SCH）确认具体引脚后替换上文映射。 TODO-2（需产品确认）：S3→S4 的激活完成条件（固定延时 / 云端确认 / 二次交互）。 TODO-3（需产品确认）：原文「魔罗抽卡」按上下文理解为「塔罗抽卡」；若为独立功能请补充差异。 TODO-4（需产品确认）：S1 首次使用引导视频的退出条件与超时时长。 </todos>



### 产品功能模块

#### 1）呼吸模块功能代码：

<figure view-type="Card"><source name="breathing-orbit-package.zip" mime="application/zip" size="163188" token="EnOCbi3zBoTs33xCjnhc6BmXnKd"/></figure>

#### 2）白噪声模块功能代码：

<figure view-type="Card"><source name="witch-sleep-orb.zip" mime="application/zip" size="252386294" token="PKErbzOO9occoLxQMO3cFqYOn4f"/></figure>

#### 3）塔罗模块功能代码（开发已有）：

- 塔罗图片素材：

<figure view-type="Card"><source name="PocketTarotCards-Rounded.zip" mime="application/zip" size="81980698" token="DCwXbY5PooIqTIxqt5lcLHWQnlg"/></figure>

- 塔罗视觉模板：

<figure view-type="Card"><source name="塔罗应用界面样机与组件规范_v4.html" mime="text/html" size="21993" token="XkRWboQouojLFTxV5wcc4MQEnNc"/></figure>

<figure view-type="Card"><source name="塔罗应用设计令牌_v4_柔光舒缓版.html" mime="text/html" size="23227" token="LUO1b3wXLoWQo5xziqqcCTN1nxc"/></figure>



#### 4）冥想+唤醒模块功能逻辑框架：

##### 整体逻辑框架：

Release the Day

放下今天｜处理反刍

Relax Your Body

身体扫描｜最通用的睡前冥想

Breathe Into Sleep

慢呼吸｜快速安静下来

Soften the Tension

渐进式肌肉放松｜释放身体压力

You’re Safe Here

慈心与安全感｜孤独、焦虑、情绪低落

##### 素材明细：

<table><colgroup><col/><col/><col/><col/><col/><col/></colgroup><tbody><tr><td></td><td><b>冥想素材1</b></td><td><b>冥想素材2</b></td><td><b>冥想素材3</b></td><td><b>冥想素材4</b></td><td><b>冥想素材5</b></td></tr><tr><td><b>文字版</b></td><td><ol><li seq="1">Release the Day｜放下今天 · 仪式感反刍</li></ol><br/>今天已经走到这里了。<br/>现在，你不需要再完成什么，也不需要再想清楚什么。<br/>那些还没有回复的消息，没有做完的事情，没有得到答案的问题，都可以暂时留在今天。<br/>轻轻吸一口气。<br/>再慢慢呼出来。<br/>想象你正站在一天的尽头。<br/>手里抱着很多细小的东西：一句没有说出口的话，一个反复回想的瞬间，一件还没有解决的事，一点懊恼，也许还有一点不甘心。<br/>现在，把它们一件一件放下来。<br/>不是丢掉它们。<br/>只是告诉自己：今晚，我不需要继续拿着。<br/>明天的你，会有明天的时间去处理。<br/>现在的你，只需要休息。<br/>再吸一口气。<br/>呼气的时候，想象今天慢慢离开你的身体。<br/>肩膀松一点。<br/>眉头松一点。<br/>牙齿也不要再咬紧。<br/>今天发生过的一切，都已经发生了。<br/>你不需要在脑海里重新经历一次，才能证明它重要。<br/>这一刻，没有什么需要解决。<br/>今天到这里，就可以了。<br/>让夜晚接过剩下的事情。<br/>你只需要慢慢地，回到睡眠里。</td><td><ol><li seq="2">Relax Your Body｜身体扫描 · 最通用的睡前冥想</li></ol><br/>找一个舒服的位置躺下来。<br/>不需要刻意保持姿势。<br/>让床承接你的重量。<br/>先把注意力放到额头。<br/>如果那里还有一点紧绷，让它慢慢展开。<br/>眼睛周围，也松下来。<br/>你已经不需要再看什么了。<br/>放松下巴。<br/>让舌头自然地落在嘴里。<br/>现在，把注意力移到肩膀。<br/>想象肩膀上的重量，正在一点一点向下沉。<br/>你不需要再撑住今天。<br/>手臂放松。<br/>手掌放松。<br/>每一根手指，都可以安静下来。<br/>慢慢来到胸口和腹部。<br/>不需要改变呼吸。<br/>只是感觉身体正在自己呼吸。<br/>吸气。<br/>身体轻轻起伏。<br/>呼气。<br/>身体又沉回床面。<br/>现在来到腰部、臀部、大腿。<br/>让这些地方变得越来越重。<br/>膝盖放松。<br/>小腿放松。<br/>脚踝放松。<br/>最后，是你的脚。<br/>从头到脚，不需要任何地方保持警觉。<br/>如果还有某个地方没有完全放松，也没有关系。<br/>你不需要努力入睡。<br/>只需要躺在这里。<br/>让身体比刚才更重一点。<br/>再重一点。<br/>床正在托住你。<br/>现在，什么都不用做了。</td><td><ol><li seq="3">Breathe Into Sleep｜慢呼吸 · 快速安静下来</li></ol><br/>现在，不需要做一个很深的呼吸。<br/>只是慢一点。<br/>轻轻吸气。<br/>一、二、三、四。<br/>稍微停一下。<br/>然后慢慢呼气。<br/>一、二、三、四、五、六。<br/>很好。<br/>再来一次。<br/>吸气的时候，不需要用力。<br/>只是让空气自然地进来。<br/>一、二、三、四。<br/>呼气。<br/>一、二、三、四、五、六。<br/>想象每一次呼气，都在告诉身体：<br/>可以慢下来了。<br/>你不需要强迫自己平静。<br/>也不需要赶走脑海里的想法。<br/>如果一个念头出现，就让它出现。<br/>然后，把注意力轻轻带回呼吸。<br/>吸气。<br/>空气进入身体。<br/>呼气。<br/>身体向下沉。<br/>每一次呼气，都比吸气稍微长一点。<br/>就像海浪来到岸边，然后慢慢退去。<br/>你不需要追着海浪走。<br/>只需要待在这里。<br/>吸气。<br/>呼气。<br/>如果你开始忘记数字，也没有关系。<br/>如果你的注意力已经变得模糊，那很好。<br/>接下来，不需要再数了。<br/>让呼吸自己继续。<br/>慢慢地。<br/>轻轻地。<br/>一口呼吸之后，再一口呼吸。<br/>直到你不再需要听见我的声音。</td><td><ol><li seq="4">Soften the Tension｜渐进式肌肉放松 · 释放身体压力<p></p></li></ol><br/>有时候，身体还紧绷着，我们自己却已经没有注意到。<br/>现在，我们试着把这些力量一点一点还给夜晚。<br/>先轻轻握紧双手。<br/>不用很用力。<br/>感受手掌和手指里的紧张。<br/>保持一下。<br/>然后，松开。<br/>注意松开的那一刻。<br/>再轻轻抬起肩膀，让肩膀靠近耳朵。<br/>停一下。<br/>然后呼气。<br/>让肩膀落下来。<br/>很好。<br/>现在轻轻绷紧双腿。<br/>感受大腿和小腿里的力量。<br/>不用坚持。<br/>然后，全部松开。<br/>让双腿沉进床里。<br/>接下来，轻轻皱一下眉头。<br/>停一下。<br/>再把额头完全放松。<br/>你会发现，有时候我们并不需要“努力放松”。<br/>我们只需要先意识到自己在哪里用力。<br/>然后，允许那股力量离开。<br/>再检查一下身体。<br/>下巴有没有咬紧？<br/>肩膀有没有偷偷抬起来？<br/>手指是不是还抓着什么？<br/>如果有，就松开一点。<br/>不需要一次全部做到。<br/>每一次呼气，都松一点。<br/>每一次呼气，都少用一点力。<br/>现在，身体不需要保护你去面对任何事情。<br/>今晚的任务只有一个。<br/>躺下来。<br/>变得柔软。<br/>然后休息。</td><td><ol><li seq="5">You’re Safe Here｜慈心与安全感 · 孤独、焦虑、情绪低落<p></p></li></ol><br/>现在，你已经来到这里了。<br/>这一小段时间，不需要证明自己很好。<br/>也不需要表现得坚强。<br/>如果今天有一点难过，一点孤单，一点不安，都可以留在这里。<br/>你不需要马上把它们变好。<br/>先感觉一下身下的床。<br/>它正在托住你的身体。<br/>感觉被子覆盖在身上。<br/>感觉空气轻轻进入鼻尖，再慢慢离开。<br/>此刻，你就在这里。<br/>这一分钟，没有人要求你回答什么。<br/>没有事情需要马上完成。<br/>你可以安静地存在。<br/>如果脑海里还有声音在说：<br/>“我是不是做得不够好？”<br/>“明天怎么办？”<br/>“为什么我还是这么累？”<br/>不用和它争论。<br/>只是轻轻回答它：<br/>我听见了。<br/>但是现在，我们先休息。<br/>把一只手轻轻放在胸口，或者腹部。<br/>感受自己的温度。<br/>然后在心里对自己说：<br/>我可以慢一点。<br/>我可以不用现在想明白所有事情。<br/>我值得拥有这一晚的休息。<br/>这一刻，我在这里。<br/>这一刻，我是安全的。<br/>夜晚不要求你成为任何人。<br/>所以现在，闭上眼睛。<br/>让自己被床、被黑夜、被这一小段安静轻轻接住。<br/>今晚，你可以休息了。</td></tr><tr><td><b>语音版</b></td><td><grid><column width-ratio="0.500000"><p></p></column><column width-ratio="0.500000"><figure view-type="Preview"><source name="1. Release the Day｜放下今天 · 仪式感反刍 (2).mp3" mime="audio/mpeg" size="1766339" token="SwpSbKZcloloiOxSGt1cUeEYntd"/></figure></column></grid></td><td><figure view-type="Preview"><source name="2. Relax Your Body｜身体扫描 · 最通用的睡前冥想 (2).mp3" mime="audio/mpeg" size="1856618" token="WADKbYVumo21xOxiySPcSKO6nJg"/></figure></td><td><figure view-type="Preview"><source name="3. Breathe Into Sleep｜慢呼吸 · 快速安静下来.mp3" mime="audio/mpeg" size="1958600" token="AAaVbPlGao4q3CxQB0Rcf9gAnzg"/></figure></td><td><figure view-type="Preview"><source name="4. Soften the Tension｜渐进式肌肉放松 · 释放身体压力.mp3" mime="audio/mpeg" size="2016279" token="E5npbCojmoVzvCxoboTcrRjqngg"/></figure></td><td><figure view-type="Preview"><source name="5. You’re Safe Here｜慈心与安全感 · 孤独、焦虑、情绪低落.mp3" mime="audio/mpeg" size="1851185" token="IPNLbVWMPoKzPwxjjLpcz8e4nVe"/></figure></td></tr></tbody></table>

## 七、To to list for LinLin（截止19:00）

1. AI人格文档写入
2. 产品链路整合  
1）呼吸/白噪声/塔罗模块代码整合（见6.1 6.2 6.3）  
2）冥想/唤醒模块素材写入  
3）视频内容（生成中）占位预留
3. 工程文档备份
