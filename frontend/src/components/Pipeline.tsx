/**
 * パイプライン進捗コンポーネント。
 *
 * バックエンドのポーリング結果（current_step）を受け取り、
 * 各ステップの状態（完了 / 実行中 / 未実行）を視覚的に表示する。
 */
import { PIPELINE_STEPS, type StepKey } from "@/types/agent"

interface Props {
  currentStep: StepKey | null
}

type StepStatus = "done" | "active" | "pending"

function getStepStatus(stepKey: string, currentStep: StepKey | null): StepStatus {
  if (!currentStep) return "pending"

  const stepKeys = PIPELINE_STEPS.map((s) => s.key)
  const currentIdx = stepKeys.indexOf(currentStep)
  const stepIdx = stepKeys.indexOf(stepKey as StepKey)

  if (stepIdx < currentIdx) return "done"
  if (stepIdx === currentIdx) return "active"
  return "pending"
}

const STATUS_STYLES: Record<StepStatus, string> = {
  done:    "bg-green-500 text-white border-green-500",
  active:  "bg-blue-500 text-white border-blue-500 animate-pulse",
  pending: "bg-gray-800 text-gray-500 border-gray-700",
}

const LABEL_STYLES: Record<StepStatus, string> = {
  done:    "text-green-400",
  active:  "text-blue-400 font-semibold",
  pending: "text-gray-500",
}

export function Pipeline({ currentStep }: Props) {
  return (
    <section className="rounded-xl bg-gray-900 border border-gray-800 p-6">
      <div className="flex items-center gap-2 mb-4">
        {/* スピナー */}
        <svg className="animate-spin h-4 w-4 text-blue-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <h2 className="text-sm font-medium text-gray-300">処理中...</h2>
      </div>

      <ol className="space-y-2">
        {PIPELINE_STEPS.map((step) => {
          const status = getStepStatus(step.key, currentStep)
          return (
            <li key={step.key} className="flex items-center gap-3">
              {/* ステップアイコン */}
              <span className={`
                w-7 h-7 rounded-full border-2 flex items-center justify-center
                text-xs font-bold flex-shrink-0 transition-all duration-300
                ${STATUS_STYLES[status]}
              `}>
                {status === "done" ? "✓" : ""}
              </span>

              {/* ラベル */}
              <span className={`text-sm transition-colors duration-300 ${LABEL_STYLES[status]}`}>
                {step.label}
                <span className="ml-2 text-xs text-gray-600">{step.description}</span>
              </span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
