/**
 * バックエンド API クライアント。
 *
 * エンドポイント:
 *   POST /agent/invoke  - グラフの起動・再開（LangServe が自動生成）
 *   GET  /agent/status/{thread_id} - 現在ステップの取得（ポーリング用）
 */

import type { AgentResponse, StatusResponse } from "@/types/agent"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function invoke(input: Record<string, unknown>): Promise<AgentResponse> {
  const res = await fetch(`${API_BASE}/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // LangServe は { input: ... } で受け取る
    body: JSON.stringify({ input }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  const json = await res.json()
  // LangServe は { output: ... } で返す
  return json.output as AgentResponse
}

export function startAgent(theme: string, threadId: string): Promise<AgentResponse> {
  return invoke({ action: "start", theme, thread_id: threadId })
}

export function resumeAgent(
  threadId: string,
  decision: "y" | "n" | "retry"
): Promise<AgentResponse> {
  return invoke({ action: "resume", thread_id: threadId, decision })
}

export async function fetchStatus(threadId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/agent/status/${threadId}`)
  if (!res.ok) throw new Error(`status fetch failed: ${res.status}`)
  return res.json()
}
