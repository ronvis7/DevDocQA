# 第 4 节 · KG-RAG 融合（项目高潮）

## 学什么

把"向量检索"和"图谱检索"**并发**起来，让 LLM 同时拿到原文片段和结构化事实。

```
                        ┌──▶ 向量检索（语义模糊匹配）─┐
用户问题 → RunnableParallel                        ├─▶ 合并 → prompt → LLM
                        └──▶ 图谱检索（精确关系）──┘
```

## 跑

```powershell
# 前置：第 1 节 ingest 跑过、第 3 节 extract+load 跑过、Neo4j 在跑
uv run python -m 04_kg_rag.chain "孙悟空的师父是谁？他师父还教过别的徒弟吗？"
```

注意要用 `python -m` 因为 `chain.py` 是包内导入。

## 关键认知

### 为什么两路检索互补

| 维度 | 向量检索 | 图谱检索 |
|---|---|---|
| 强项 | 语义模糊（"花果山"≈"美猴王老家"） | 精确关系（A 的徒弟是 B 的徒弟吗？） |
| 弱项 | 多跳推理糊涂 | 字面没命中实体就一无所获 |
| 数据 | 原文 chunk | 三元组 |

合在一起：用户问"孙悟空的师父的另一个徒弟是谁？"，向量召回唐僧相关章节，
图谱直接给出 "唐僧→徒弟→{孙悟空, 猪八戒, 沙僧}" 的结构化答案。

### `RunnableParallel` 的真正威力

```python
RunnableParallel(
    vector_chunks=vector_retriever,
    graph_facts=graph_retriever,
    question=RunnablePassthrough(),
)
```

三路**并发**执行，最慢的一路决定总耗时。生产 RAG 系统的"多路召回 + 融合"
基本都是这个模式。

### 与 Yuxi 的对照

Yuxi 的 LightRAG 集成（`backend/package/yuxi/knowledge/implementations/lightrag.py`）
内部也做了向量+图谱融合，但黑盒；本节是它的**白盒等价物**：
- 我们手动控制图谱检索的 `max_hops` 和命中策略
- 我们手动决定如何把两路结果合到 context（这一步往往是效果差异的关键）

## 进一步玩法

- 给 `_format_context` 加 token 截断，超长时优先保图谱事实
- 在 `graph_search` 里做实体链接（NER + 同义词归并）
- 加一路 BM25 检索（`langchain_community.retrievers.BM25Retriever`），变成三路融合
