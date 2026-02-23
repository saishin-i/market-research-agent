"""
Web検索ツール（Tavily）。

LangChain の @tool デコレータで定義することで、
LLM が「どんなツールか・引数は何か」を理解して呼び出せるようになる。

TAVILY_API_KEY が未設定の場合はダミー関数を返し、
アプリ自体は起動できる状態を保つ。
"""
from __future__ import annotations

import os

from langchain_core.tools import tool


def _format_results(response: object) -> str:
    """Tavily のレスポンス dict を読みやすいテキストに整形する。"""
    if not isinstance(response, dict):
        return f"（検索結果の形式が想定外）\nraw: {response!r}"

    results = response.get("results") or []
    if not results:
        return "（検索結果なし）"

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        if not isinstance(r, dict):
            continue
        title = (r.get("title") or "").strip()
        content = (r.get("content") or r.get("raw_content") or "").strip()
        # プロンプトが長くなりすぎないよう上限を設ける
        if len(content) > 900:
            content = content[:900] + "…"
        url = (r.get("url") or "").strip()
        lines.append(f"[{i}] {title}\n{content}\nsource: {url}")

    return "\n\n".join(lines) if lines else "（検索結果なし）"


def build_tools() -> list:
    """環境変数に応じてツールリストを組み立てて返す。"""
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not tavily_key:
        @tool
        def web_search(query: str) -> str:
            """Web検索。TAVILY_API_KEY が未設定のため実行できません。"""
            return "（TAVILY_API_KEY が未設定のため Web検索を実行できません）"

        return [web_search]

    from langchain_tavily import TavilySearch

    _client = TavilySearch(max_results=3, search_depth="basic")

    @tool
    def web_search(query: str) -> str:
        """Web検索（Tavily）。上位結果を整形して返す。"""
        try:
            return _format_results(_client.invoke({"query": query}))
        except Exception as e:
            return f"（検索エラー）{type(e).__name__}: {e}"

    return [web_search]
