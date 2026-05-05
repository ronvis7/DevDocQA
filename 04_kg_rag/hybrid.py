"""第 4 节 · 双路检索器：向量召回 + 图谱邻居扩展

两条独立的检索函数，都包成 Runnable，方便第二个文件 chain.py 用 RunnableParallel 并起来。
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.runnables import RunnableLambda
from neo4j import GraphDatabase

from shared import get_embedding, settings

# ---------- ① 向量检索（来自第 1 节的 Chroma） ----------

_vectorstore = Chroma(
    persist_directory=str(settings.chroma_persist_dir),
    embedding_function=get_embedding(),
    collection_name="basic_rag",
)
_chroma_retriever = _vectorstore.as_retriever(search_kwargs={"k": 4})


def vector_search(query: str) -> list[dict]:
    """语义召回最相关的 chunk。"""
    docs = _chroma_retriever.invoke(query)
    return [{"source": d.metadata.get("source", "?"), "content": d.page_content} for d in docs]


# ---------- ② 图谱检索：先匹配实体，再扩展邻居 ----------

_driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_username, settings.neo4j_password),
)


def graph_search(query: str, max_hops: int = 2, limit: int = 30) -> list[dict]:
    """图谱检索：
    1. 在图谱里找出 query 字面包含的所有实体名
    2. 围绕这些实体做 1-2 跳邻居扩展
    3. 把所有相关三元组拍平返回

    生产里第 1 步会改用实体链接（NER + 实体消歧），这里为了简单直接做字符串匹配。
    """
    with _driver.session(database=settings.neo4j_database) as session:
        # 拿全部实体名（小型图谱可接受；大图请改 fulltext index）
        all_names = [r["name"] for r in session.run("MATCH (e:Entity) RETURN e.name AS name").data()]
        seeds = [n for n in all_names if n and n in query]

        if not seeds:
            return []

        # 找出种子实体周围 1-N 跳能到达的所有三元组
        records = session.run(
            f"""
            MATCH (h:Entity)-[r:REL]->(t:Entity)
            WHERE h.name IN $seeds
               OR t.name IN $seeds
               OR EXISTS {{
                  MATCH (h)-[:REL*1..{max_hops}]-(seed:Entity)
                  WHERE seed.name IN $seeds
               }}
            RETURN DISTINCT h.name AS head, r.type AS relation, t.name AS tail
            LIMIT $limit
            """,
            seeds=seeds,
            limit=limit,
        ).data()

    return [{"head": r["head"], "relation": r["relation"], "tail": r["tail"]} for r in records]


# ---------- ③ 包成 Runnable 方便链式组合 ----------

vector_retriever = RunnableLambda(vector_search)
graph_retriever = RunnableLambda(graph_search)
