"""第 3 节 · 自然语言 → Cypher → 答案

用 langchain-neo4j 提供的 GraphCypherQAChain：
1. LLM 看图谱 schema，把用户问题翻译成 Cypher
2. 自动执行 Cypher 拿到结果
3. LLM 再把结果组织成自然语言回答

⚠️ 这条链对图谱质量敏感：实体命名不一致、关系类型太碎都会让 LLM 写错 Cypher。
   生产环境通常配合 Cypher 模板 / few-shot examples。
"""

from __future__ import annotations

import sys

from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

from shared import get_llm, settings


def main() -> None:
    graph = Neo4jGraph(
        url=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
        # 让 LangChain 自动刷新 schema 给 LLM 看
        refresh_schema=True,
    )

    # 在控制台打印图谱 schema（LLM 看到的就是这段）
    print("📋 图谱 Schema：")
    print(graph.schema)
    print("=" * 60)

    chain = GraphCypherQAChain.from_llm(
        cypher_llm=get_llm(temperature=0.0),
        qa_llm=get_llm(temperature=0.0),
        graph=graph,
        verbose=True,             # 打印 LLM 生成的 Cypher
        return_intermediate_steps=True,
        # 安全开关：不允许执行写操作
        allow_dangerous_requests=True,  # 关闭 LangChain 的安全提示（学习项目本就只读）
    )

    question = " ".join(sys.argv[1:]) or "孙悟空的师父是谁？"
    print(f"\n❓ 问题：{question}")
    result = chain.invoke({"query": question})

    print("\n💡 答案：")
    print(result["result"])

    if "intermediate_steps" in result:
        print("\n🔧 中间步骤（Cypher + 原始结果）：")
        for step in result["intermediate_steps"]:
            print(f"   {step}")


if __name__ == "__main__":
    main()
