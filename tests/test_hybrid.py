"""分岐とGraphの取得範囲を、実際のLLM・APIを呼ばずに確認する。"""

import json
from unittest.mock import Mock

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from app import hybrid, retrieval
from app.agent import print_trace


@pytest.mark.parametrize("sufficient,has_page,graph_fails", [
    (True, True, False), (False, True, False), (False, False, False), (False, True, True),
])
def test_tree_then_conditional_graph(monkeypatch, capsys, sufficient, has_page, graph_fails):
    graph = Mock(return_value={"expanded": [
        {"page_id": "lec02-main-p053", "content": "追加の根拠"}
    ]})
    if graph_fails:
        graph.side_effect = FileNotFoundError("graph.jsonがありません")
    monkeypatch.setattr(retrieval, "expand_graph", graph)
    # Treeの全文を読んだ後に充足判断し、最後に別のモデル呼び出しで回答する。
    steps = []

    def respond(messages, info):
        if not info.output_tools:
            prompt = json.loads(messages[-1].parts[0].content)
            assert bool(prompt["tree_pages"]) == has_page
            assert bool(prompt["graph_pages"]) == (not sufficient and has_page and not graph_fails)
            assert bool(prompt["graph_error"]) == (graph_fails or not has_page)
            return ModelResponse(parts=[TextPart("本文に基づく回答")])
        steps.append(1)
        route = [None, "lec02-main", "lec02-main-s045", "lec02-main-p052"] if has_page else [None]
        if len(steps) <= len(route):
            return ModelResponse(parts=[ToolCallPart("browse_tree", {"node_id": route[len(steps) - 1]})])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
            "sufficient": sufficient, "reason": "本文を確認した結果",
            "missing_information": [] if sufficient else ["追加の説明"],
            "anchor_page_ids": ["lec02-main-p052"] if has_page else [],
        })])

    result = hybrid.run_hybrid("質問", FunctionModel(respond))
    assert result.output == "本文に基づく回答"
    assert result.usage.requests == (6 if has_page else 3)
    if not sufficient and has_page:
        graph.assert_called_once_with(["lec02-main-p052"])
    else:
        graph.assert_not_called()
    if sufficient:
        assert result.graph is None
    elif not has_page:
        assert "error" in result.graph
    print_trace(result, 1.0)
    trace = capsys.readouterr().out
    assert "[充足判断]" in trace and "[usage]" in trace and "[cost]" in trace
    assert ("実行せず" in trace) == sufficient


def test_graph_expands_tree_seeds_without_vector_search(monkeypatch):
    monkeypatch.setattr(retrieval, "search", Mock(side_effect=AssertionError("検索は不要")))
    result = retrieval.expand_graph(["lec02-main-p052", "lec02-main-p052"])
    assert [page["page_id"] for page in result["seeds"]] == ["lec02-main-p052"]
    all_pages = result["seeds"] + result["expanded"]
    ids = [page["page_id"] for page in all_pages]
    assert len(ids) == len(set(ids)) <= retrieval.GRAPH_MAX_RESULTS
    assert {"lec02-main-p051", "lec02-main-p053"} <= set(ids)
    assert all(page["hops"] <= retrieval.GRAPH_HOPS for page in all_pages)
    assert all(page["content"] and page["lecture"] and page["page"] for page in all_pages)
    with pytest.raises(ValueError):
        retrieval.expand_graph(["unknown-page"])


def test_unread_anchor_is_rejected():
    calls = []

    def respond(messages, info):
        calls.append(1)
        if len(calls) == 1:
            return ModelResponse(parts=[ToolCallPart("browse_tree", {})])
        if len(calls) > 2:
            # 不正な入口に対するModelRetryをモデルが受け取る。
            assert any("本文を取得したページID" in str(part) for part in messages[-1].parts)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
            "sufficient": False, "reason": "根拠不足", "missing_information": ["説明"],
            "anchor_page_ids": ["lec02-main-p052"] if len(calls) == 2 else [],
        })])

    checker, _ = hybrid.build_tree_checker()
    result = checker.run_sync("質問", model=FunctionModel(respond))
    assert result.output.anchor_page_ids == []
    assert len(calls) == 3


def test_tree_cannot_be_skipped_or_jump_to_undiscovered_page():
    step = 0

    def respond(messages, info):
        nonlocal step
        step += 1
        if step == 1:
            # ツールを呼ばずに判断しようとしたら、調査を要求する。
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
                "sufficient": False, "reason": "未確認", "missing_information": ["本文"],
                "anchor_page_ids": [],
            })])
        if step == 2:
            assert "目次を開いて調査" in str(messages[-1].parts)
            return ModelResponse(parts=[ToolCallPart("browse_tree", {"node_id": "lec02-main-p052"})])
        if step == 3:
            data = json.loads(messages[-1].parts[0].content)
            assert "error" in data
            return ModelResponse(parts=[ToolCallPart("browse_tree", {})])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
            "sufficient": False, "reason": "目次を確認したが根拠を特定できない",
            "missing_information": ["本文"], "anchor_page_ids": [],
        })])

    checker, pages = hybrid.build_tree_checker()
    result = checker.run_sync("質問", model=FunctionModel(respond))
    assert not result.output.sufficient
    assert not pages
    assert step == 4
