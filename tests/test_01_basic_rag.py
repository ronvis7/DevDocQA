"""第 1 节回归测试：能 import + 能构建链。

不真的发请求（避免烧 token），只验证结构。
"""

from __future__ import annotations

import importlib

import pytest


def test_query_module_imports():
    mod = importlib.import_module("01_basic_rag.query")
    assert hasattr(mod, "build_chain")
    assert hasattr(mod, "format_docs")


def test_format_docs_handles_empty():
    from importlib import import_module

    mod = import_module("01_basic_rag.query")
    assert mod.format_docs([]) == ""


@pytest.mark.skipif(
    not __import__("pathlib").Path("data/chroma_db/chroma.sqlite3").exists(),
    reason="需要先跑 01_basic_rag/ingest.py 建索引",
)
def test_chain_invoke_smoke():
    """烟雾测试：链能被实际调用。需 .env + 索引。"""
    from importlib import import_module

    chain = import_module("01_basic_rag.query").build_chain()
    answer = chain.invoke("用一句话介绍一下文档")
    assert isinstance(answer, str)
    assert len(answer) > 0
