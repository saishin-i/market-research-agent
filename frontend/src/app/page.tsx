"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { fetchStatus, resumeAgent, startAgent } from "@/lib/api"
import { ApprovalCard } from "@/components/ApprovalCard"
import { Pipeline } from "@/components/Pipeline"
import { ReportCard } from "@/components/ReportCard"
import { ThemeInput } from "@/components/ThemeInput"
import type { ApprovalPayload, AppStatus, StepKey } from "@/types/agent"

// ポーリング間隔（ms）
const POLL_INTERVAL = 2000

// ブラウザ側で thread_id を生成する
// バックエンドに invoke を呼ぶ前に ID を決めておくことで、
// 実行中もポーリングで同じスレッドの状態を取得できる
function generateThreadId(): string {
  return crypto.randomUUID()
}

export default function Home() {
  const [status, setStatus] = useState<AppStatus>("idle")
  const [theme, setTheme] = useState("")
  const [threadId, setThreadId] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState<StepKey | null>(null)
  const [approval, setApproval] = useState<ApprovalPayload | null>(null)
  const [report, setReport] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // ポーリング用タイマーの ref（クリーンアップに使う）
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ポーリング開始: 2秒ごとに GET /agent/status/{thread_id} を叩く
  const startPolling = useCallback((tid: string) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const s = await fetchStatus(tid)
        if (s.current_step) setCurrentStep(s.current_step)
      } catch {
        // ポーリングエラーは無視（メインリクエストのエラーを優先）
      }
    }, POLL_INTERVAL)
  }, [])

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  // アンマウント時にポーリングを止める
  useEffect(() => () => stopPolling(), [stopPolling])

  async function handleStart() {
    if (!theme.trim()) return

    const tid = generateThreadId()
    setThreadId(tid)
    setStatus("loading")
    setCurrentStep(null)
    setApproval(null)
    setReport(null)
    setError(null)

    // invoke が返るまでの間、ポーリングでステップを更新し続ける
    startPolling(tid)

    try {
      const res = await startAgent(theme, tid)
      stopPolling()

      if (res.status === "interrupted" && res.interrupt) {
        setApproval(res.interrupt)
        setCurrentStep("approval")
        setStatus("waiting_approval")
      } else {
        setCurrentStep("report")
        setReport(res.report ?? "")
        setStatus("completed")
      }
    } catch (e) {
      stopPolling()
      setError(String(e))
      setStatus("error")
    }
  }

  async function handleDecision(decision: "y" | "n" | "retry") {
    if (!threadId) return

    // 却下はバックエンドに送らずフロント側で完結
    if (decision === "n") {
      setStatus("cancelled")
      setReport("")
      return
    }

    setStatus("resuming")
    setApproval(null)
    setError(null)
    startPolling(threadId)

    try {
      const res = await resumeAgent(threadId, decision)
      stopPolling()

      if (res.status === "interrupted" && res.interrupt) {
        setApproval(res.interrupt)
        setCurrentStep("approval")
        setStatus("waiting_approval")
      } else {
        setCurrentStep("report")
        setReport(res.report ?? "")
        setStatus("completed")
      }
    } catch (e) {
      stopPolling()
      setError(String(e))
      setStatus("error")
    }
  }

  function handleReset() {
    stopPolling()
    setStatus("idle")
    setTheme("")
    setThreadId(null)
    setCurrentStep(null)
    setApproval(null)
    setReport(null)
    setError(null)
  }

  const isRunning = status === "loading" || status === "resuming"
  const isBlocked = isRunning || status === "waiting_approval"

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-6">

        {/* ヘッダー */}
        <header>
          <h1 className="text-3xl font-bold tracking-tight">Market Research Agent</h1>
          <p className="mt-2 text-gray-400">
            AI エージェントが事業テーマを調査し、投資家向けレポートを自動生成します。
          </p>
        </header>

        {/* テーマ入力 */}
        <ThemeInput
          value={theme}
          onChange={setTheme}
          onSubmit={handleStart}
          disabled={isBlocked}
        />

        {/* パイプライン進捗（処理中のみ表示） */}
        {isRunning && (
          <Pipeline currentStep={currentStep} />
        )}

        {/* エラー */}
        {error && (
          <div className="rounded-xl bg-red-900/30 border border-red-700/50 p-4 text-red-300 text-sm">
            <strong className="block mb-1">エラーが発生しました</strong>
            {error}
          </div>
        )}

        {/* 承認カード（HITL） */}
        {status === "waiting_approval" && approval && (
          <ApprovalCard
            payload={approval}
            onDecision={handleDecision}
            disabled={false}
          />
        )}

        {/* 最終レポート */}
        {(status === "completed" || status === "cancelled") && report !== null && (
          <ReportCard
            report={report}
            theme={theme}
            onReset={handleReset}
          />
        )}

      </div>
    </main>
  )
}
