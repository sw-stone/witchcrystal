# 塔罗界面 v4 规范对齐报告

将 `mbtiproject1` 现有塔罗界面与两份 v4 设计规范进行比对与对齐：
- 样机：`塔罗应用界面样机与组件规范_v4.html`（4 屏 Soft Lumina 流程）
- 令牌：`塔罗应用设计令牌_v4_柔光舒缓版.html`（配色/字体/质感/动效/形状）

部署域名：**tarot.sh.cn**

---

## 一、比对结论（改造前 → 改造后）

| 维度 | 规范 v4 要求 | 原有 `console.html` | 对齐后 `tarot.html` |
|------|------------|-------------------|-------------------|
| 主题 | 深暮紫 twilight `#241F36` 暗色 | 浅紫 `#f4f1fa` 亮色 ❌ | 暗色 twilight ✅ |
| 字体 | Bodoni Moda(标题斜体) + Jost(正文) | 系统无衬线 ❌ | Google Fonts 引入 ✅ |
| 质感 | 液态玻璃 backdrop-blur(20px)+5%白 | 实色卡片 ❌ | 液态玻璃 ✅ |
| 氛围 | 极光 3 层径向渐变 blur(22px) | 无 ❌ | 3 层 aurora blob ✅ |
| 装饰 | 光粒子/月相环/柔光分隔线/星线 | 无 ❌ | 粒子+月相光球+glow-div ✅ |
| 动效 | 呼吸 4s / 飘移 8-12s / 翻牌 600ms expo | 部分翻牌 | 三种动效令牌全实现 ✅ |
| 屏1 首页 | 月相光球+今日牌(玻璃卡)+关键词标签+底栏 | 无独立首页 ❌ | 完整实现 ✅ |
| 屏2 牌阵 | 4 种牌阵卡(选中态)+Begin Reading | 3 种 ❌ | 4 种(补 Relationship) ✅ |
| 屏3 抽牌 | 扇形牌背+进度点+提示文案 | 78 张网格平铺 ❌ | 扇形牌背 fan ✅ |
| 屏4 解读 | 牌阵布局(正/逆位+位置标签)+解读卡+关键词+展开 | 有解读但样式不符 | 完整实现 ✅ |
| 底栏 | Today / Spread / Diary | 自定义底栏 | 三项 ✅ |
| 牌阵数 | 4 种(single/three/celtic/relationship) | 3 种(无 relationship) | 4 种 ✅ |
| 圆角 | 卡24/钮20/标签12 | 混乱 | 严格遵循 ✅ |

---

## 二、后端改动

### 1. 新增 Relationship（关系牌阵）7 张
`backend/divination-service/app/core/tarot_data.py:927`
```python
SPREAD_SIZES["relationship"] = 7
SPREAD_POSITIONS["relationship"] = [
    "你自己", "对方", "关系现状", "你的期待", "对方的期待", "潜在影响", "最终指引"
]
```

### 2. 修复允许的牌阵白名单
`backend/divination-service/app/router.py:165` —— 原代码只允许 `single/three_card/five_card`（`five_card` 根本不存在于 SPREAD_SIZES，是个 bug）。修正为：
```python
spread = dto.spread if dto.spread in (
    "single", "three_card", "celtic_cross", "relationship", "destiny_cross", "five_card"
) else "three_card"
```

### 3. 网关路由 + 公开路径
`backend/gateway/app/main.py` —— 新增 `/tarot` 路由（与 `/crystal` 同构，显式 GET 绕过鉴权）：
```python
@app.get("/tarot")
async def tarot_aura_page():
    return FileResponse(_TAROT_HTML, media_type="text/html")
```
`backend/gateway/app/auth_jwt.py:34` —— 将 `/divination/history` 加入 PUBLIC_PATHS，使塔罗 Web 应用在无登录态下也能保存/查看占卜日记（按客户端生成的匿名 UID 隔离）。

---

## 三、前端改动：`tarot.html`（Soft Lumina 4 屏流程）

**文件**：`backend/gateway/app/static/tarot.html`（单文件 SPA，复用 `/static/tarot/*.webp` 78 张牌图）

### 设计令牌落地（对应《设计令牌 v4》逐条）

| 令牌组 | 规范值 | 实现 |
|-------|-------|------|
| **01 配色** Twilight `#241F36` / Lavender `#B8A4E0` / Mist `#8B9FD1` / Rose `#E8B4A8` / Moon `#DBC8A0` / Sage `#9BCBB0` / Pearl `#DDD4C8` | 7 色 | `:root` CSS 变量全量定义 ✅ |
| **液态玻璃** backdrop-blur(20px) · bg 5%白 · border 0.5px rgba(255,255,255,0.12) · shadow 0 8px 32px rgba(0,0,0,0.12) | 4 参数 | `.glass` 类 ✅ |
| **柔光氛围** 3 层径向 opacity 0.06-0.14 · blur(22px) · screen blend | 3 层 | `.aurora .b1/b2/b3` ✅ |
| **02 字体** Bodoni Moda(400/500 italic) + Jost(300/400/500) | 2 族 | Google Fonts ✅ |
| **03 质感** 液态玻璃 / 柔光球体(3层径向) / 呼吸 / 极光流动 | 4 种 | 全实现 ✅ |
| **04 装饰** 星线 / 月相环 / 光粒子 / 柔光分隔线 | 4 种 | 粒子+月相光球+glow-div ✅ |
| **05 动效** 呼吸(scale 0.96↔1.04 4s) / 飘移(±8px 8-12s) / 翻牌(rotateY 180° 600ms expo 80ms stagger) | 3 种 | `@keyframes breath/drift1-3` + `.flip` transition ✅ |
| **06 形状** 卡 24px / 钮 20px / 标签 12px / 间距 24·32·48·80 | — | `--r-card/btn/tag` ✅ |
| **投影** 0 8px 32px rgba(0,0,0,0.10) | — | `--glass-shadow` ✅ |
| **触控** 44pt min | — | 钮/卡均≥44px ✅ |

### 4 屏流程（对应《样机 v4》逐屏）

**屏1 · Home / Daily Draw**
- 月相光球（halo + core，breathing 4s 动画）
- 日期行（Friday · Aug 14 格式）
- 今日牌玻璃卡（抽象图标 + 牌名 Bodoni 斜体 + 罗马数字 + 关键词 + "tap to reveal ↗"）
- 关键词标签（lav/rose/moon 三色）
- 底栏 Today/Spread/Diary
- 今日牌按日期确定性抽取（同一天稳定不变），点按进入单牌解读

**屏2 · Spread Selection**
- 4 张牌阵玻璃卡：Single Card(1·30s) / Three Card(3·2min) / Celtic Cross(10·5min) / Relationship(7·3min)
- 选中态：薰衣草渐变背景 + 勾选圆点（对应样机选中指示）
- 问题输入 + 心境 chips
- "Begin Reading" 薰衣草→雾蓝渐变按钮

**屏3 · Drawing Cards**
- 扇形牌背（9 张扇形展开 -26°~+26°，对应样机 fan 布局）
- 中心引导光（pulse + ring breathing 动画）+ "感受它的能量"
- 进度点（Draw 1 of 3 + dots）
- 轻触抽牌，抽中卡片飞出消失，集齐自动进入解读

**屏4 · Reading & Interpretation**
- 牌阵布局：位置标签(Past/Present/Future…) + 牌名 + 正/逆位标识
- 翻牌动画：rotateY 180° 600ms expo，80ms stagger
- 逆位牌 rotateZ(180°) 翻转
- 解读卡：左侧极光竖条 + 牌名 + 关键词 chips + SSE 流式解读（光标闪烁）
- "展开单牌深度解读 ↓" → 每张牌调用 `/divination/tarot/card-reading` 逐张深度解读

### API 接线（复用现有后端，零新增接口）

| 功能 | 端点 | 说明 |
|------|------|------|
| 牌库+关键词 | `GET /divination/tarot/cards` | 今日牌关键词富化 |
| 流式整体解读 | `POST /divination/tarot/interpret-stream` | SSE，客户端传 picked cards |
| 单牌深度解读 | `POST /divination/tarot/card-reading` | 每张牌独立解读 |
| 保存历史 | `POST /divination/history` | best-effort |
| 占卜日记 | `GET /divination/history/{uid}` | Diary 屏 |

---

## 四、部署配置（tarot.sh.cn）

### Cloudflare Tunnel
`infra/cloudflared.yml` —— 新增 hostname 路由：
```yaml
- hostname: tarot.sh.cn
  service: http://nginx:80
```
> 需在 Cloudflare Dashboard 为隧道 `19c0df1a-...` 添加 `tarot.sh.cn` → tunnel 的 Public Hostname 记录（或将其 CNAME 指向 `*.cfargotunnel.com`）。

### Nginx
`infra/nginx.conf` —— 新增 `server` 块 `server_name tarot.sh.cn`：
- `location = /` → 代理到 `gateway/tarot`（根域名直接出塔罗应用）
- 复用 SSE `/divination/tarot/interpret-stream`（buffering off）+ WS 透传 + 限流规则

### Docker Compose
`docker-compose.yml` —— nginx 服务新增卷挂载，使 `nginx.conf` 改动无需重建镜像即生效：
```yaml
volumes:
  - ./infra/nginx.conf:/etc/nginx/conf.d/default.conf:ro
```

### 启动（本地）
```bash
cd /path/to/mbtiproject1
docker compose up -d nginx gateway divination-service
# 本地访问 http://localhost:8080/tarot
```

> 公网部署见 `docs/DEPLOYMENT.md`。当前线上入口为 `https://tarot.shitman666.top/tarot`（经香港服务器 + Cloudflare 代理）；`tarot.sh.cn` 待 NS 迁移 CF 完成后启用。

---

## 五、验证

- `tarot.html` JS 语法：`node --check` ✅
- 33 个 HTML id 全部被 JS 正确引用 ✅
- 25/25 设计令牌检查通过 ✅
- divination-service 70 个单元测试全绿 ✅
- 5 屏 + 3 底栏项 + 4 牌阵结构完整 ✅
- 公网端到端：`/tarot` 200 / `/health` 200 / `/divination/tarot/cards` 200 / SSE `interpret-stream` 返回 `event: cards` + `event: delta` ✅

---

## 六、卡牌图像镜像修复（2026-08-15）

### 问题
正位牌图像显示为左右镜像（用户反馈"所有卡牌图像都是倒置的"）。

### 根因
原实现用 `background-image` + `transform:rotateY(180deg)`：
- `rotateY(180deg)` 是绕 Y 轴的 3D 翻转，会让贴在元素表面的 `background-image` **水平镜像**
- 配合父级 `.flip.revealed` 的 `rotateY(180deg)` 在 3D 空间朝向虽正确，但 2D 贴图本身被镜像

### 修复
改用 `<img>` 标签（与 `console.html` 一致），让图片内容随 3D 翻转一起转动：

```css
/* 修复前（background-image 会镜像） */
.read-card .front{transform:rotateY(180deg);background-size:cover;background-position:center}
.read-card.reversed .front{transform:rotateY(180deg) rotateZ(180deg)}

/* 修复后（img 标签跟随 3D 翻转） */
.read-card .front{transform:rotateY(180deg);overflow:hidden}
.read-card .front img{width:100%;height:100%;object-fit:cover;display:block}
.read-card.reversed .front img{transform:rotateZ(180deg)}
```

```html
<!-- 修复前 -->
<div class="face front" style="background-image:url('${img}')"></div>
<!-- 修复后 -->
<div class="face front"><img src="${img}" alt="${card.name}"></div>
```

同步修复了 `fan-card .front`（屏3抽牌）和 `.per-card .pc-head .mini`（单牌解读小图）。

### 部署注意
gateway 容器不挂载 static 目录（构建时 COPY 进镜像），改 `tarot.html` 后需：
```bash
# 方式1：docker cp 进运行中的容器 + 重启
docker cp backend/gateway/app/static/tarot.html mbti-gateway-1:/app/app/static/tarot.html
docker restart mbti-gateway-1

# 方式2：重建镜像（更彻底）
docker compose build gateway && docker compose up -d gateway
```
