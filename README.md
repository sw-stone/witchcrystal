# MBTI 玄学水晶球 · AI 情绪解压搭子

## 项目简介

本项目是 **AI造物大赏第2期 · 任务1** 参赛作品：基于 Tuya T5AI-Core 开发板的 **AI 玄学类情绪解压搭子**。

一套「语音硬件 + 云端 AI Agent + 后端微服务 + 手机 App」结合的 MBTI 玄学情绪解压产品：

- **线下硬件（T5AI-Core 开发板）**：语音交互式"水晶球"——用户通过麦克风与「星语」（MBTI INFJ 玄学精灵）对话，体验塔罗牌占卜、星座运势、AI 解梦、今日运势和情绪陪伴。板载 LED 灯效随占卜结果变化，扬声器播报解读结果。
- **线上 App**：用户在 App 中查看占卜历史、情绪趋势图表、任务打卡、社区分享，以及与硬件绑定的电子宠物家园。
- **AI Agent**：基于涂鸦云 AI 的语音智能体（ASR→LLM→TTS 全链路），具备独特 INFJ 人设、长期记忆和成长能力。
- **后端微服务**：11 个 FastAPI 服务支撑全链路——用户、社交、宠物、日记、网关 + 人格引擎、小镇模拟、记忆库 + 占卜、情绪追踪、任务系统。
  - 多宠物间的自动社交模拟（类似 "AI Town/生成式智能体小镇"）；
  - 每日交互日记自动生成（养成系日常记录）。
  - 云端长期/超长程记忆：沉淀跨天对话、关系与小镇事件，后续用于推动宠物 MBTI 参数的多维成长和动态演化。
  - 三层 VLA / 快慢脑架构目标：端侧/近端小模型做亚秒级瞬时行为决策，云端慢脑做复杂推理与反思，超长程记忆层负责成长演化。
  - 风格化动作生成：少量动作库只作为基础动作原语，宠物会根据场景、情绪、关系和性格即时生成 5-10 秒动作序列，避免相同输入下机械重复反馈。
  - 家庭模拟器数据闭环：在真实入户数据不足时，模拟家庭空间、成员、猫狗和长程事件，生成可标注的主被动情感交互轨迹，用于训练端侧模型理解潜在意图与内部情绪。
- **线下加好友玩法**：两个挂件 NFC 碰一碰 → 双方手机 App 弹出好友申请 → 申请卡片上可预览对方宠物基本信息 + 用户名片 → 用户选择同意/拒绝。

## 目录结构

```
mbtiproject1/
├── README.md                 # 项目说明（本文件）
├── TASKTODO.md                # 详细任务拆解与开发计划
├── docs/
│   └── prd-divination-device.md # 玄学设备产品需求文档（Task 1 要求逐条映射）
├── hardware/                   # T5AI-Core 固件（TuyaOpen C 项目）
│   └── firmware/
│       ├── src/                 # C 源码：语音对话、LED 灯效、模式状态机、塔罗牌、星座
│       ├── include/             # 头文件 + AI Agent 人设 Prompt + 设备授权配置
│       ├── config/              # T5AI-Core 板级配置
│       ├── Kconfig              # 可配置项
│       └── assets/zh-CN/        # 中文语音提示文案
├── mobile-app/                # Flutter 客户端（NFC/WS/三大页面骨架已完成）
├── backend/                   # 后端微服务（FastAPI，端口 3000-3010）
│   ├── gateway/                # API 网关：HTTP 反代 + WS 透传，App 唯一入口
│   ├── user-service/           # 用户账号、个人名片、设备绑定
│   ├── social-service/         # 好友关系、NFC 碰一碰、WS 实时推送
│   ├── pet-profile-service/    # 电子宠物档案、MBTI 参数、养成值
│   ├── diary-service/          # 每日互动日记
│   ├── divination-service/     # ★玄学占卜：塔罗牌(78张)/星座运势/AI解梦/今日运势
│   ├── emotion-service/        # ★情绪追踪：情绪分析/长期趋势/PHQ-4心理评估
│   └── task-service/           # ★任务体系：每日签到/冥想打卡/积分/成就
├── agent-service/              # Agent 能力层（端口 3005-3007）
│   ├── personality-engine/     # MBTI 四维 -> 人格 Prompt / 对话 / 反思
│   ├── town-simulation/        # 多 Agent 自动社交模拟
│   └── memory-store/           # Agent 长期记忆
└── infra/                      # docker-compose（Postgres+Redis）+ 数据库 schema
```

## 技术选型建议（待评审）

- 移动端：Flutter（跨端 + 良好 NFC/BLE 插件生态）
- 后端：Node.js/TypeScript 或 Go 微服务 + gRPC/REST
- Agent 编排：LangGraph / 自研状态机 + LLM API（如 Claude API）
- 实时通信：WebSocket / MQTT（用于 NFC 触发的即时通知、宠物间实时互动）
- 数据库：PostgreSQL（关系数据）+ Redis（会话/在线状态）+ 向量库（Agent 记忆检索）
- 硬件通信：SIM 卡走蜂窝网络直连云端 MQTT/HTTP，NFC 仅做本地"碰一碰"身份交换触发

## 快速开始

```bash
# 1. 起基础设施（Postgres + Redis；不起也能跑，各服务自动降级内存存储）
docker compose -f infra/docker-compose.yml up -d

# 2. 起后端（各服务独立 venv，依赖见各自 requirements.txt）
cd backend && npm run dev:gateway   # 3000（App 统一入口）
npm run dev:user                    # 3001
npm run dev:social                  # 3002
npm run dev:pet                     # 3003
npm run dev:diary                   # 3004

# 3. 起 Agent 服务
cd agent-service/memory-store        && uvicorn app.main:app --port 3005
cd agent-service/personality-engine  && uvicorn app.main:app --port 3006
cd agent-service/town-simulation     && uvicorn app.main:app --port 3007

# 4. 起玄学设备后端服务（Task 1 新增）
cd backend/divination-service  && uvicorn app.main:app --port 3008
cd backend/emotion-service     && uvicorn app.main:app --port 3009
cd backend/task-service         && uvicorn app.main:app --port 3010
# 未配置 ANTHROPIC_API_KEY 时 LLM 自动降级为 Mock（零成本跑通全链路）

# 5. App（需 Flutter SDK）
cd mobile-app && flutter pub get && flutter run --dart-define=GATEWAY_URL=http://localhost:3000
```

### 固件编译（T5AI-Core 开发板）

```bash
# 1. 克隆 TuyaOpen SDK
git clone https://github.com/tuya/TuyaOpen.git && cd TuyaOpen && . ./export.sh

# 2. 将固件工程放入 SDK
cp -r /path/to/mbtiproject1/hardware/firmware apps/tuya.ai/mbti_divination

# 3. 填入设备授权码（include/tuya_config.h），配置 Tuya 云 AI Agent

# 4. 编译烧录
cd apps/tuya.ai/mbti_divination
tos.py config choice    # 选择 TUYA_T5AI_CORE.config
tos.py build && tos.py flash
```

各服务测试：进入服务目录 `pytest`（Postgres 集成测试需设 `TEST_DATABASE_URL`，未设自动跳过）。

## Task 1 (AI玄学情绪解压搭子) 要求覆盖

| 要求 | 状态 | 实现 |
|------|------|------|
| a. 玄学形式 (≥1种) | ✅ 4种 | 塔罗牌(78张完整韦特)/星座运势(12星座)/AI解梦/今日运势 |
| b. AI对话 | ✅ 优秀档 | 涂鸦云AI Agent「星语」INFJ人设 + personality-engine长期记忆 + 性格成长 |
| c. 语音交互 | ✅ 优秀档 | T5AI-Core mic→cloud ASR/LLM/TTS→speaker + LED灯效多模态 |
| d. 结果展示 | ✅ 优秀档 | LED随塔罗结果变色(紫/金/红/绿) + **花色专属灯效**(权杖脉动/圣杯呼吸/宝剑闪烁/星币稳光/大阿尔卡纳幻彩) + App牌面详情页(牌意+三维指引) + 音效 + 彩蛋(连续占卜解锁隐藏牌阵) |
| e. 云端连接 | ✅ 优秀档 | 涂鸦云IoT DP同步 + App查看历史 + 社区分享 |
| f. 情绪识别 | ✅ 优秀档 | emotion-service情绪分析 + 长期追踪 + PHQ-4心理健康评估 |
| g. 个性化 | ✅ 优秀档 | 用户信息+占卜历史 + AI根据情绪趋势主动推荐玄学形式 |
| h. 数据统计 | ✅ 优秀档 | 占卜统计 + 情绪趋势曲线 + 周报/月报 + 心理健康评分 |
| i. 任务体系 | ✅ 优秀档 | task-service: 每日签到/情绪记录/冥想打卡/积分等级/成就系统 |

### 差异化亮点

- **78张塔罗牌三维指引**：每张牌除关键词外，还提供爱情/事业/健康三维专属指引文案(玄学诗意风格)，App端点击任意牌即可查看完整牌意解读，云端LLM解读时注入全部牌意+三维指引上下文
- **硬件花色灯效**：T5AI-Core LED根据抽到的塔罗花色呈现不同光效模式——权杖(火)快速脉动、圣杯(水)柔和呼吸、宝剑(风)锐利闪烁、星币(土)沉稳常亮、大阿尔卡纳幻彩流转
- **Mock LLM零成本演示**：未配置API Key时，MockLlmClient会解析抽到的牌面信息(牌名+正逆位+关键词+牌意摘要)生成情境化占位解读，竞赛演示全程零成本跑通

## 文档索引

- 任务拆解与里程碑：见 `TASKTODO.md`
- 玄学设备产品需求文档：`docs/prd-divination-device.md`
- 固件编译说明：`hardware/firmware/README.md`
- 塔罗应用 v4 设计规范对齐：`docs/TAROT_V4_ALIGNMENT.md`
- 塔罗应用部署指南（含香港服务器 + Cloudflare 配置 + 踩坑记录）：`docs/DEPLOYMENT.md`

## Tarot Aura · 塔罗占卜 Web 应用

独立的塔罗占卜 Web 界面（Soft Lumina v4 柔光舒缓版），与硬件 / App 解耦，浏览器直接访问。

- **线上入口**：https://tarot.shitman666.top/tarot （Cloudflare 代理 → 香港服务器）
- **本地预览**：`docker compose up -d nginx gateway divination-service` → http://localhost:8080/tarot
- **设计规范**：4 屏流程（首页/牌阵/抽牌/解读）+ 液态玻璃 + 极光背景 + Bodoni Moda/Jost 字体
- **后端复用**：不新增 API，复用 `/divination/tarot/*` 现有接口（SSE 流式解读 + 单牌深度解读 + 78 张牌库）
- **牌阵**：single / three_card / celtic_cross / relationship（7 张关系牌阵，v4 新增）

详细对齐报告见 `docs/TAROT_V4_ALIGNMENT.md`，部署流程见 `docs/DEPLOYMENT.md`。
