"""
グラフの組み立てと API 向けヘルパー関数。

このファイルの責務は「どのノードをどう繋ぐか」だけ。
各ノードの実装は agents/ 以下に分離してある。

グラフ構造:
  START
    └─ research ─┬─(ツール呼び出しあり)─▶ tools ─▶ research（ループ）
                 └─(調査完了)───────────▶ summary
                                              └─▶ market
                                                    └─▶ technical
                                                          └─▶ approval ─┬─(y)─▶ report ─▶ END
                                                                         ├─(retry)─▶ market
                                                                         └─(n)─▶ END
"""
from __future__ import annotations

import sqlite3
import uuid

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from .agents.market import market_node
from .agents.report import approval_node, report_node
from .agents.research import research_node, tools_node
from .agents.summary import summary_node
from .agents.technical import technical_node
from .config import CHECKPOINT_DB_PATH
from .state import AgentState

# --- グラフ組み立て ---
_builder = StateGraph(AgentState)

_builder.add_node("research", research_node)
_builder.add_node("tools", tools_node)
_builder.add_node("summary", summary_node)
_builder.add_node("market", market_node)
_builder.add_node("technical", technical_node)
_builder.add_node("approval", approval_node)
_builder.add_node("report", report_node)

_builder.add_edge(START, "research")
_builder.add_edge("report", END)

# --- チェックポインター（SQLite永続化） ---
# interrupt() でグラフを一時停止したとき、状態を SQLite に保存する。
# resume 時にこの状態を復元することで、中断した地点から再開できる。
_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
_conn.execute("PRAGMA journal_mode=WAL;")    # 並行書き込み耐性を上げる
_conn.execute("PRAGMA synchronous=NORMAL;")  # パフォーマンスと安全性のバランス
_conn.execute("PRAGMA busy_timeout=5000;")   # ロック競合時の待機時間(ms)

_checkpointer = SqliteSaver(_conn)
_checkpointer.setup()  # チェックポイントテーブルを初期化

graph = _builder.compile(checkpointer=_checkpointer)


# --- API向けヘルパー ---
def _serialize(result: dict) -> dict:
    """
    graph.invoke() の戻り値を JSON シリアライズ可能な dict に変換する。

    interrupt が発生している場合は "interrupted" ステータスを返す。
    完了している場合は最終レポートと全メッセージ履歴を返す。
    """
    interrupts = result.get("__interrupt__")
    if interrupts:
        first = interrupts[0] if isinstance(interrupts, (list, tuple)) else interrupts
        payload = getattr(first, "value", first)
        return {"status": "interrupted", "interrupt": payload}

    msgs = result.get("analysis_messages", [])
    serialized = [
        {
            "type": type(m).__name__,
            "content": m.content if isinstance(m.content, str) else str(m.content),
        }
        for m in msgs
    ]
    report = serialized[-1]["content"] if serialized else ""

    return {
        "status": "completed",
        "report": report,
        "analysis_messages": serialized,
    }


def new_thread_id() -> str:
    """セッションを識別するユニーク ID を発行する。"""
    return str(uuid.uuid4())


def run_start(theme: str, thread_id: str) -> dict:
    """新規テーマでグラフを起動する。"""
    initial: dict = {
        "research_messages": [HumanMessage(content=f"テーマ: {theme}")],
        "loop_count": 0,
        "analysis_messages": [],
    }
    config = {"configurable": {"thread_id": thread_id}}
    raw = graph.invoke(initial, config=config)
    return _serialize(raw)


def run_resume(decision: str, thread_id: str) -> dict:
    """interrupt で停止中のグラフをユーザー判断で再開する。"""
    config = {"configurable": {"thread_id": thread_id}}
    raw = graph.invoke(Command(resume=decision), config=config)
    return _serialize(raw)


def close_db() -> None:
    """アプリ終了時に SQLite 接続を閉じる。"""
    try:
        _conn.close()
    except Exception:
        pass
