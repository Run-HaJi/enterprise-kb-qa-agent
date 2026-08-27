from agentchat.services.rag.vector_stores import vector_client


class VectorRetrieval:
    """向量库文档检索：支持单条或多条改写查询跨知识库召回"""

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
