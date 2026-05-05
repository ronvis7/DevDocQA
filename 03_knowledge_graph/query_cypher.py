"""第 3 节 · 直接写 Cypher 查图谱（手动模式）

读完这一份你应该能：
1. 看懂 MATCH / WHERE / RETURN 三板斧
2. 知道怎么用 `r.type` 这种属性约束代替动态关系标签
3. 用 1-2 跳邻居扩展（k-hop neighborhood）
"""

from __future__ import annotations

from neo4j import GraphDatabase

from shared import settings

QUERIES: list[tuple[str, str]] = [
    (
        "① 列出前 10 个实体及类型",
        "MATCH (e:Entity) RETURN e.name AS name, e.type AS type LIMIT 10",
    ),
    (
        "② 找出某个实体的所有出边",
        """
        MATCH (h:Entity {name: $name})-[r:REL]->(t:Entity)
        RETURN h.name AS head, r.type AS relation, t.name AS tail
        """,
    ),
    (
        "③ 找出与某实体一跳相连的所有邻居（双向）",
        """
        MATCH (e:Entity {name: $name})-[r:REL]-(neighbor:Entity)
        RETURN DISTINCT neighbor.name AS neighbor, neighbor.type AS type
        """,
    ),
    (
        "④ 两跳内能到达的实体（用于第 4 节图扩展）",
        """
        MATCH path = (e:Entity {name: $name})-[:REL*1..2]-(other:Entity)
        WHERE other.name <> $name
        RETURN DISTINCT other.name AS name, other.type AS type
        LIMIT 20
        """,
    ),
]


def main() -> None:
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    # 拿一个真实存在的实体名做参数，否则 ② ③ ④ 全空
    with driver.session(database=settings.neo4j_database) as session:
        sample = session.run("MATCH (e:Entity) RETURN e.name AS name LIMIT 1").single()
        if not sample:
            print("⚠️  图谱为空，请先跑 load_to_neo4j.py")
            return
        focus_name = sample["name"]
        print(f"🎯 演示焦点实体：{focus_name}\n")

        for title, cypher in QUERIES:
            print(f"\n{title}")
            print(f"  Cypher: {cypher.strip()}")
            records = session.run(cypher, name=focus_name).data()
            for rec in records[:10]:
                print(f"  → {rec}")
            if len(records) > 10:
                print(f"  ... 共 {len(records)} 条")

    driver.close()


if __name__ == "__main__":
    main()
