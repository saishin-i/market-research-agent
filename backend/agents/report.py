"""
承認ノード + レポート生成エージェント。

approval_node:
  LangGraph の interrupt() を使って処理を一時停止し、
  ユーザーの判断（y / n / retry）を待つ。
  これが HITL（Human-in-the-Loop）の核心。

  interrupt() が呼ばれると:
    1. グラフの実行が止まり、状態が SQLite に保存される
    2. API は "interrupted" ステータスをクライアントに返す
    3. クライアントが /resume を呼ぶと、interrupt() の戻り値としてユーザー入力が届く

report_node:
  承認（y）された場合のみ最終レポートを生成する。
"""
from __future__ import annotations

from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import Command, interrupt

from ..config import DEBUG_MODE, MODEL_NAME
from ..state import AgentState

model = ChatOpenAI(model=MODEL_NAME, temperature=0)

_report_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "これまでの議論を統合し、投資家向けの具体的な事業プランを作成してください。\n"
     "文末での質問や提案は禁止です。「以上」で終わらせてください。"),
    MessagesPlaceholder(variable_name="analysis_messages"),
])
_report_chain = _report_prompt | model


def _safe_preview(messages: list[BaseMessage], limit: int = 3) -> list[dict]:
    """analysis_messages の末尾 limit 件を JSON シリアライズ可能な形式に変換する。"""
    tail = messages[-limit:] if messages else []
    result = []
    for m in tail:
        s = m.content if isinstance(m.content, str) else str(m.content)
        result.append({
            "type": type(m).__name__,
            "content": s[:1200] + "…" if len(s) > 1200 else s,
        })
    return result


def approval_node(
    state: AgentState,
) -> Command[Literal["market", "report", "__end__"]]:
    """
    HITL 承認ノード。

    interrupt(payload) でグラフを一時停止する。
    payload はクライアントに "interrupted" レスポンスとして返される。
    resume 時に届くユーザー入力（y/n/retry）で次のノードを決定する。
    """
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: approval\n" + "-" * 40)

    payload = {
        "kind": "approval_request",
        "question": "ここまでの議論を承認してレポートを作成しますか？",
        "options": ["y", "n", "retry"],
        "analysis_preview": _safe_preview(state.get("analysis_messages", [])),
    }

    # ここでグラフが停止し、SQLite に状態が保存される
    raw = interrupt(payload)

    decision = raw.strip().lower() if isinstance(raw, str) else str(raw).strip().lower()
    if decision not in ("y", "n", "retry"):
        decision = "n"

    if DEBUG_MODE:
        print(f"🐛 [DEBUG] Approval decision: {decision!r}\n" + "-" * 40)

    update = {"approval_decision": decision, "current_step": "approval"}

    if decision == "y":
        return Command(update=update, goto="report")
    if decision == "retry":
        return Command(update=update, goto="market")
    return Command(update=update, goto=END)


def report_node(state: AgentState) -> Command[Literal["__end__"]]:
    """最終レポートを生成して final_report に保存する。"""
    if DEBUG_MODE:
        print("\n🐛 [DEBUG] Node: report\n" + "-" * 40)

    if (state.get("approval_decision") or "").strip().lower() != "y":
        return Command(update={"final_report": "", "current_step": "done"}, goto=END)

    response = _report_chain.invoke({"analysis_messages": state.get("analysis_messages", [])})
    text = response.content if isinstance(response.content, str) else str(response.content)

    return Command(
        update={"analysis_messages": [response], "final_report": text, "current_step": "done"},
        goto=END,
    )
