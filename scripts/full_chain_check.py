"""后端全链路复检脚本"""
import sys, requests, json, time

# Windows GBK 控制台无法输出 emoji，强制 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

B = "http://127.0.0.1:7860"
KB = "t_a3da1e42de03489b"
report = []

def step(name, ok, detail=""):
    report.append((name, ok, detail))
    print(f"{'✅' if ok else '❌'} {name} | {detail}")

# 1. 服务健康
h = requests.get(f"{B}/health", timeout=5).json()
step("后端健康", h.get("status") == "OK", str(h))
h2 = requests.get("http://127.0.0.1:19000/health", timeout=5).json()
step("Embedding服务", h2.get("status") == "OK", f"dim={h2.get('dim')}")

# 2. 登录
t = requests.post(f"{B}/api/v1/user/login", json={"user_name":"demo_user","user_password":"demo123456"}, timeout=8).json()
token = t["data"]["access_token"]
H = {"Authorization": f"Bearer {token}"}
step("JWT登录", t.get("status_code") == 200, "demo_user")

# 3. Agent列表
agents = requests.get(f"{B}/api/v1/agent", headers=H, timeout=8).json()["data"]
# 优先选绑定了知识库的 Agent
kb_agent = next((a for a in agents if a.get("knowledge_ids")), agents[0] if isinstance(agents, list) else None)
agent_id = kb_agent.get("id") if kb_agent else None
names = [a.get("name") for a in agents][:4] if isinstance(agents, list) else []
step("Agent列表", agent_id is not None, f"{len(agents)}个, 选中: {kb_agent.get("name") if kb_agent else None}")

# 4. 创建会话
d = requests.post(f"{B}/api/v1/dialog", headers=H, json={"name": "复检对话", "agent_id": agent_id, "agent_type": "text2dialog"}, timeout=8).json()
dialog_id = (d.get("data") or {}).get("dialog_id") if d.get("status_code") == 200 else None
step("创建会话", dialog_id is not None, f"dialog_id={str(dialog_id)[:16]}…")

# 5. 对话链路（SSE 真实流式 → DeepSeek）
if dialog_id:
    r = requests.post(f"{B}/api/v1/completion", headers={**H, "Content-Type": "application/json"},
                      json={"dialog_id": dialog_id, "user_input": "员工每月加班时间上限是多少？需要审批吗？"},
                      timeout=90, stream=True)
    chunks, started_at = [], time.time()
    first_tok = None
    for line in r.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            payload = line[5:].strip()
            if payload and payload != "[DONE]":
                try:
                    evt = json.loads(payload)
                    data = evt.get("data", {})
                    text = data.get("chunk") or data.get("message") or data.get("text") or ""
                    if text and not chunks:
                        first_tok = time.time()
                    if text:
                        chunks.append(text)
                except Exception:
                    pass
    full = "".join(chunks)
    tok_cost = f"首token {(first_tok - started_at):.1f}s" if first_tok else "首token 无输出"
    step("对话链路(DeepSeek流式)", len(full) > 5, f"{len(chunks)}个分片, {tok_cost}, 内容: {full[:60]}")
else:
    step("对话链路(DeepSeek流式)", False, "无dialog")

# 6. 混合检索（语义型）
r = requests.post(f"{B}/api/v1/knowledge/retrieval", headers=H, json={"query": "加班有什么规定", "knowledge_id": KB}, timeout=120)
c1 = r.json().get("data") or ""
step("混合检索-语义型", len(c1) > 50, f"{len(c1)}字符, 含'加班': {'加班' in c1}")

# 7. 混合检索（词面型——考勤新文档，验证BM25失效钩子）
r = requests.post(f"{B}/api/v1/knowledge/retrieval", headers=H, json={"query": "迟到 全勤奖 取消", "knowledge_id": KB}, timeout=120)
c2 = r.json().get("data") or ""
step("混合检索-词面型(新文档)", "考勤" in c2 or "迟到" in c2, f"{len(c2)}字符, 命中新文档: {'迟到' in c2}")

# 8. 静态文件读回（本地存储：现上传现读回）
import io as _io
up = requests.post(f"{B}/api/v1/upload", headers=H, files={"file": ("probe_kbqa_static.txt", _io.BytesIO("KBQA静态读回探针OK".encode("utf-8")), "text/plain")}, timeout=10)
probe_url = up.json()["data"]
f = requests.get(f"{B}{probe_url}", timeout=5)
step("本地存储静态读回", f.status_code == 200 and "探针OK" in f.text, f"{f.status_code}, {probe_url}")

print("\n===== 汇总 =====")
fails = [n for n, ok, _ in report if not ok]
print(f"通过 {sum(1 for _,ok,_ in report if ok)}/{len(report)}", "| 失败项:", fails if fails else "无")
