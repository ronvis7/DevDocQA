# 第 2 节 · LCEL 进阶

把第 1 节的链拆成零件，每个零件单独玩透。

| 文件 | 学什么 |
|---|---|
| `runnables.py` | `RunnablePassthrough` / `RunnableParallel` / `RunnableLambda` 三大件 |
| `streaming.py` | `.stream()` / `.astream()` —— 所有 LCEL 链自动支持流式 |
| `multi_query.py` | `MultiQueryRetriever` —— LLM 自动改写问题，提升召回 |
| `history_aware.py` | 带历史改写的对话式 RAG（生产标配） |

## 跑

```powershell
uv run python 02_lcel_advanced/runnables.py
uv run python 02_lcel_advanced/streaming.py
uv run python 02_lcel_advanced/multi_query.py "唐僧"
uv run python 02_lcel_advanced/history_aware.py
```

依赖第 1 节的 Chroma 索引（`uv run python 01_basic_rag/ingest.py` 跑过即可）。

## 关键认知

- **LCEL = 函数组合**：`a | b | c` 等价于 `c(b(a(input)))`，只是把同步/异步/流式/批量自动配齐了。
- **dict 字面量 = `RunnableParallel`**：写 `{"k1": r1, "k2": r2}` 时 LangChain 会自动转成并行执行。
- **`.invoke / .stream / .batch / .ainvoke / .astream / .abatch`**：每条链都自带 6 种调用方式，一次性写一种就够。
- **MultiQuery / HistoryAware** 这类"高阶 retriever" 本质上都是再叠一层 LCEL 链。

## 还想深入

- `langchain.retrievers.contextual_compression.ContextualCompressionRetriever`：检索后用 LLM 再过滤
- `langchain.retrievers.parent_document.ParentDocumentRetriever`：小块召回 + 大块返回，平衡精度与上下文
- `langchain_core.runnables.RunnableConfig`：给链加 callback、tags、metadata，配合 LangSmith 追踪
