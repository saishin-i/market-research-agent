"""
FastAPI サーバー。

エンドポイント: POST /agent/invoke
  LangServe が自動生成するエンドポイント。
  リクエスト形式: { "input": { "action": "start"|"resume", ... } }

起動コマンド（プロジェクトルートから）:
  uvicorn backend.server:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables import RunnableLambda
from langserve import add_routes
from pydantic import BaseModel, Field

from .graph import close_db, new_thread_id, run_resume, run_start


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_db()  # シャットダウン時に SQLite 接続を閉じる


app = FastAPI(title="Market Research Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では接続元を絞ること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- スキーマ ---
class AgentRequest(BaseModel):
    action: Literal["start", "resume"] = Field(..., description="start: 新規 / resume: 再開")
    thread_id: Optional[str] = Field(None, description="resume 時に必要なセッションID")
    theme: Optional[str] = Field(None, description="start 時のリサーチテーマ")
    decision: Optional[str] = Field(None, description="resume 時のユーザー判断（y/n/retry）")


# --- ハンドラー ---
def _handle(req: AgentRequest | dict) -> dict:
    if isinstance(req, dict):
        req = AgentRequest(**req)

    tid = req.thread_id or new_thread_id()
    print(f"[server] action={req.action} thread_id={tid}")

    if req.action == "start":
        theme = req.theme or "宇宙ゴミの回収事業"
        data = run_start(theme=theme, thread_id=tid)
    else:
        decision = (req.decision or "").strip().lower()
        data = run_resume(decision=decision, thread_id=tid)

    return {"thread_id": tid, **data}


# LangServe が /agent/invoke などのエンドポイントを自動生成する
runnable = RunnableLambda(_handle).with_types(input_type=AgentRequest, output_type=dict)
add_routes(app, runnable, path="/agent")
