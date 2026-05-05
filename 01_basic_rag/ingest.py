"""第 1 节 · 入库脚本

流程：data/tech_docs/ 下的所有文档 → 切块 → bge-small 嵌入 → 写入 Chroma

跑通后会在 data/chroma_db/ 下看到持久化文件，下次 query 不用重新算嵌入。
"""

from __future__ import annotations

from langchain_chroma import Chroma

from shared import get_embedding, load_docs_from_dir, settings, split_documents


def main() -> None:
    print(f"📂 加载文档目录：{settings.tech_docs_dir}")
    documents = load_docs_from_dir(settings.tech_docs_dir)
    print(f"   共 {len(documents)} 篇文档")

    print("✂️  切块（chunk_size=500, overlap=80）...")
    chunks = split_documents(documents)
    print(f"   切出 {len(chunks)} 个 chunks")

    print(f"🧬 嵌入并写入 Chroma：{settings.chroma_persist_dir}")
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)

    # from_documents 会一次性完成「嵌入 + 入库 + 持久化」
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding(),
        persist_directory=str(settings.chroma_persist_dir),
        collection_name="basic_rag",
    )
    print(f"✅ 完成。已索引 {len(chunks)} 个 chunks")


if __name__ == "__main__":
    main()
