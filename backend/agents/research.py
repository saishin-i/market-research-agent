"""
リサーチエージェント。

2つのノードを定義する:
  - research_node : LLM にリサーチを依頼。ツール呼び出しが必要なら tools_node へ。
  - tools_node    : ツール（Web検索）を実行して結果を research_messages に追記。

「LLM → ツール → LLM → ツール → ...」という ReAct ループを
MAX_TOOL_LOOPS 回まで繰り返す。
"""
from __future__ import annotations

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from ..config import DEBUG_MODE, MAX_TOOL_LOOPS, MODEL_NAME, TODAY
from ..state import AgentState
from ..tools.search import build_tools

# --- モデルとツールのセットアップ ---
tools = build_tools()
model = ChatOpenAI(model=MODEL_NAME, temperature=0)
model_with_tools = model.bind_tools(tools)  # LLM がツール定義を認識できる状態にする

# LangGraph 組み込みのツール実行ノード
# messages_key でどのメッセージリストにツール結果を追記するか指定
tool_node = ToolNode(tools, messages_key="research_messages")

# --- プロンプト ---
_prompt = ChatPromptTemplate.from_messages([
    ("system", f"""あなたは事業リサーチ担当です。ユーザーのテーマについて、\
市場規模・主要プレイヤー・技術課題などをWeb検索で調査してください。
今日は {TODAY} です。新しい情報が必要なら新しい情報を優先してください。

【出典ルール】
- ツール出力にある "source: URL" を根拠として使うときのみ本文中に [n] を付ける。
- 末尾に参照一覧（[n] URL）を付ける。
- 存在しない出典は作らない。"""),
    MessagesPlaceholder(variable_name="research_messages"),
])
_chain = _prompt | model_with_tools


# --- ノード関数 ---
def research_node(state: AgentState) -> Command[Literal["tools", "summary"]]:
    """
    LLM にリサーチを依頼するノード。

    LLM がツール呼び出しを返した場合 → tools_node へ
    それ以外（調査完了と判断）         → summary_node へ
    """
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: research\n" + "-" * 40)

    response = _chain.invoke({"research_messages": state.get("research_messages", [])})
    loop_count = state.get("loop_count", 0)
    update = {"research_messages": [response], "current_step": "research"}

    if getattr(response, "tool_calls", None) and loop_count < MAX_TOOL_LOOPS:
        return Command(update=update, goto="tools")

    return Command(update=update, goto="summary")


def tools_node(state: AgentState) -> Command[Literal["research"]]:
    """
    Web検索を実行するノード。

    ToolNode が tool_calls を読み取り・実行・結果を ToolMessage として返す。
    loop_count をインクリメントして research_node に戻る。
    """
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: tools\n" + "-" * 40)

    result = tool_node.invoke({"research_messages": state.get("research_messages", [])})
    last = result["research_messages"][-1]
    text = last.content if isinstance(last.content, str) else str(last.content)
    if DEBUG_MODE:
        print(f"Tool output (先頭300文字): {text[:300]}")

    return Command(
        update={
            "research_messages": result["research_messages"],
            "loop_count": state.get("loop_count", 0) + 1,
            "current_step": "tools",
        },
        goto="research",
    )
