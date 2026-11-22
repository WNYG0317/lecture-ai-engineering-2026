"""Google ADK で作る AIE2026 の用語集・学習支援エージェント。

使い方（リポジトリのルートで実行）:
    uv sync --frozen --extra adk --python 3.12
    uv run --extra adk adk run adk_agent/glossary_agent
    uv run --extra adk adk web adk_agent

GEMINI_API_KEY（または GOOGLE_API_KEY）を環境変数に設定してから起動する。
モデルは gemini-3.5-flash-lite を使う。指示文は app.agent の INSTRUCTIONS を共用する。
ADK は root_agent を読み込み、モデルの要求に応じて Python 関数をツールとして
実行する。app.tools を再利用し、用語検索・カテゴリによる関連知識・講義の要点を
提供する。関連知識の意味検索は行わない。
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS

# ADK の CLI / Web UI が読み込むエントリーポイント。
# 関数の docstring と型ヒントから、モデルに渡す説明文と引数の定義が作られる。
root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.related_knowledge, tools.get_lecture_summary],
)
