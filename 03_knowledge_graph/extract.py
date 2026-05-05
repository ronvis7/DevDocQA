"""第 3 节 · 用 LLM 抽取实体与关系（结构化输出）

核心技巧：用 Pydantic 定义目标 schema，再用 `llm.with_structured_output(Schema)`，
LangChain 会自动告诉 LLM "请按这个 JSON 格式返回"，并校验结果。
比裸 prompt + JSON 解析稳定得多。

不需要 Neo4j，先看抽取结果再说。
"""

from __future__ import annotations

import json
import sys

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from shared import get_llm, load_docs_from_dir, settings


# ---------- ① Pydantic schema：告诉 LLM 我们要什么形状 ----------

class Entity(BaseModel):
    """图谱中的一个节点。"""
    name: str = Field(description="实体名称，如「孙悟空」「花果山」")
    type: str = Field(description="实体类型：人物 / 地点 / 组织 / 物品 / 事件 之一")


class Relation(BaseModel):
    """图谱中的一条边。head --[relation]--> tail。"""
    head: str = Field(description="关系起点的实体名称")
    relation: str = Field(description="关系类型，如「师父」「居住于」「攻打」")
    tail: str = Field(description="关系终点的实体名称")


class Triples(BaseModel):
    """从一段文本中抽到的所有三元组。"""
    entities: list[Entity] = Field(description="文本中出现的所有命名实体（去重）")
    relations: list[Relation] = Field(description="文本中体现的所有实体间关系")


# ---------- ② 构造抽取链 ----------

EXTRACT_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个知识图谱抽取专家。给定中文文本，请抽取其中出现的实体和关系。\n"
        "要求：\n"
        "1. 实体名称使用文中出现的原词，避免归并不同名（如「悟空」和「孙悟空」按文中所写）\n"
        "2. 关系动词要简洁（2-4 字最佳）\n"
        "3. 只抽取文中**明确**体现的事实，不要推断\n"
        "4. 同一对实体的多条关系都要列出",
    ),
    ("human", "文本：\n{text}"),
])


def build_extractor():
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(Triples)
    return EXTRACT_PROMPT | structured_llm


# ---------- ③ CLI：抽 sample_docs 里所有文档 ----------

def main() -> None:
    extractor = build_extractor()

    documents = load_docs_from_dir(settings.tech_docs_dir)
    print(f"📂 待抽取 {len(documents)} 篇文档\n")

    all_triples: list[dict] = []
    for doc in documents:
        # 简单截断防止超长；生产环境应该按段切再合并
        text = doc.page_content[:3000]
        print(f"🔎 抽取：{doc.metadata['source']}（{len(text)} 字）...")
        result: Triples = extractor.invoke({"text": text})
        print(f"   → {len(result.entities)} 个实体，{len(result.relations)} 条关系")
        all_triples.append({
            "source": doc.metadata["source"],
            "entities": [e.model_dump() for e in result.entities],
            "relations": [r.model_dump() for r in result.relations],
        })

    out_path = settings.project_root / "data" / "triples.json"
    out_path.write_text(
        json.dumps(all_triples, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✅ 三元组已写入：{out_path}")
    if "--show" in sys.argv:
        print(json.dumps(all_triples, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
