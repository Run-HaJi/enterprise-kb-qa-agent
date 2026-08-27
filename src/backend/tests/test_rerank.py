"""重排模块单元测试：模式路由、本地排序映射、失败降级

不加载真实模型：通过 monkeypatch 替换 LocalReranker.get_model。
运行：cd src/backend && .venv/Scripts/python -m pytest tests/ -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentchat.services.rag import rerank as rerank_module  # noqa: E402
from agentchat.services.rag.rerank import Reranker  # noqa: E402
from agentchat.settings import app_settings  # noqa: E402
from agentchat.schemas.common import Rag  # noqa: E402


class FakeModel:
    """模拟 CrossEncoder：包含"重排"的文档得分高"""

    def rerank(self, query, documents):
        scores = []
        for doc in documents:
            s = 1.0 if "重排" in doc else 0.1
            scores.append(s)
        return scores

    @staticmethod
    def make():
        return FakeModel()


@pytest.fixture
def docs():
    return [
        "无关文档A",
        "讲重排模型的文档",
        "无关文档B",
    ]


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    """每个用例隔离模型单例与配置"""
    if app_settings.rag is None or not isinstance(app_settings.rag, Rag):
        app_settings.rag = Rag()
    monkeypatch.setattr(rerank_module.LocalReranker, "_model", None)
    monkeypatch.setattr(rerank_module.LocalReranker, "get_model", FakeModel.make)
    app_settings.rag.rerank_mode = "local"
    yield
    app_settings.rag.rerank_mode = "local"


class TestLocalRerank:
    @pytest.mark.asyncio
    async def test_orders_by_relevance(self, docs):
        results = await Reranker.rerank_documents("重排怎么做", docs)
        assert results[0].index == 1  # 含"重排"的文档排第一
        assert results[0].content == docs[1]
        assert results[0].score >= results[-1].score

    @pytest.mark.asyncio
    async def test_indices_map_to_original(self, docs):
        results = await Reranker.rerank_documents("任意", docs)
        for r in results:
            assert r.content == docs[r.index]


class TestDegradation:
    @pytest.mark.asyncio
    async def test_model_failure_falls_back_to_recall_order(self, docs, monkeypatch):
        def boom():
            raise RuntimeError("model not loaded")

        monkeypatch.setattr(rerank_module.LocalReranker, "rerank_sync", boom)
        results = await Reranker.rerank_documents("任意", docs)
        assert [r.index for r in results] == [0, 1, 2]  # 召回原始顺序
        assert results[0].score > results[-1].score

    @pytest.mark.asyncio
    async def test_off_mode_keeps_recall_order(self, docs, monkeypatch):
        app_settings.rag.rerank_mode = "off"
        called = {"flag": False}

        def spy(*a, **k):
            called["flag"] = True
            return FakeModel.rerank(*a[1:], **k)

        monkeypatch.setattr(rerank_module.LocalReranker, "rerank_sync", spy)
        results = await Reranker.rerank_documents("任意", docs)
        assert called["flag"] is False  # off 模式不触发推理
        assert [r.index for r in results] == [0, 1, 2]


class TestModeRouting:
    @pytest.mark.asyncio
    async def test_dashscope_mode_skips_local(self, docs, monkeypatch):
        app_settings.rag.rerank_mode = "dashscope"

        def spy(*a, **k):
            raise AssertionError("local 不应被调用")

        monkeypatch.setattr(rerank_module.LocalReranker, "rerank_sync", spy)

        async def fake_request(query, documents):
            return [{"index": 2, "relevance_score": 0.9}]

        monkeypatch.setattr(Reranker, "request_rerank", fake_request)
        results = await Reranker.rerank_documents("任意", docs)
        assert results[0].index == 2  # 走云端结果
