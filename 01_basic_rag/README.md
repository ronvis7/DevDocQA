# 第 1 节 · 基础 RAG（LCEL 入门）

## 学什么

用 LangChain 表达式语言（**LCEL**）写出最经典的 RAG 链：

```
用户问题 → 检索（向量库）→ 提示词模板 → LLM → 解析器 → 答案
```

读完本节你应该理解：
- LCEL 的 `|` 在做什么 —— 它是 `Runnable.__or__`，本质是函数组合
- `RunnablePassthrough()` 何时用 —— 让原始输入"穿过"链路而不加工
- `{"key": runnable_a, "key2": runnable_b}` 字面量字典 ≡ `RunnableParallel`
- 为什么要 `format_docs` —— retriever 返回 `list[Document]`，但 prompt 要字符串

## 怎么跑

```powershell
# 在仓库根目录
copy .env.example .env   # 然后填入 DEEPSEEK_API_KEY 和 SILICONFLOW_API_KEY
uv sync

# 1) 入库（首次运行）
uv run python 01_basic_rag/ingest.py

# 2) 问答
uv run python 01_basic_rag/query.py
uv run python 01_basic_rag/query.py "孙悟空的师父是谁？"
uv run python 01_basic_rag/query.py "三国时期蜀汉的丞相是谁？"
```

## 关键代码（一定要读熟）

```python
chain = (
    {
        "context":  retriever | format_docs,   # 一路：检索 → 拼字符串
        "question": RunnablePassthrough(),     # 一路：原样透传
    }
    | prompt                                    # 灌进模板
    | llm                                       # 送给 LLM
    | StrOutputParser()                         # 取 .content
)
```

每一行都是 `Runnable` 之间的串联。这条链有四种能力，开箱即用：
- `chain.invoke(q)` —— 同步一次性
- `chain.stream(q)` —— 流式（本文件用的）
- `chain.batch([q1, q2])` —— 批量
- `chain.ainvoke(q)` / `chain.astream(q)` —— 异步版

## 与 Yuxi 的对照

| 这里 | Yuxi 对应 |
|---|---|
| `Chroma.from_documents(...)` | `MilvusKB.index_file` |
| `vectorstore.as_retriever()` | `query_kb` 工具内部的 retriever |
| LCEL `|` 链 | **没有** —— Yuxi 用 `create_agent` + middleware |

⚠️ Yuxi 之所以不用 LCEL 链，是因为它要让 LLM **自主决定何时调检索**（工具调用），
而本节是"硬拉"每次都先检索。两种范式各有取舍，第 5 节会回头讨论。

## 故障排查

| 现象 | 原因 | 修复 |
|---|---|---|
| `RuntimeError: 环境变量 ... 未配置` | 没建 `.env` | `copy .env.example .env` 并填 key |
| 嵌入接口超时 | SiliconFlow 偶发慢 | 直接重跑 ingest.py，已嵌入的不会重复 |
| 回答总是"资料中未提及" | 切块太短或问题太偏 | 把 `chunk_size` 调大，或换示例文档 |
