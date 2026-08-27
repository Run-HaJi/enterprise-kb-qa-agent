"""本地中文向量服务：OpenAI 协议兼容 /v1/embeddings

用法：
    .venv/Scripts/python.exe scripts/embedding_server.py
端口 19000，模型 bge-small-zh-v1.5（fastembed + ONNX，首次启动自动下载）
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union
import uvicorn
from fastembed import TextEmbedding

MODEL_NAME = "BAAI/bge-small-zh-v1.5"

app = FastAPI(title="Local Embedding Server")
model = TextEmbedding(model_name=MODEL_NAME)
DIM = next(model.embed(["probe"])).shape[0]


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = MODEL_NAME


@app.get("/health")
def health():
    return {"status": "OK", "model": MODEL_NAME, "dim": DIM}


@app.post("/v1/embeddings")
def create_embeddings(req: EmbeddingRequest):
    texts = [req.input] if isinstance(req.input, str) else req.input
    vectors = list(model.embed(texts))
    return {
        "object": "list",
        "model": req.model,
        "data": [
            {"object": "embedding", "index": i, "embedding": vec.tolist()}
            for i, vec in enumerate(vectors)
        ],
        "usage": {"prompt_tokens": sum(len(t) for t in texts), "total_tokens": sum(len(t) for t in texts)},
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=19000)
