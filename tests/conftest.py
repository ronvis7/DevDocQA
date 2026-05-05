"""测试装置：把仓库根目录加进 sys.path，让 `from shared import ...` 工作。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def has_chroma_index(project_root) -> bool:
    return (project_root / "data" / "chroma_db" / "chroma.sqlite3").exists()


@pytest.fixture(scope="session")
def has_neo4j() -> bool:
    """快速检查 Neo4j 是否可达，1 秒超时。"""
    try:
        from neo4j import GraphDatabase

        from shared import settings

        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
            connection_timeout=1.0,
        )
        with driver.session(database=settings.neo4j_database) as s:
            s.run("RETURN 1").single()
        driver.close()
        return True
    except Exception:
        return False
