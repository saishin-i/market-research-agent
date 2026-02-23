/**
 * 人間承認（HITL）カード。
 *
 * バックエンドの interrupt() が発生したときに表示される。
 * ユーザーが y / retry / n を選択すると、
 * バックエンドに resume リクエストが送られてグラフが再開する。
 */
import type { ApprovalPayload } from "@/types/agent"

interface Props {
  payload: ApprovalPayload
  onDecision: (decision: "y" | "n" | "retry") => void
  disabled: boolean
}

export function ApprovalCard({ payload, onDecision, disabled }: Props) {
  return (
    <section className="rounded-xl bg-gray-900 border border-yellow-700/50 p-6 space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-yellow-400 text-lg">⏸</span>
        <h2 className="font-semibold text-yellow-400">承認待ち（Human-in-the-Loop）</h2>
      </div>

      <p className="text-gray-300">{payload.question}</p>

      {/* 分析プレビュー */}
      {payload.analysis_preview.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400">ここまでの分析（最新3件）</h3>
          {payload.analysis_preview.map((msg, i) => (
            <details key={i} className="rounded-lg bg-gray-800 border border-gray-700">
              <summary className="px-4 py-2.5 cursor-pointer text-sm text-gray-300
                                 flex items-center justify-between">
                <span className="font-medium">{msg.type}</span>
                <span className="text-gray-500 text-xs truncate max-w-xs ml-3">
                  {msg.content.slice(0, 80)}…
                </span>
              </summary>
              <pre className="px-4 py-3 text-xs text-gray-400 whitespace-pre-wrap
                             border-t border-gray-700 max-h-60 overflow-y-auto">
                {msg.content}
              </pre>
            </details>
          ))}
        </div>
      )}

      {/* 承認ボタン */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={() => onDecision("y")}
          disabled={disabled}
          className="px-5 py-2 bg-green-700 hover:bg-green-600
                     disabled:opacity-50 disabled:cursor-not-allowed
                     rounded-lg font-medium text-sm transition-colors"
        >
          承認してレポート生成（y）
        </button>
        <button
          onClick={() => onDecision("retry")}
          disabled={disabled}
          className="px-5 py-2 bg-yellow-700 hover:bg-yellow-600
                     disabled:opacity-50 disabled:cursor-not-allowed
                     rounded-lg font-medium text-sm transition-colors"
        >
          市場分析からやり直し（retry）
        </button>
        <button
          onClick={() => onDecision("n")}
          disabled={disabled}
          className="px-5 py-2 bg-gray-700 hover:bg-gray-600
                     disabled:opacity-50 disabled:cursor-not-allowed
                     rounded-lg font-medium text-sm transition-colors"
        >
          却下（n）
        </button>
      </div>
    </section>
  )
}
