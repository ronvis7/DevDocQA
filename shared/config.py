"""加载 .env 并以 dataclass 暴露配置。

设计意图：
- 用 frozen dataclass 而不是全局变量，强制不可变；
- 失败要快：缺关键 key 时直接抛错，避免后续报奇怪的网络错误；
- 第 1-2 节只读 LLM 字段；第 3+ 节才读 Neo4j 字段。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 从仓库根目录的 .env 加载（运行入口可能在子目录里，所以指定路径）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _required(key: str) -> str:
    value = os.getenv(key)
    if not value or value.startswith("sk-xxx"):
        raise RuntimeError(
            f"环境变量 {key} 未配置。请复制 .env.example 到 .env 并填入真实 key。"
        )
    return value


def _optional(key: str, default: str) -> str:
    return os.getenv(key) or default


@dataclass(frozen=True)
class Settings:
    # LLM (DeepSeek) —— 唯一需要的 API key
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    # Neo4j（第 3-5 节才用）
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str
    # 本地路径
    project_root: Path
    chroma_persist_dir: Path
    tech_docs_dir: Path


def _build_settings() -> Settings:
    return Settings(
        deepseek_api_key=_required("DEEPSEEK_API_KEY"),
        deepseek_base_url=_optional("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        deepseek_model=_optional("DEEPSEEK_MODEL", "deepseek-chat"),
        neo4j_uri=_optional("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_username=_optional("NEO4J_USERNAME", "neo4j"),
        neo4j_password=_optional("NEO4J_PASSWORD", "mini-rag-kg-pass"),
        neo4j_database=_optional("NEO4J_DATABASE", "neo4j"),
        project_root=PROJECT_ROOT,
        chroma_persist_dir=PROJECT_ROOT / _optional("CHROMA_PERSIST_DIR", "data/chroma_db"),
        tech_docs_dir=PROJECT_ROOT / _optional("TECH_DOCS_DIR", "data/tech_docs"),
    )


# 模块级单例 —— 第一次 import 时校验环境变量
settings = _build_settings()
