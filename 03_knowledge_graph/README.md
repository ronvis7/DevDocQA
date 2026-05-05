# 第 3 节 · 知识图谱

## 学什么

把非结构化文档变成结构化的"实体-关系"图，存进 Neo4j，再用三种方式查询：

```
原始文本
   ↓ extract.py     ★ Pydantic schema + with_structured_output
三元组 JSON
   ↓ load_to_neo4j.py
Neo4j
   ↓ query_cypher.py     纯 Cypher
   ↓ nl_to_cypher.py     LLM 自动翻译 Cypher
```

## 启动 Neo4j（首次）

```powershell
docker compose up -d neo4j
# 等约 20 秒后访问 http://localhost:7474
# 账号 neo4j / 密码 mini-rag-kg-pass（见 .env）
```

## 跑

```powershell
# ① 抽三元组（写到 data/triples.json）
uv run python 03_knowledge_graph/extract.py
uv run python 03_knowledge_graph/extract.py --show   # 同时打印结果

# ② 写入 Neo4j（会先清库）
uv run python 03_knowledge_graph/load_to_neo4j.py

# ③ 直接 Cypher 查询
uv run python 03_knowledge_graph/query_cypher.py

# ④ 自然语言 → Cypher
uv run python 03_knowledge_graph/nl_to_cypher.py "唐僧的徒弟有哪些？"
```

## 关键认知

### `with_structured_output(Pydantic)` 才是抽取的正确姿势

错误姿势：在 prompt 里写"请输出 JSON"然后 `json.loads()`。模型偶尔会输出额外文字、Markdown 围栏、错误引号，解析就崩。

正确姿势：

```python
class Triples(BaseModel):
    entities: list[Entity]
    relations: list[Relation]

extractor = llm.with_structured_output(Triples)
triples: Triples = extractor.invoke({"text": "..."})  # ← 直接拿到 Pydantic 对象
```

LangChain 会自动选最佳协议（OpenAI function call / JSON mode）让模型严格遵守 schema。

### 图谱设计的小决策

- **节点用 `:Entity`，类型存属性**：避免动态标签需要 APOC，简化新手入门
- **关系类型存属性 `r.type`**：动态关系标签 Cypher 写起来更绕，统一 `:REL` 边更方便扩展
- **`MERGE` 而不是 `CREATE`**：幂等，重复跑不出错

### 与 Yuxi 的对照

| 这里 | Yuxi 对应 |
|---|---|
| `extract.py` 用 `with_structured_output` 抽三元组 | LightRAG 内部也是 LLM-based 抽取，但黑盒 |
| `load_to_neo4j.py` 手写 Cypher MERGE | `backend/package/yuxi/knowledge/graphs/upload_graph_service.py` |
| `nl_to_cypher.py` 用 GraphCypherQAChain | Yuxi 的 `query_kb` 工具底层走 LightRAG，对图的查询封装更深 |

## 故障排查

| 现象 | 修复 |
|---|---|
| `Could not connect to bolt://localhost:7687` | `docker compose up -d neo4j` 等 20 秒 |
| `data/triples.json not found` | 先跑 `extract.py` |
| nl_to_cypher 答非所问 | LLM 写错了 Cypher，看 `verbose=True` 的输出，调整 schema 或换大模型 |
