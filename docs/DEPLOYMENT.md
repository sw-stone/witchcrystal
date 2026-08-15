# 塔罗应用部署指南

Tarot Aura Web 应用（`tarot.html`）的部署流程与踩坑记录。
设计规范对齐见 `docs/TAROT_V4_ALIGNMENT.md`。

---

## 一、访问入口

| 域名 | 状态 | 路径 |
|------|------|------|
| `https://tarot.shitman666.top/tarot` | ✅ 已上线 | Cloudflare 代理 → 香港服务器 154.64.255.205:80 → nginx → gateway |
| `https://tarot.sh.cn/tarot` | ⏳ 待 NS 生效 | NS 迁移到 CF 后启用（见下文"tarot.sh.cn 接入"） |
| `http://localhost:8080/tarot` | 本地开发 | docker compose 起本地 nginx + gateway |

---

## 二、架构

```
浏览器
  ↓ HTTPS
Cloudflare 边缘（SSL 终止 + CDN 代理）
  ↓ HTTP（A 记录指向源站 IP）
香港服务器 154.64.255.205:80
  ↓ docker-proxy
nginx 容器（mbti-nginx，透传所有路径）
  ↓ proxy_pass http://gateway:8000
gateway 容器（mbti-gateway-1）
  ├─ @app.get("/tarot") → 返回 tarot.html（显式路由）
  ├─ /divination/tarot/cards        → 代理到 divination-service
  ├─ /divination/tarot/interpret-stream (SSE) → 代理到 divination-service
  └─ /divination/tarot/card-reading → 代理到 divination-service
```

**关键**：`tarot.shitman666.top` 走的是 **CF 代理 + 源站 A 记录**（和 `mbti.shitman666.top` 同路径），**不是** Cloudflare Tunnel。Tunnel 方案因 Dashboard 添加 Public Hostname 失败而弃用（见"踩坑记录"）。

---

## 三、香港服务器部署流程

服务器：`154.64.255.205`（RainYun 香港，root SSH 免密已配）
项目目录：`/opt/mbti/`

### 3.1 同步代码改动到服务器

```bash
# 从本地同步改动的文件
cd /Users/lf/Desktop/mbtiproject1

# gateway 改动（/tarot 路由 + 公开路径 + tarot.html）
scp backend/gateway/app/main.py \
    backend/gateway/app/auth_jwt.py \
    root@154.64.255.205:/opt/mbti/backend/gateway/app/
scp backend/gateway/app/static/tarot.html \
    root@154.64.255.205:/opt/mbti/backend/gateway/app/static/

# divination-service 改动（relationship 牌阵 + 白名单修复）
scp backend/divination-service/app/core/tarot_data.py \
    root@154.64.255.205:/opt/mbti/backend/divination-service/app/core/
scp backend/divination-service/app/router.py \
    root@154.64.255.205:/opt/mbti/backend/divination-service/app/
```

### 3.2 重建镜像 + 重启

```bash
ssh root@154.64.255.205
cd /opt/mbti

# 重建 gateway 和 divination-service 镜像
docker compose build gateway divination-service

# 重启
docker compose up -d gateway divination-service

# ⚠️ 重要：重启 nginx 清掉旧 upstream 连接缓存
# （否则 nginx 会连旧 gateway 容器，返回 404）
docker restart mbti-nginx
```

### 3.3 只改 tarot.html 的快速更新（不重建镜像）

gateway 容器不挂载 static 目录（构建时 COPY 进镜像），改 `tarot.html` 后：

```bash
ssh root@154.64.255.205
# docker cp 进容器 + 重启
docker cp /opt/mbti/backend/gateway/app/static/tarot.html \
    mbti-gateway-1:/app/app/static/tarot.html
docker restart mbti-gateway-1
```

### 3.4 验证

```bash
# 服务器本地
curl -s -o /dev/null -w "%{http_code}" http://localhost/tarot   # 期望 200

# 公网
curl -sk -o /dev/null -w "%{http_code}" https://tarot.shitman666.top/tarot  # 期望 200

# SSE 流式解读
curl -sk -X POST https://tarot.shitman666.top/divination/tarot/interpret-stream \
  -H "Content-Type: application/json" \
  -d '{"userId":"_test","spread":"single","cards":[{"name_en":"The Star","name_cn":"星星","reversed":false,"position":"今日指引"}]}' \
  --max-time 20 | head -4   # 期望 event: cards + event: delta
```

---

## 四、Cloudflare DNS 配置

### 4.1 tarot.shitman666.top（已生效）

CF Dashboard → DNS → `shitman666.top` zone：

| 类型 | 名称 | 内容 | 代理 |
|------|------|------|------|
| A | `tarot` | `154.64.255.205` | ✅ 已代理（橙云） |

或用 API：
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/<zone_id>/dns_records" \
  -H "Authorization: Bearer <CF_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"tarot","content":"154.64.255.205","proxied":true,"ttl":1}'
```

### 4.2 tarot.sh.cn（待 NS 生效）

`tarot.sh.cn` 注册商是阿里云，原 NS 是 `dns17/18.hichina.com`。已在阿里云域名管理把 NS 改为 Cloudflare 分配的：
- `drew.ns.cloudflare.com`
- `julissa.ns.cloudflare.com`

NS 传播需 1-2 小时（中国域名可能更久）。CF 主面板 `tarot.sh.cn` 卡片变绿（Active）后：
1. 在 CF DNS 里加 A 记录 `tarot.sh.cn` → `154.64.255.205`（proxied）
2. nginx.conf 已支持 `server_name tarot.sh.cn`（无需改）
3. 访问 `https://tarot.sh.cn/tarot`

> 注意：CF Free 套餐**不支持 CNAME 接入**（只有 Business+ 支持 partial setup）。`tarot.sh.cn` 必须走完全 NS 迁移。

---

## 五、踩坑记录

### 5.1 Cloudflare Tunnel 方案失败（已弃用）

**尝试**：用 Cloudflare Tunnel（cloudflared 容器）暴露本地 Docker 服务。

**失败点**：
1. **Dashboard 加 Public Hostname 一直失败** —— "Failed to add published application"，无详细错误。新版 CF UI 对 token 模式隧道的 Public Hostname 添加有隐藏限制或 bug。
2. **CLI `cloudflared tunnel route dns` 只创 DNS 不配 ingress** —— DNS 指向隧道了，但隧道不知道转发到哪（HTTP 530 error 1033）。
3. **token 模式下本地 `config.yml` 不生效** —— token 模式 ingress 完全由 Dashboard 远程下发，加 `--config` 参数会导致 TLS handshake 失败连不上 CF 边缘。
4. **credentials 模式 QUIC 连不上** —— 国内网络 UDP 7844 被封，credentials 模式不支持 `--protocol http2`，TLS handshake EOF。

**结论**：放弃 Tunnel 方案，改用 **CF 代理 + 源站 A 记录**（和现有 `mbti.shitman666.top` 同路径），直接走香港服务器 80 端口。

### 5.2 macOS Docker 单文件挂载 deadlock

**问题**：`docker-compose.yml` 里 `volumes: - ./infra/nginx.conf:/etc/nginx/conf.d/default.conf:ro` 导致 nginx 启动报 `pread() failed (Resource deadlock would occur)`。

**原因**：Docker Desktop for macOS 挂载单文件有已知 bug，挂载目录才行。

**修复**：把 nginx.conf 放到独立目录，挂载目录：
```yaml
volumes:
  - ./infra/nginx-conf:/etc/nginx/conf.d:ro
```
（香港服务器 nginx 镜像内已有配置，不需要挂载，此问题仅影响本地开发）

### 5.3 gateway 镜像缺 python-multipart

**问题**：重建 gateway 镜像后启动报 `RuntimeError: Form data requires "python-multipart"`。

**原因**：`voice.py` 用了 `Form`，依赖 `python-multipart`，但旧镜像没装。

**修复**：`requirements.txt` 已含 `python-multipart>=0.0.9`，用 `docker compose build gateway`（走 Dockerfile.service）会正确安装。`docker commit` 方式构建时需手动 `pip install`。

### 5.4 nginx 缓存旧 upstream

**问题**：重建 gateway 镜像后，`/tarot` 经 nginx 仍返回 404，但容器内直测 `gateway:8000/tarot` 是 200。

**原因**：nginx 保持到旧 gateway 容器的 upstream 连接，没感知到新容器。

**修复**：`docker restart mbti-nginx` 清掉连接缓存。

### 5.5 卡牌图像镜像（用户反馈"倒置"）

**问题**：所有正位牌图像左右镜像。

**根因**：`.front` 用 `background-image` + `transform:rotateY(180deg)`，3D 翻转会让 2D 贴图水平镜像。

**修复**：改用 `<img>` 标签，让图片内容随 3D 翻转一起转动。详见 `docs/TAROT_V4_ALIGNMENT.md` 第六节。

### 5.6 误建 DNS 记录

`cloudflared tunnel route dns mbti tarot.sh.cn` 在 `shitman666.top` zone 下误建了 `tarot.sh.cn.shitman666.top`（CF 把 `tarot.sh.cn` 当成 `shitman666.top` 的子域）。无害但脏，可在 CF Dashboard → `shitman666.top` → DNS 删除。

---

## 六、本地开发

```bash
cd /Users/lf/Desktop/mbtiproject1

# 起核心服务
docker compose up -d nginx gateway divination-service

# 本地访问
open http://localhost:8080/tarot

# 改 tarot.html 后快速更新（不重建镜像）
docker cp backend/gateway/app/static/tarot.html \
    mbtiproject1-gateway-1:/app/app/static/tarot.html
# FastAPI 的 FileResponse 每次请求都读文件，无需重启
```

### 本地改后端代码（gateway / divination-service）

本地 Docker 用 `docker commit` 方式重建镜像（比 `docker compose build` 快）：

```bash
# gateway
CID=$(docker run -d --name gw-build --entrypoint "" \
  -v "$PWD/backend/gateway/app:/app/app" \
  -v "$PWD/backend/gateway/requirements.txt:/app/requirements.txt:ro" \
  mbti/svc:gateway sleep 3600)
docker exec gw-build pip install --no-cache-dir -r /app/requirements.txt
docker commit --change='ENTRYPOINT []' \
  --change='CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]' \
  gw-build mbti/svc:gateway
docker rm -f gw-build
docker compose up -d gateway
```

> 注意：`docker commit --change='ENTRYPOINT []'` 在某些 Docker 版本不生效（ENTRYPOINT 仍为 `["sleep"]`）。可靠方式是用 Dockerfile 重建，或用 `--entrypoint ""` 启动临时容器。

---

## 七、文件清单

本次 v4 对齐 + 部署涉及的改动文件：

| 文件 | 改动 |
|------|------|
| `backend/gateway/app/static/tarot.html` | **新增** Soft Lumina 4 屏塔罗 Web 应用 |
| `backend/gateway/app/main.py` | 加 `/tarot` 路由（`@app.get("/tarot")`） |
| `backend/gateway/app/auth_jwt.py` | PUBLIC_PATHS 加 `/tarot` `/crystal` `/divination/history` |
| `backend/divination-service/app/core/tarot_data.py` | 加 `relationship` 7 张牌阵 |
| `backend/divination-service/app/router.py` | 修复牌阵白名单（原 `five_card` 不存在） |
| `infra/nginx.conf` | 加 `server_name tarot.sh.cn tarot.shitman666.top` 的 server 块 |
| `infra/nginx-conf/default.conf` | 本地开发用（避免单文件挂载 deadlock） |
| `infra/cloudflared-config.yml` | Tunnel credentials 模式配置（已弃用，保留备查） |
| `infra/cloudflared.yml` | 加注释说明 token 模式下不生效 |
| `docker-compose.yml` | nginx 挂载 nginx-conf 目录；cloudflared 改回 token 模式 |
| `docs/TAROT_V4_ALIGNMENT.md` | 设计规范对齐报告 |
| `docs/DEPLOYMENT.md` | 本文件 |
