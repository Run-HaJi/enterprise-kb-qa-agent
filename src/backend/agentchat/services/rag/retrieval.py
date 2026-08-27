from typing import List

from loguru import logger

from agentchat.services.rag.keyword_index import keyword_index_manager
from agentchat.services.rag.vector_stores import vector_client
from agentchat.settings import app_settings

RRF_K = 60  # Reciprocal Rank Fusion 常数，平滑名次差异


def rrf_fuse(result_lists: List[List], k: int = RRF_K, cap: int = 10) -> List:
    """Reciprocal Rank Fusion：按名次倒数融合多路召回结果

    每路结果各自按相关性排好序，文档得分为 sum(1/(k + rank))。
    以 chunk_id 去重合并，返回按融合分数降序的前 cap 条。
    只依赖名次而非原始分数，天然规避向量相似度与 BM25 分值不可比的问题。
    """
    fused = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = doc.chunk_id
            if key not in fused:
                fused[key] = {"doc": doc, "score": 0.0}
            fused[key]["score"] += 1.0 / (k + rank + 1)

    merged = sorted(fused.values(), key=lambda item: item["score"], reverse=True)[:cap]

    out = []
    for item in merged:
        doc = item["doc"]
        doc.score = item["score"]  # 覆写为融合分数，仅用于后续排序与去重
        out.append(doc)
    return out


class VectorRetrieval:
    """纯向量召回（语义相似）"""

    @classmethod
    async def retrieve_documents(cls, query, knowledges_id, search_field):
        documents = []
        queries = query if isinstance(query, list) else [query]

        for query in queries:
            for knowledge_id in knowledges_id:
                if search_field == "summary":
                    documents += await vector_client.search_summary(query, knowledge_id)
                else:
                    documents += await vector_client.search(query, knowledge_id)

        return documents


class HybridRetrieval:
    """双路召回：BM25 关键词 + 向量语义，RRF 融合"""

    @classmethod
    async def retrieve_documents(cls, query_list, knowledges_id, search_field):
        vector_results = await VectorRetrieval.retrieve_documents(
            query_list, knowledges_id, search_field
        )
        result_lists = [vector_results]

        if app_settings.rag.enable_keyword_recall:
            try:
                keyword_results = []
                for knowledge_id in knowledges_id:
                    keyword_results += keyword_index_manager.search(
                        knowledge_id, query_list, top_k=10
                    )
                result_lists.append(keyword_results)
            except Exception as err:
                # 关键词路失效不阻断检索，退化为纯向量
                logger.warning(f"BM25 关键词召回失败，退化为纯向量: {err}")

        return rrf_fuse(result_lists)
