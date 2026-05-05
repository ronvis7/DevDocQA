"""端到端真值测试：构造迷你语料 → 入库 → 检索，验证语义命中正确文档。

不调用 DeepSeek，只用本地 BGE embedding + Chroma 临时目录。
首次运行会从 HuggingFace 下载 BGE 模型 (~100MB)；离线/超时会自动 skip。
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def mini_corpus(tmp_path: Path) -> Path:
    """构造一个临时迷你语料：3 个主题明显不同的文档。"""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "react.md").write_text(
        "# React\n\n在 React 中，useEffect 是处理副作用的钩子函数，"
        "依赖数组决定何时重新执行；空数组只在挂载时执行一次。",
        encoding="utf-8",
    )
    (corpus / "vue.md").write_text(
        "# Vue\n\nVue 通过 ref 和 reactive 创建响应式数据，watch 用来监听响应式数据的变化并执行副作用。",
        encoding="utf-8",
    )
    (corpus / "fastapi.md").write_text(
        "# FastAPI\n\nFastAPI 通过 Depends 函数实现依赖注入，Pydantic 模型用于声明请求体并自动校验。",
        encoding="utf-8",
    )
    return corpus


@pytest.fixture(scope="session")
def has_embedding_model() -> bool:
    """检查能否加载 BGE 模型（首次需联网下载）。"""
    try:
        from shared import get_embedding

        get_embedding().embed_query("ping")
        return True
    except Exception:
        return False


def test_e2e_ingest_and_retrieve(
    tmp_path: Path,
    mini_corpus: Path,
    has_embedding_model: bool,
) -> None:
    """端到端：建迷你库 → 检索 → 验证 top-1 命中语义对应文档。

    这是一个"真值"测试：覆盖 文档加载 / 切块 / 嵌入 / 持久化 / 召回 全链路，
    只在离线或模型下载失败时 skip。
    """
    if not has_embedding_model:
        pytest.skip("BGE embedding 模型不可用（离线 / 首次下载未完成）")

    from langchain_chroma import Chroma

    from shared import get_embedding, load_docs_from_dir, split_documents

    # 1. ingest
    docs = load_docs_from_dir(mini_corpus)
    assert len(docs) == 3, "应加载 3 篇文档"

    chunks = split_documents(docs)
    assert len(chunks) >= 3, "至少每篇应保留一个 chunk"

    # 2. 写入 Chroma 临时目录（独立于项目实际索引）
    chroma_dir = tmp_path / "chroma"
    vs = Chroma.from_documents(
        documents=chunks,
        embedding=get_embedding(),
        persist_directory=str(chroma_dir),
        collection_name="test_e2e",
    )

    retriever = vs.as_retriever(search_kwargs={"k": 1})

    # 3. 语义召回正确性验证（不依赖 LLM）
    # React 关键词应命中 React 文档
    react_hits = retriever.invoke("useEffect 钩子怎么用")
    assert len(react_hits) == 1
    assert "React" in react_hits[0].page_content or "useEffect" in react_hits[0].page_content

    # FastAPI 关键词应命中 FastAPI 文档
    fastapi_hits = retriever.invoke("依赖注入是什么")
    assert "FastAPI" in fastapi_hits[0].page_content or "Depends" in fastapi_hits[0].page_content

    # Vue 响应式 → Vue 文档
    vue_hits = retriever.invoke("响应式数据怎么定义")
    assert "Vue" in vue_hits[0].page_content or "reactive" in vue_hits[0].page_content


def test_format_docs_concatenates_with_source_tag() -> None:
    """验证 format_docs 按预期格式拼接：[source] content。"""
    from importlib import import_module

    from langchain_core.documents import Document

    query_mod = import_module("01_basic_rag.query")
    docs = [
        Document(page_content="alpha", metadata={"source": "a.md"}),
        Document(page_content="beta", metadata={"source": "b.md"}),
    ]
    text = query_mod.format_docs(docs)
    assert "[a.md] alpha" in text
    assert "[b.md] beta" in text
    assert text.count("\n\n") == 1, "两段之间应只有一个空行分隔"
