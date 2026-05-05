"""第 3 节 · 把三元组写入 Neo4j

读 data/triples.json（由 extract.py 生成），用 Cypher MERGE 幂等写入。

MERGE 语义：节点/关系不存在就创建，存在就跳过 —— 重复跑不会报错也不会重复。
"""

from __future__ import annotations

import json
from collections import Counter

from neo4j import GraphDatabase

from shared import settings


def main() -> None:
    triples_path = settings.project_root / "data" / "triples.json"
    if not triples_path.exists():
        raise FileNotFoundError("先跑 03_knowledge_graph/extract.py 生成 data/triples.json")

    payload = json.loads(triples_path.read_text(encoding="utf-8"))

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    type_counter: Counter[str] = Counter()
    rel_counter: Counter[str] = Counter()

    with driver.session(database=settings.neo4j_database) as session:
        # 清库（学习用，方便反复跑）
        session.run("MATCH (n) DETACH DELETE n")

        for doc in payload:
            source = doc["source"]

            # 写实体节点
            for ent in doc["entities"]:
                # 用属性 type 区分类别，避免动态标签的麻烦
                session.run(
                    """
                    MERGE (e:Entity {name: $name})
                    ON CREATE SET e.type = $type, e.source = $source
                    """,
                    name=ent["name"],
                    type=ent["type"],
                    source=source,
                )
                type_counter[ent["type"]] += 1

            # 写关系
            for rel in doc["relations"]:
                # 关系类型作为动态属性 + 一个统一的 :REL 边类型，方便 Cypher 查询
                session.run(
                    """
                    MERGE (h:Entity {name: $head})
                    MERGE (t:Entity {name: $tail})
                    MERGE (h)-[r:REL {type: $rel_type}]->(t)
                    ON CREATE SET r.source = $source
                    """,
                    head=rel["head"],
                    tail=rel["tail"],
                    rel_type=rel["relation"],
                    source=source,
                )
                rel_counter[rel["relation"]] += 1

        # 统计
        result = session.run("MATCH (n:Entity) RETURN count(n) AS n")
        node_count = result.single()["n"]
        result = session.run("MATCH ()-[r:REL]->() RETURN count(r) AS n")
        edge_count = result.single()["n"]

    driver.close()

    print(f"✅ 入库完成。节点：{node_count}，关系：{edge_count}")
    print(f"   实体类型分布：{dict(type_counter)}")
    print(f"   高频关系 Top5：{rel_counter.most_common(5)}")
    print("\n🌐 打开 http://localhost:7474 看图（账号 neo4j / 密码见 .env）")
    print("   试试这条 Cypher：MATCH p=()-[:REL]->() RETURN p LIMIT 50")


if __name__ == "__main__":
    main()
