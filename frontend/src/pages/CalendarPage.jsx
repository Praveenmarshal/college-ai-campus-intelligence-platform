import React, { useState } from 'react'
import { Calendar, Send, Loader2 } from 'lucide-react'
import { routerAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import ReactMarkdown from 'react-markdown'

export default function CalendarPage() {
  useTitle('Academic Calendar')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const ask = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const { data } = await routerAPI.ask({ query })
      setResult(data.data)
    } catch { /* handled globally */ }
    finally { setLoading(false) }
  }

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Academic Calendar</h1>
        <p className="page-subtitle">Ask about semester dates, holidays, and exam schedules</p>
      </div>
      <div className="card p-5">
        <div className="flex gap-2">
          <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()}
            placeholder="e.g. When does the next semester start?" className="input flex-1" />
          <button onClick={ask} disabled={loading || !query.trim()} className="btn-primary px-4">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        {result && <div className="mt-4 chat-bubble-ai max-w-none"><ReactMarkdown>{result.answer}</ReactMarkdown></div>}
        <p className="text-2xs text-gray-400 mt-3">Tip: Upload the academic calendar PDF via Admin → Upload PDF for accurate answers.</p>
      </div>
    </div>
  )
}
