"""重排序模块：本地 bge-reranker（fastembed ONNX）为主，Dashscope 云端为备选

三种模式（rag.rerank_mode 配置）：
- local:     本地 CrossEncoder 推理，数据不出内网（默认）
- dashscope: 阿里云 text-rerank，需配置 api_key
- off:       跳过重排，保持召回顺序

任何模式下重排失败都会降级为召回原始顺序，不阻断问答链路。
"""
import asyncio
import json
import threading
from typing import List

import aiohttp
from loguru import logger
from agentchat.settings import app_settings
from agentchat.schemas.rerank import RerankResultModel


class LocalReranker:
    """fastembed TextCrossEncoder 本地重排，懒加载 + 双重检查锁"""

    _model = None
    _lock = threading.Lock()

    @classmethod
    def get_model(cls):
        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    from fastembed.rerank.cross_encoder import TextCrossEncoder

                    model_name = getattr(app_settings.rag, "local_rerank_model", "")
                    logger.info(f"加载本地重排模型: {model_name}")
                    cls._model = TextCrossEncoder(model_name=model_name)
                    logger.info("本地重排模型就绪")
        return cls._model

    @classmethod
    def rerank_sync(cls, query: str, documents: List[str]) -> List[dict]:
        """同步推理（CPU 密集），由 rerank_documents 放入线程池调用"""
        model = cls.get_model()
        scores = list(model.rerank(query, documents))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            {"index": idx, "relevance_score": float(score)}
            for idx, score in ranked
        ]


class Reranker:

    @staticmethod
    def _mode() -> str:
        mode = getattr(app_settings.rag, "rerank_mode", "local")
        return (mode or "local").lower()

    @classmethod
    def preload(cls):
        """应用启动后预加载本地模型，避免首次查询承担加载耗时"""
        if cls._mode() != "local":
            return

        def _load():
            try:
                LocalReranker.get_model()
                logger.info("本地重排模型预加载完成")
            except Exception as err:
                logger.warning(f"重排模型预加载失败（首次调用时将重试）: {err}")

        threading.Thread(target=_load, daemon=True, name="rerank-preload").start()

    @classmethod
    async def _local_rerank(cls, query: str, documents: List[str]) -> List[dict]:
        # 推理是 CPU 密集型同步调用，放入线程池避免阻塞事件循环
        return await asyncio.to_thread(LocalReranker.rerank_sync, query, documents)

    @classmethod
    async def request_rerank(cls, query, documents):
        """Dashscope 云端重排（text-rerank 协议）"""
        if not documents:
            return []

        headers = {
            "Authorization": f"Bearer {app_settings.multi_models.rerank.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": app_settings.multi_models.rerank.model_name,
            "input": {
                "query": query,
                "documents": documents
            },
            "parameters": {
                "return_documents": True,
                "top_n": app_settings.rag.retrival.get('top_k') * 2
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=app_settings.multi_models.rerank.base_url, headers=headers, data=json.dumps(payload)) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['output']['results']
                else:
                    response.raise_for_status()

    @classmethod
    async def rerank_documents(cls, query, documents):
        final_documents = []
        original_documents = documents

        try:
            if cls._mode() == "dashscope":
                results = await cls.request_rerank(query, documents)
            elif cls._mode() == "off":
                results = [
                    {"index": idx, "relevance_score": 1.0 - idx / max(len(documents), 1)}
                    for idx in range(len(documents))
                ]
            else:
                results = await cls._local_rerank(query, documents)
        except Exception as err:
            # 重排失败不阻断问答：降级为召回原始顺序
            logger.warning(f"重排失败，降级为召回原始顺序: {err}")
            results = [
                {"index": idx, "relevance_score": 1.0 - idx / max(len(documents), 1)}
                for idx in range(len(documents))
            ]

        for result in results:
            result = dict(result)
            result['document'] = original_documents[result['index']]

            final_documents.append(RerankResultModel(query=query, content=result['document'],
                                                     score=result['relevance_score'], index=result['index']))
        return final_documents

if __name__ == "__main__":
    asyncio.run(Reranker.rerank_documents(query="什么是文本排序模型", documents=[
            "文本排序模型广泛用于搜索引擎和推荐系统中，它们根据文本相关性对候选文本进行排序",
            "量子计算是计算科学的一个前沿领域",
            "预训练语言模型的发展给文本排序模型带来了新的进展"
        ]))
