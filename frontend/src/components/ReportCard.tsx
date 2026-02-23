/**
 * 最終レポート表示カード。
 *
 * 承認後にバックエンドが生成した投資家向けレポートを表示する。
 * コピーとテキストファイルダウンロード機能付き。
 */
"use client"

import { useState } from "react"

interface Props {
  report: string
  theme: string
  onReset: () => void
}

export function ReportCard({ report, theme, onReset }: Props) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(report)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleDownload() {
    const date = new Date()
    const yyyymmdd = date.toISOString().slice(0, 10).replace(/-/g, "")
    const safeTheme = theme.replace(/[\\/:*?"<>|]/g, "_").slice(0, 40)
    const filename = `report_${yyyymmdd}_${safeTheme || "theme"}.txt`
    const blob = new Blob([report], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const isEmpty = !report.trim()

  return (
    <section className="rounded-xl bg-gray-900 border border-gray-800 p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="text-green-400">✓</span>
          <h2 className="font-semibold text-gray-100">
            {isEmpty ? "処理完了（レポートなし）" : "最終レポート"}
          </h2>
        </div>
        <div className="flex gap-2">
          {!isEmpty && (
            <>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700
                           border border-gray-700 rounded-lg transition-colors"
              >
                {copied ? "コピー済み ✓" : "コピー"}
              </button>
              <button
                onClick={handleDownload}
                className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700
                           border border-gray-700 rounded-lg transition-colors"
              >
                .txt で保存
              </button>
            </>
          )}
          <button
            onClick={onReset}
            className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700
                       border border-gray-700 rounded-lg transition-colors"
          >
            新しいテーマ
          </button>
        </div>
      </div>

      {isEmpty ? (
        <p className="text-gray-500 text-sm">却下またはレポートが生成されませんでした。</p>
      ) : (
        <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed
                        max-h-[60vh] overflow-y-auto
                        bg-gray-950 border border-gray-800 rounded-lg p-4">
          {report}
        </pre>
      )}
    </section>
  )
}
