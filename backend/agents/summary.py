"""
サマリーエージェント。

リサーチフェーズで蓄積した research_messages（LLM↔ツールのやり取り）を
読みやすい「基礎レポート」に整理する。

このノードの出力は analysis_messages の最初のメッセージになる。
以降の market / technical / report エージェントはこの analysis_messages を積み重ねていく。
"""
from __future__ import annotations

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from ..config import DEBUG_MODE, MODEL_NAME
from ..state import AgentState

model = ChatOpenAI(model=MODEL_NAME, temperature=0)

_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "あなたは優秀な書記です。以下の「調査ログ」を要約し、"
     "市場分析チームが使える基礎レポートを作成してください。\n"
     "断定的な事実には可能な限り [n] を付け、末尾に参照一覧（[n] URL）を付けてください。"
     "存在しない出典は作らない。\n"
     "ツール出力に含まれる source: URL だけを参照として扱ってください。"),
    ("human", "以下が調査ログです:"),
    MessagesPlaceholder(variable_name="research_messages"),
    ("human", "上記を元に、市場分析のための基礎レポートを作成してください。"),
])
_chain = _prompt | model


def summary_node(state: AgentState) -> Command[Literal["market"]]:
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: summary\n" + "-" * 40)

    response = _chain.invoke({"research_messages": state.get("research_messages", [])})
    return Command(
        update={
            "analysis_messages": [response],
            "loop_count": 0,  # 次フェーズに備えてリセット
            "current_step": "summary",
        },
        goto="market",
    )
