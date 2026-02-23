"""
技術評価エージェント（CTO視点）。

市場分析の結果を踏まえ、事業の技術的課題・実現可能性を評価する。
このエージェントの後に人間承認ノードが入り、ユーザーが内容を確認できる。
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
    ("system", "あなたは技術のCTOです。市場分析を踏まえ、技術的課題と実現性を指摘してください。"),
    MessagesPlaceholder(variable_name="analysis_messages"),
])
_chain = _prompt | model


def technical_node(state: AgentState) -> Command[Literal["approval"]]:
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: technical\n" + "-" * 40)

    response = _chain.invoke({"analysis_messages": state.get("analysis_messages", [])})
    return Command(
        update={"analysis_messages": [response], "current_step": "technical"},
        goto="approval",
    )
