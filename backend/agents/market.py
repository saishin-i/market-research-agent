"""
市場分析エージェント。

基礎レポートを元に SWOT 分析（強み・弱み・機会・脅威）を行う。
結果は analysis_messages に追記されるため、
以降の technical / report エージェントは全履歴を参照できる。
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
    ("system", "あなたは市場分析のプロです。レポートを元にSWOT分析を行ってください。"),
    MessagesPlaceholder(variable_name="analysis_messages"),
])
_chain = _prompt | model


def market_node(state: AgentState) -> Command[Literal["technical"]]:
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: market\n" + "-" * 40)

    response = _chain.invoke({"analysis_messages": state.get("analysis_messages", [])})
    return Command(
        update={"analysis_messages": [response], "current_step": "market"},
        goto="technical",
    )
