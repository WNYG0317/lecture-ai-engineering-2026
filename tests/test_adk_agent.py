"""ADK 版の登録・ツール実行を検証する。LLM や API キーは使わない。

uv run --extra adk pytest -q tests/test_adk_agent.py で実行する。
ADK の追加依存を入れていない環境では、このファイルだけスキップする。
"""

import asyncio
import json

import pytest

pytest.importorskip("google.adk")

from google.adk.tools import FunctionTool

from adk_agent.glossary_agent.agent import root_agent
from app import tools
from app.agent import INSTRUCTIONS


def test_adk_agent_registers_existing_tools():
    assert root_agent.name == "glossary_agent"
    assert root_agent.model == "gemini-3.5-flash-lite"
    assert root_agent.instruction == INSTRUCTIONS
    assert root_agent.tools == [
        tools.search_glossary, tools.related_knowledge, tools.get_lecture_summary
    ]


@pytest.mark.parametrize(
    "function,args",
    [
        (tools.search_glossary, {"query": "LoRA"}),
        (tools.related_knowledge, {"term": "LoRA"}),
        (tools.get_lecture_summary, {"lecture": 3}),
    ],
)
def test_adk_function_tools_execute(function, args):
    tool = FunctionTool(function)
    declaration = tool._get_declaration()
    assert declaration.name == function.__name__
    assert declaration.description
    result = asyncio.run(tool.run_async(args=args, tool_context=None))
    assert result == function(**args)
    if function is tools.related_knowledge:
        payload = json.loads(result)
        assert payload["category"] == "ファインチューニング"
        assert payload["related_terms"]
