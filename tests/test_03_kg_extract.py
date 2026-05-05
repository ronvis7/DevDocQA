"""第 3 节：抽取 schema 的纯结构测试。"""

from __future__ import annotations


def test_triples_schema():
    from importlib import import_module

    mod = import_module("03_knowledge_graph.extract")

    # 直接构造一个合法对象，验证 schema
    triples = mod.Triples(
        entities=[mod.Entity(name="孙悟空", type="人物")],
        relations=[mod.Relation(head="孙悟空", relation="徒弟", tail="唐僧")],
    )
    assert triples.entities[0].name == "孙悟空"
    assert triples.relations[0].relation == "徒弟"


def test_extractor_chain_constructs():
    """构建链不发请求，只检查 with_structured_output 不抛错。"""
    from importlib import import_module

    mod = import_module("03_knowledge_graph.extract")
    extractor = mod.build_extractor()
    assert extractor is not None
