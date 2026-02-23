// アプリ全体の状態
export type AppStatus =
  | "idle"              // 初期状態
  | "loading"           // 実行中（start）
  | "resuming"          // 再開中（resume）
  | "waiting_approval"  // 人間承認待ち（HITL）
  | "completed"         // 完了
  | "cancelled"         // 却下
  | "error"             // エラー

// パイプラインのステップ定義
export const PIPELINE_STEPS = [
  { key: "research",  label: "リサーチ",   description: "Web検索で情報収集" },
  { key: "tools",     label: "Web検索",    description: "Tavily で検索実行" },
  { key: "summary",   label: "サマリー",   description: "調査ログを整理" },
  { key: "market",    label: "市場分析",   description: "SWOT 分析" },
  { key: "technical", label: "技術評価",   description: "CTO 視点でレビュー" },
  { key: "approval",  label: "承認待ち",   description: "内容を確認・承認" },
  { key: "report",    label: "レポート",   description: "投資家向けレポート生成" },
] as const

export type StepKey = (typeof PIPELINE_STEPS)[number]["key"]

// バックエンド API のレスポンス型
export interface ApprovalPayload {
  kind: string
  question: string
  options: string[]
  analysis_preview: Array<{ type: string; content: string }>
}

export interface AgentResponse {
  thread_id: string
  status: "interrupted" | "completed"
  interrupt?: ApprovalPayload
  report?: string
  analysis_messages?: Array<{ type: string; content: string }>
}

export interface StatusResponse {
  current_step: StepKey | null
  is_interrupted: boolean
}
