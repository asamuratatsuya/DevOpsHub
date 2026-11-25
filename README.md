# DevOpsHub

> 基于 Kubernetes 与 GitOps 的自动化交付管理平台 · 设计与实现

DevOpsHub 是一个前后端分离的 DevOps 自动化持续交付平台，目标是把「代码提交 → 镜像构建 → 镜像仓库 → GitOps 自动部署 → 集群资源管理 → 运行监控」整合为一条可观测、可复现、可回滚的完整闭环。平台自身即作为一个被托管的示例应用，完整运行在自己管理的 Kubernetes 集群上。

---

## ✨ 核心特性

- **自动化交付闭环**：推送代码后由 GitHub Actions 自动构建前后端镜像并推送 GHCR，再将新镜像标签回写到 Git 仓库内的 Kubernetes 部署清单；Argo CD 检测到清单变更后自动同步到集群完成滚动更新。
- **GitOps 单一事实来源**：所有部署状态以 Git 仓库 `k8s/` 目录为准，变更版本化、可审计、可回滚；Argo CD 开启自动同步与自修复（`automated + prune + selfHeal`）。
- **集群资源可视化管理**：在 Web 界面查看集群概览、节点、Pod、Deployment，支持查看 Pod 详情与日志、Deployment 扩缩容与重启（滚动重建）。
- **流水线视图**：集成 GitHub Actions 运行记录，交付过程可追溯。
- **监控集成**：基于 Prometheus 采集节点与集群指标，平台首页提供资源可视化并在受限集群上做了精细的节点调度规划。
- **真实接入、非演示**：后端通过 Kubernetes Python Client 以集群内 ServiceAccount 身份访问 API Server，业务数据持久化于 PostgreSQL，前后端与数据库全部容器化并由 GitOps 统一管理。

---

## 🧱 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3 · TypeScript · Element Plus（vue-pure-admin 模板）· Vite · Axios |
| 后端 | Python · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Kubernetes Python Client |
| 容器化 | Docker · Docker Compose（本地开发编排） |
| CI/CD | GitHub Actions · GHCR（容器镜像仓库） |
| 部署 | Kubernetes · Argo CD（GitOps） |
| 监控 | Prometheus · kube-state-metrics · node-exporter |

---

## 🔄 自动化交付链路

```
git push (main)
      │
      ▼
GitHub Actions ── 构建镜像 ──▶ 推送 GHCR
      │            (backend / frontend，tag: branch / sha-xxxxxxx / latest)
      ▼
回写镜像标签到 k8s/*.yaml ──▶ 自动 commit & push
      │
      ▼
Argo CD 检测到 Git 清单变更 ──▶ 同步到 Kubernetes ──▶ 滚动更新 / 回滚
      │
      ▼
Prometheus 采集运行指标 ──▶ 平台前端可视化
```

CI 回写 tag 所产生的 commit 本身即 Argo CD 的同步触发信号，无需额外 webhook。

---

## 🗂️ 功能模块与 API

后端统一挂载在 `/api/v1` 下：

| 模块 | 路由前缀 | 主要接口 |
| --- | --- | --- |
| 项目管理 | `/api/v1/projects` | 项目信息增删改查（与数据库真实联通） |
| 集群管理 | `/api/v1/cluster` | `overview`、`nodes`、`nodes/{name}`、`pods` |
| Pod 管理 | `/api/v1/pods` | 列表、`{ns}/{name}` 详情、`{ns}/{name}/logs` 日志 |
| 工作负载 | `/api/v1/deployments` | 列表、`{ns}/{name}` 详情、`scale`（扩缩容）、`restart`（重启） |
| 监控 | `/api/v1/monitoring` | `overview`（Prometheus 指标概览） |
| 流水线 | `/api/v1/pipelines` | `runs`（GitHub Actions 运行记录） |
| 健康检查 | `/api/v1/health` | 数据库探活（`SELECT 1`） |

前端对应提供：项目管理、集群管理、工作负载管理、流水线管理、总览 Dashboard（含资源图表与 Prometheus 入口）等页面。路由采用 `import.meta.glob` 模块化自动注册，新增页面即生效。

---

## 📁 项目结构

```
DevOpsHub/
├── backend/            FastAPI 服务
│   └── app/
│       ├── routers/    project / cluster / pods / deployments / monitoring / pipelines
│       ├── services/   Kubernetes 客户端封装（in-cluster 优先，kubeconfig 回落）
│       ├── models/     SQLAlchemy ORM（Project）
│       ├── schemas/    Pydantic 读写模型
│       └── db/         engine / session / 依赖注入
├── frontend/           Vue 3 管理端（nginx 镜像内置 API 反向代理）
│   └── src/
│       ├── api/        各模块接口封装
│       ├── router/     模块化自动注册
│       └── views/      project / cluster / deployment / pipeline / welcome
├── compose.yaml        本地开发：postgres + backend + frontend
├── k8s/                生产部署清单（GitOps 事实来源）
│   ├── backend-*.yaml  Deployment / Service / RBAC
│   ├── frontend-*.yaml Deployment / Service（NodePort 30080）
│   ├── postgres.yaml   StatefulSet + Service
│   ├── monitoring/     Prometheus Helm values
│   └── prometheus-*.yaml  监控命名空间与 Argo CD 应用
├── argocd/             DevOpsHub 自身的 Argo CD Application
└── .github/workflows/  docker-build.yml（构建 + 推送 + 回写 tag）
```

---

## 💻 本地开发

本地开发只需要 **Docker + Docker Compose**（以及做热重载时的 Python、pnpm）。Kubernetes、Argo CD、Prometheus 属于集群侧组件，**本地不运行**。

### 前置

- 项目根目录 `.env` 中设置 `POSTGRES_PASSWORD`（compose 与后端连接数据库依赖它）。
- 若采用"混合模式"本地裸跑后端，复制 `backend/.env.example` 为 `backend/.env` 并按需填写 `DATABASE_URL`（指向 `127.0.0.1:5432`）。

### 模式 A：全容器一键启动（最简单）

```bash
docker compose up -d          # postgres + backend + frontend 全部启动
docker compose down           # 停止（默认保留数据卷，切勿加 -v）
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:80 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### 模式 B：混合热重载（日常开发推荐）

数据库用容器，前后端在本地跑以便热重载：

```bash
# 1) 只起数据库
docker compose up -d postgres

# 2) 本地起后端（自动重载）
cd backend
uvicorn app.main:app --reload --port 8000

# 3) 本地起前端（另开终端）
cd frontend
pnpm install
pnpm dev          # 默认 http://localhost:8848，/api 由 Vite 代理到 127.0.0.1:8000
```

### 各组件的开启与关闭

| 组件 | 本地是否需要 | 开启 | 关闭 |
| --- | --- | --- | --- |
| PostgreSQL | 必需 | `docker compose up -d postgres` | `docker compose stop postgres` |
| 后端 FastAPI | 必需 | `docker compose up -d backend` 或本地 `uvicorn ... --reload` | `docker compose stop backend` |
| 前端 | 必需 | `docker compose up -d frontend` 或本地 `pnpm dev` | `docker compose stop frontend` |
| Kubernetes 集群 API | 本地无 | — | — |
| Argo CD | 仅集群 | 见「部署到集群」 | — |
| Prometheus | 仅集群 | 见「部署到集群」 | — |

> 说明：`cluster / pods / deployments / monitoring / pipelines` 这些接口依赖真实的 Kubernetes 集群、Prometheus 与 GitHub 凭据。本地没有这些后端时，相关接口会返回 `503`（服务不可用）或空数据，这是**预期行为**，不影响项目管理等基于数据库的功能开发与联调。前端在本地开发模式下通过 Vite 代理把 `/api` 转发到 `127.0.0.1:8000`；生产镜像则由内置 Nginx 完成 `/api/` 反向代理。

---

## ☸️ 部署到集群（GitOps 完整流程）

平台运行在 Kubernetes（k3s）集群上，由 Argo CD 统一管理。除 Argo CD 本体与若干一次性密钥外，**所有应用清单均由 Git 仓库经 Argo CD 自动部署**，不需要手动 `kubectl apply` 工作负载。

> 下方命令均在 **Linux 集群控制节点**、`kubectl` 已配置好集群上下文的前提下执行；`<尖括号>` 为占位符需自行替换。

### 1. 前置条件

- 一个可用的 Kubernetes 集群（本项目为 3 节点 k3s，每节点 2C/3G，含 `local-path` StorageClass）。
- 已安装 `kubectl` 并能访问集群。
- GitHub 账号与一个可拉取 GHCR 私有镜像的 PAT（用于 `ghcr-pull` 与流水线读取 Actions）。

### 2. 安装 Argo CD（一次性）

本环境使用 **Argo CD 官方 v2.14.18 的安装清单 `install.yaml`**（未经修改，非 Helm）部署。官方清单不包含 `argocd` 命名空间，需先创建再应用：

```bash
kubectl create namespace argocd
curl -sLO https://raw.githubusercontent.com/argoproj/argo-cd/v2.14.18/manifests/install.yaml
kubectl apply -n argocd -f install.yaml
```

确认安装与版本：

```bash
kubectl -n argocd get deploy
kubectl -n argocd get pods
```

访问 Argo CD UI（`argocd-server` 默认为 ClusterIP，端口 80/443 → 容器 8080），二选一：

```bash
# 方式一：临时端口转发，浏览器访问 https://localhost:8080（忽略自签证书告警）
kubectl -n argocd port-forward svc/argocd-server 8080:443

# 方式二：改为 NodePort 长期访问，再查看分配的端口
kubectl -n argocd patch svc argocd-server -p '{"spec":{"type":"NodePort"}}'
kubectl -n argocd get svc argocd-server
```

初始管理员口令（用户名为 `admin`）：

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

> 该 secret 在你首次登录并修改口令后会被自动删除；若已改口令则以实际为准。

### 3. 创建命名空间

```bash
kubectl create namespace devopshub
kubectl create namespace monitoring
```

（`argocd` 命名空间已在第 2 步创建。）

### 4. 创建镜像拉取密钥（GHCR）

```bash
kubectl -n devopshub create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username=<GH用户名> \
  --docker-password=<GH_PAT> \
  --docker-email=<邮箱>
```

### 5. 创建业务密钥

数据库口令（用户名/库名固定为 `devopshub`，后端 `DATABASE_URL` 会引用此口令）：

```bash
kubectl -n devopshub create secret generic devopshub-db \
  --from-literal=POSTGRES_PASSWORD=<数据库强密码>
```

流水线模块读取 GitHub Actions 运行记录所需的令牌：

```bash
kubectl -n devopshub create secret generic devopshub-github \
  --from-literal=GITHUB_TOKEN=<GH_PAT>
```

### 6. 注册 Argo CD Application

```bash
# 平台自身（前端 + 后端 + 数据库），监听 k8s/ 目录
kubectl apply -f argocd/devopshub-application.yaml

# 监控系统（Prometheus，独立 monitoring 命名空间，经 Helm OCI 仓库）
kubectl apply -f k8s/prometheus-repo.yaml
kubectl apply -f k8s/prometheus-application.yaml
```

Argo CD 配置了自动同步与自修复（`automated + prune + selfHeal`），注册后会自动拉取清单并部署。

### 7. 验证部署

```bash
kubectl -n devopshub  get pods,svc,deploy
kubectl -n monitoring get pods,svc
```

访问入口：

| 组件 | 地址 |
| --- | --- |
| 平台前端 | `http://<任意节点IP>:30080` |
| 后端 API | 集群内 `http://backend:8000`（前端 Nginx 反代 `/api/`） |
| Prometheus | `http://<任意节点IP>:30090` |

### 8. 日常更新（无需手动操作）

代码推送到 `main` 后：GitHub Actions 自动构建前后端镜像并推送 GHCR → 将新的 `sha-xxxxxxx` 镜像标签回写到 `k8s/` 清单并自动提交 → Argo CD 检测到 Git 变更自动同步 → 集群滚动更新。**整个过程无需人工 `kubectl apply`**；如需回滚，回退 Git 清单提交即可由 Argo CD 同步还原。

服务与权限要点：后端通过 `ServiceAccount devopshub-backend` + RBAC 以最小权限访问集群 API（节点/Pod/Deployment 读取，工作负载扩缩容/重启等写操作单独授权），镜像标签由 CI 维护，集群期望状态始终以 Git 仓库为唯一事实来源。

---

## 📊 监控与资源调度

监控系统基于精简的 Prometheus 部署：

- 关闭非必需的 Alertmanager、PushGateway，仅启用 **kube-state-metrics** 与 **node-exporter** 采集集群与主机指标；
- 指标保留策略 `retention 7d / 4GB`，持久卷 `5Gi`（`local-path`）；
- Prometheus 服务通过 NodePort `30090` 对外暴露，平台首页提供图表展示与跳转入口。

**节点调度规划**：集群由三台 2 核 / 3GB 内存的虚拟机构成，整体资源有限。为避免监控组件与平台自身争抢资源，Prometheus server 与 kube-state-metrics 通过 `nodeSelector: kubernetes.io/hostname: node2` **显式调度到 node2**——master 节点已承担平台核心负载与系统组件，资源余量不足，因此将较占用内存的监控组件集中固定到 node2，并为其设置明确的 requests/limits；node-exporter 则以 DaemonSet 形式覆盖全部节点（含带污点节点）。这是在资源受限环境下保证集群稳定运行的刻意设计。

---

## 🧪 运行环境

| 项 | 说明 |
| --- | --- |
| 集群 | 3 × 虚拟机（2 vCPU / 3GB 内存），Kubernetes（k3s） |
| 存储 | `local-path` StorageClass |
| 镜像仓库 | GHCR（`ghcr.io/asamuratatsuya/devopshub-{backend,frontend}`） |

---

## 📝 关于

本项目为本科毕业设计作品，采用开源技术栈搭建，贯通 CI/CD、GitOps、集群管理与可观测性的完整交付链路。
