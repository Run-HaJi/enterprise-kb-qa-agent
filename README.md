# KBQA · 企业知识库智能问答 Agent 平台

基于 **FastAPI + LangChain/LangGraph + ChromaDB + Vue 3** 的多 Agent 知识库问答系统：
文档上传 → 解析分块 → 本地向量化 → 检索重排 → 流式回答，答案附带来源引用。

> 本项目基于 MIT 协议的开源框架 AgentChat 深度二次开发：
> 裁剪聚焦核心链路（路由 22→13 组，代码量约 -46%）、向量库统一为 ChromaDB、
> 对象存储替换为本地磁盘 + 静态目录、修复多处启动期缺陷、前端以 Tailwind CSS
> 重构为深色工作台风格。

## 功能

- **知识库 RAG**：PDF/DOCX/TXT/MD 上传，解析分块 → bge-small-zh 向量化 → 检索 → 重排（无外部 Rerank 服务时自动降级）→ 带引用回答
- **多 Agent 会话**：Agent 配置（模型/工具/知识库绑定）、SSE 流式输出、会话历史持久化
- **插件工具**：论文检索、PDF/DOCX 互转等本地工具，支持 OpenAPI 自定义工具注册
- **三层记忆**：短期上下文 / 历史总结 / 长期偏好
- **账号体系**：注册登录、JWT 鉴权

## 架构

```text
Vue 3 + Element Plus + Tailwind CSS（:8090，/api 代理）
  └─ FastAPI（:7860）
       ├─ api/v1        REST 路由
       ├─ api/services  业务服务（Agent / RAG / LLM / Memory）
       ├─ core/agents   LangGraph ReAct 主链路
       ├─ services/rag  解析 → 分块 → 向量化 → 检索 → 重排
       ├─ services/mcp  ...
       ├─ ChromaDB（./vector_db 持久化）
       ├─ MySQL（SQLModel）+ Redis
       └─ 本地磁盘存储（/api/files 静态目录）
本地 Embedding 服务（:19000，fastembed + bge-small-zh-v1.5）
```

## 快速开始

```bash
# 1. 基础设施（MySQL/Redis）
cd docker && docker compose up -d mysql redis

# 2. 后端（Python 3.12）
cd src/backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
cp agentchat/config.yaml agentchat/.env   # 按需填写 DEEPSEEK_API_KEY
.venv/Scripts/python -m uvicorn agentchat.main:app --port 7860

# 3. 本地向量服务
cd scripts
python -m venv .venv && .venv/Scripts/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi "uvicorn[standard]" fastembed
.venv/Scripts/python embedding_server.py   # :19000

# 4. 前端
cd src/frontend
npm install && npm run dev                 # :8090
```

默认账号：`demo_user / demo123456`（首次启动自动初始化）

## 关键配置

密钥一律通过环境变量注入（不写入配置文件）：在 `src/backend/.env` 中设置
`DEEPSEEK_API_KEY=sk-...`，启动时自动填充对话 / 工具调用 / 推理模型。
`config.yaml` 中的 `sk-local-placeholder` 仅为占位哨兵。

## License

MIT（沿袭上游 AgentChat）
