"""
アプリケーション設定。
環境変数 → デフォルト値 の順で解決する。
"""
from __future__ import annotations

import datetime
import os

from dotenv import load_dotenv

load_dotenv()

# LLM
MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")

# リサーチエージェントがツールを呼べる最大回数
MAX_TOOL_LOOPS: int = int(os.getenv("MAX_TOOL_LOOPS", "3"))

# SQLiteチェックポイントDB（HITL用・再開に必要）
CHECKPOINT_DB_PATH: str = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.sqlite")

# デバッグログ出力フラグ
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 今日の日付（リサーチプロンプトで使用）
TODAY: str = datetime.date.today().isoformat()
