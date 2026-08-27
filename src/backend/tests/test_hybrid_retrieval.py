"""混合检索单元测试：RRF 融合逻辑与 BM25 分词

运行：cd src/backend && .venv/Scripts/python -m pytest tests/ -q
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentchat.services.rag.retrieval import rrf_fuse  # noqa: E402
from agentchat.services.rag.keyword_index import tokenize  # noqa: E402
from agentchat.schemas.search import SearchModel  # noqa: E402


def make_doc(chunk_id: str, content: str, score: float = 0.0) -> SearchModel:
    return SearchModel(
        chunk_id=chunk_id,
        content=content,
        score=score,
        file_id="f1",
        file_name="doc.txt",
        knowledge_id="kb1",
        update_time="2026-08-28",
        summary="",
    )


class TestRRFFuse:
    def test_both_lists_agree_boosts_consensus(self):
        """两路都命中的文档应排到只被单路命中的文档之前"""
        a = [make_doc("c1", "both"), make_doc("c2", "only-a")]
        b = [make_doc("c1", "both"), make_doc("c3", "only-b")]
        fused = rrf_fuse([a, b])
        assert fused[0].chunk_id == "c1"
        assert {d.chunk_id for d in fused} == {"c1", "c2", "c3"}

    def test_order_by_rank_not_raw_score(self):
        """融合只看名次：原始分数高低不影响融合结果"""
        high_score = [make_doc("x", "x", score=99.0)]
        low_score = [make_doc("y", "y", score=0.01)]
        fused = rrf_fuse([high_score, low_score])
        # 两路各自排第一 → 融合分数相同 → 去重保序，都不丢弃
        assert len(fused) == 2

    def test_cap_limits_results(self):
        docs = [make_doc(f"c{i}", f"doc{i}") for i in range(30)]
        fused = rrf_fuse([docs], cap=10)
        assert len(fused) == 10

    def test_score_is_rrf_formula(self):
        """首名分数应为 1/(k+1)=1/61，验证公式而非名次巧合"""
        fused = rrf_fuse([[make_doc("solo", "solo")]], k=60)
        assert abs(fused[0].score - 1 / 61) < 1e-9

    def test_empty_input(self):
        assert rrf_fuse([[], []]) == []


class TestTokenizer:
    def test_chinese_segmentation(self):
        tokens = tokenize("员工每月加班上限")
        assert any("加班" in t for t in tokens)
        assert all(t == t.lower() for t in tokens)

    def test_mixed_cn_en(self):
        tokens = tokenize("使用 deepseek-v4-flash 模型")
        assert "deepseek-v4-flash" in tokens or any("deepseek" in t for t in tokens)

    def test_empty(self):
        assert tokenize("") == []


class TestBM25AgainstRealCorpus:
    """小型语料上的行为验证（不依赖 Chroma）"""

    def test_keyword_hits_ranked_first(self):
        from rank_bm25 import BM25Okapi

        corpus_texts = [
            "公司规定员工每天加班时间不得超过2小时，需要提前在OA系统提交加班申请",
            "员工入职满一年后，每年享有5天带薪年假",
            "工资每月15日通过银行代发，由基本工资和绩效奖金组成",
        ]
        corpus = [tokenize(t) for t in corpus_texts]
        bm25 = BM25Okapi(corpus)
        scores = list(bm25.get_scores(tokenize("OA 加班 申请")))
        best = scores.index(max(scores))
        assert best == 0  # 加班条款应词面命中第一篇

    def test_zero_score_when_no_overlap(self):
        from rank_bm25 import BM25Okapi

        corpus = [tokenize(t) for t in ["完全无关的内容", "另一段话"]]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenize("量子纠缠"))
        assert all(s == 0 for s in scores)
