"""第 0 层：shared 模块的纯单元测试，不需要外部服务。"""

from __future__ import annotations

import pytest
from langchain_core.documents import Document


def test_split_documents_chinese_friendly():
    from shared.docs import split_documents

    long_text = "孙悟空是花果山的猴王。" * 50
    docs = [Document(page_content=long_text, metadata={"source": "test.txt"})]
    chunks = split_documents(docs, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1, "长文本应该被切成多块"
    assert all(c.metadata["source"] == "test.txt" for c in chunks), "metadata 必须保留"
    assert all(len(c.page_content) <= 220 for c in chunks), "切块尺寸应该接近设置值"


def test_settings_loaded():
    from shared import settings

    # 不检查具体值（取决于 .env），只确认结构存在
    assert settings.deepseek_model
    assert settings.deepseek_base_url
    assert settings.project_root.exists()


@pytest.mark.parametrize("ext", [".txt", ".md"])
def test_load_text_file(tmp_path, ext):
    from shared.docs import load_docs_from_dir

    f = tmp_path / f"sample{ext}"
    f.write_text("Hello 世界", encoding="utf-8")

    docs = load_docs_from_dir(tmp_path)
    assert len(docs) == 1
    assert docs[0].page_content == "Hello 世界"
    assert docs[0].metadata["source"] == f.name
