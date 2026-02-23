interface Props {
  value: string
  onChange: (v: string) => void
  onSubmit: () => void
  disabled: boolean
}

export function ThemeInput({ value, onChange, onSubmit, disabled }: Props) {
  return (
    <section className="rounded-xl bg-gray-900 border border-gray-800 p-6">
      <label htmlFor="theme" className="block text-sm font-medium text-gray-300 mb-3">
        リサーチテーマ
      </label>
      <div className="flex gap-3">
        <input
          id="theme"
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            // IME変換中（日本語入力中）はEnterを無視する
            if (e.nativeEvent.isComposing) return
            if (e.key === "Enter" && !disabled && value.trim()) onSubmit()
          }}
          placeholder="例: 宇宙ゴミの回収事業"
          disabled={disabled}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5
                     text-white placeholder-gray-500
                     focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500
                     disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed
                     rounded-lg font-medium transition-colors"
        >
          実行
        </button>
      </div>
      <p className="mt-2 text-xs text-gray-500">Enter で実行</p>
    </section>
  )
}
