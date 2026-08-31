# KBQA 项目开发规范

> 本规范由早期开发阶段（ZCode + GLM）沉淀，每一条都对应一次真实事故或返工。
> 它与当时的实现一起生长，**不保证每个字都对**：与代码事实冲突、或执行成本高于价值
> 的条款，允许按价值取舍，但在偏离时对用户说明（本项目曾据此放宽视觉存量清理条款）。

## 0. 验证纪律（最重要）

- **说"完成"之前必须跑验收**：后端改动跑 `scripts/full_chain_check.py`（9 环全链路）+ `pytest tests/`；前端改动跑 `npx vite build`；**视觉/UI 改动**额外用 Chrome 无头截图人工核验。
- 截图验收用 `scripts/shot/shot.js`（本机 Chrome 无头，完整单幅 1440×900）。**禁止**用 ZCode 内置浏览器的 screenshot 出图给用户——该浏览器会将截图平铺成 2×2 网格，部分内容被遮挡，导致模型视觉审核不到位。
- "在我机器上是好的"不算验证——改动后即使本地服务没起也要按第 6 节顺序拉起再验。

## 1. 数据操作

- **改/删任何 DB 行之前，先查引用关系**。事故案例：去重 llm 表时没查 agent 表的外键引用，造成悬空 llm_id，对话链路 500。
- 播种/初始化逻辑（init_data）必须**按名查重、幂等**，否则每次空态重启都会翻倍。
- 大批量数据修正优先写一次性脚本或 SQL 并保留记录，不做不可追溯的手工改动。

## 2. 敏感信息

- 密钥只进 `.env`（已被 .gitignore），配置文件里只放占位哨兵（如 `sk-local-placeholder`），由 settings 启动时注入。
- **每次 push 前全仓 grep 扫描**：`sk-[a-zA-Z0-9]{16,}`、`api_key: "非占位值"`、`password`、`secret`。接手第三方代码先做凭据审计（本项目曾从上游清出 3 处真实密钥）。
- 仓库要保持随时可转公开的状态。

## 3. Git 纪律

- **禁止裸用 `git add -A`**。先 `git status` 核对，警惕 `.venv`/`node_modules`/运行时数据被卷入（曾发生 2 万文件污染提交，靠 amend+强推才清干净）。
- `.gitignore` 新增目录模式后要验证不会误伤源码（`storage/` 曾误伤 `services/storage/`）。
- 推送判定用**命令真实退出码**（`if git push; then`），不要 `git push | tail`（管道吃掉退出码，假成功）。网络走 `HTTPS_PROXY=http://127.0.0.1:7897`，失败重试 3-5 次。
- 每个逻辑动作独立 commit，message 用 `type(scope): 描述` 格式，中文正文可。

## 4. 前端视觉规范（设计令牌体系）

- **颜色一律走 `src/style.css` 的 `--color-*` 令牌**，禁止在**新增/修改**的样式中硬编码彩色值（`#409eff`/`#67c23a`/`#f56c6c`/rgba 彩底/蓝紫渐变）。语义色（ok/warn/danger）已降饱和，用途仅限状态提示。
- 设计语言：近黑底 + 白字 + 灰阶层级 + 单一品牌蓝强调；**图标用线性 SVG 简笔或字母徽章（monogram），禁用 emoji 和卡通图**；状态用文字表达。
- 改色后做三轮扫描：`#hex 彩色`、`rgba(彩底)`、`linear-gradient(含浅色)`——三轮都有过漏网。
- 新增浅色/深色值前先查令牌表，没有合适的就加令牌，不要就地写值。
- **存量例外**：`agent.vue`/`tool.vue`/`model-editor.vue` 等管理页仍存在大量硬编码彩色与 emoji（如 `type.ts` 的 `KnowledgeFileStatus` 枚举），属已知债务。清理是独立工程量，**不得混入功能变更**，需另行立项（2026-08 已由作者确认此边界）。

## 5. 后端架构

- **外部客户端（LLM/搜索/存储）禁止在模块导入期实例化**——密钥缺失会崩启动。模式：构建时 try/except 降级 + 调用时友好报错。
- 所有外部依赖（LLM、Rerank、向量服务）调用失败必须**降级不阻断**主链路（参照 rerank 的降级实现）。
- 裁剪模块时按依赖图从叶子往主干删，每删一批重启验证一次；删除后全局 grep 残留 import。
- 引用了已删除模块的 import 是启动炸弹，删模块必须同步清聚合层（如 `tools/__init__.py`）。

## 6. 本地服务恢复顺序（机器重启后）

```text
Docker Desktop → 等引擎就绪 → agentchat-mysql/redis 自启
→ scripts/.venv python embedding_server.py   # :19000
→ src/backend/.venv uvicorn agentchat.main:app --port 7860   # cwd 必须在 src/backend
→ src/frontend npm run dev                    # :8090
→ python scripts/full_chain_check.py          # 验收 (Windows 下脚本已内置 UTF-8 输出修复)
```

常见坑：后端 cwd 错了配置加载不到（mysql endpoint 为 None）；开发模式需要 MySQL 容器 `-p 3306:3306` 端口映射（本机 3306 被占用时容器侧注释该映射、并改用其它可达地址）；`taskkill //IM python.exe` 会误杀 embedding 服务，按端口 PID 精准杀。

## 7. 测试

- 核心纯逻辑（融合算法/分词/排序/降级）必须有 pytest 用例；外部模型用 stub，不依赖网络和真实密钥。
- 当前基线：15 个用例。CI（GitHub Actions）会在每次 push 时自动跑。
