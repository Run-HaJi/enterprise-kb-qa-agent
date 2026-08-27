"""BM25 关键词召回索引

语料直接取自 Chroma 集合内该知识库的全部原文条目（跳过摘要条目），
构建 BM25Okapi 索引后常驻内存；文档写入/删除时由调用方失效对应缓存，
下次查询懒加载重建。向量召回负责语义相似，本模块补齐精确词面匹配
（型号、编号、专有名词等向量检索的弱项），两路结果在 retrieval 层做 RRF 融合。
"""
import threading
from typing import Dict, List

import jieba
from loguru import logger
from rank_bm25 import BM25Okapi

from agentchat.schemas.search import SearchModel
from agentchat.services.rag.vector_stores import vector_client


def tokenize(text: str) -> List[str]:
    """中文分词 + 小写归一，过滤空白与单字符噪声"""
    return [t for t in jieba.lcut((text or "").lower()) if t.strip()]


class KeywordIndexManager:
    """按知识库维度的 BM25 索引缓存与查询"""

    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def _build(self, knowledge_id: str) -> dict:
        collection = vector_client._get_collection_safe(knowledge_id)
        if collection is None:
            return {"empty": True}

        result = collection.get(include=["documents", "metadatas"])
        documents, metadatas, corpus = [], [], []
        for doc_id, doc, meta in zip(result["ids"], result["documents"], result["metadatas"]):
            meta = meta or {}
            if meta.get("is_summary", False):
                continue
            documents.append(doc or "")
            metadatas.append(meta)
            corpus.append(tokenize(doc or ""))

        if not documents:
            return {"empty": True}

        bm25 = BM25Okapi(corpus)
        return {"bm25": bm25, "documents": documents, "metadatas": metadatas}

    def _get(self, knowledge_id: str) -> dict:
        with self._lock:
            if knowledge_id not in self._cache:
                try:
                    self._cache[knowledge_id] = self._build(knowledge_id)
                except Exception as err:
                    logger.warning(f"BM25 索引构建失败({knowledge_id}): {err}")
                    self._cache[knowledge_id] = {"empty": True}
            return self._cache[knowledge_id]

    def invalidate(self, knowledge_id: str):
        """文档写入/删除后失效对应知识库的缓存"""
        with self._lock:
            self._cache.pop(knowledge_id, None)

    def search(self, knowledge_id: str, queries: List[str], top_k: int = 10) -> List[SearchModel]:
        entry = self._get(knowledge_id)
        if entry.get("empty"):
            return []

        bm25: BM25Okapi = entry["bm25"]
        scores = [0.0] * len(entry["documents"])
        for q in queries:
            tokens = tokenize(q)
            if not tokens:
                continue
            for i, s in enumerate(bm25.get_scores(tokens)):
                scores[i] += float(s)

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results: List[SearchModel] = []
        for i in ranked:
            # 精确零分 = 查询词面完全未命中；负分是极小语料下的 IDF 现象，仍是有效命中
            if scores[i] == 0:
                continue
            meta = entry["metadatas"][i] or {}
            results.append(
                SearchModel(
                    content=entry["documents"][i],
                    chunk_id=meta.get("chunk_id", ""),
                    file_id=meta.get("file_id", ""),
                    file_name=meta.get("file_name", ""),
                    knowledge_id=meta.get("knowledge_id", ""),
                    update_time=meta.get("update_time", ""),
                    summary=meta.get("summary", ""),
                    score=scores[i],
                )
            )
        return results


keyword_index_manager = KeywordIndexManager()
