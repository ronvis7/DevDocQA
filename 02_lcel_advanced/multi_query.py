"""第 2 节 · MultiQueryRetriever —— 一句变多句

用户的原问题往往不够好。让 LLM 自动改写成 3-5 个不同角度的查询，
分别去检索后取并集，能显著提升召回率。

依赖第 1 节的 Chroma 索引。先跑过 01_basic_rag/ingest.py 再来。
"""

from __future__ import annotations

import sys

from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_chroma import Chroma

from shared import get_embedding, get_llm, settings


def main() -> None:
    vectorstore = Chroma(
        persist_directory=str(settings.chroma_persist_dir),
        embedding_function=get_embedding(),
        collection_name="basic_rag",
    )
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 关键一行：把基础 retriever + LLM 包成多查询 retriever
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=get_llm(temperature=0.0),
    )

    # 打开 LangChain 的日志看 LLM 改写出了哪些查询
    import logging

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)

    question = " ".join(sys.argv[1:]) or "孙悟空有哪些本领？"
    print(f"❓ 原问题：{question}\n")

    docs = retriever.invoke(question)
    print(f"\n📚 召回 {len(docs)} 条 chunk（去重后）：")
    for i, d in enumerate(docs, 1):
        print(f"  {i}. [{d.metadata.get('source')}] {d.page_content[:80]}...")


if __name__ == "__main__":
    main()
