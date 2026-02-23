"""
LangGraph が管理するグラフ全体の状態（State）。

TypedDict で定義することで、各ノードがどのキーを読み書きするか
型として明示できる。

add_messages アノテーション:
  ノードが {"research_messages": [新メッセージ]} を返すと、
  LangGraph が既存リストに追記（append）してくれる。
  通常の TypedDict では上書きになるところを、
  add_messages が「追記」の挙動に変える reducer として機能する。
"""
from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # リサーチフェーズのメッセージ履歴（LLM↔ツールのやり取り）
    research_messages: Annotated[list[BaseMessage], add_messages]

    # 分析フェーズのメッセージ履歴（サマリー→SWOT→技術→レポート）
    analysis_messages: Annotated[list[BaseMessage], add_messages]

    # リサーチエージェントがツールを呼んだ回数（ループ上限管理用）
    loop_count: int

    # UIに現在どのステップを実行中か伝えるための文字列
    current_step: str

    # 人間承認ノードでのユーザー選択（"y" / "n" / "retry"）
    approval_decision: str

    # report_agent が生成した最終レポートテキスト
    final_report: str
