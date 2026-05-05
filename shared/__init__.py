"""跨章节共享的最小工具层。

只暴露三件事：LLM、Embedding、文档加载/切块。
其他章节优先 import 这里的工厂函数，避免重复配置。
"""

from shared.config import settings
from shared.docs import load_docs_from_dir, split_documents
from shared.embedding import get_embedding
from shared.llm import get_llm

__all__ = [
    "settings",
    "get_llm",
    "get_embedding",
    "load_docs_from_dir",
    "split_documents",
]
