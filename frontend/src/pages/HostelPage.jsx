import React, { useState } from 'react'
import { Home, Send, Loader2 } from 'lucide-react'
import { routerAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import ReactMarkdown from 'react-markdown'

export default function HostelPage() {
  useTitle('Hostel')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const ask = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const { data } = await routerAPI.ask({ query, context: { collection: 'hostel' } })
      setResult(data.data)
    } catch { /* handled globally */ }
    finally { setLoading(false) }
  }

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Hostel Assistant</h1>
        <p className="page-subtitle">Room allocation, vacancy, and hostel queries</p>
      </div>
      <div className="card p-5">
        <div className="flex gap-2">
          <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()}
            placeholder="e.g. How many vacancies in Block A?" className="input flex-1" />
          <button onClick={ask} disabled={loading || !query.trim()} className="btn-primary px-4">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        {result && <div className="mt-4 chat-bubble-ai max-w-none"><ReactMarkdown>{result.answer}</ReactMarkdown></div>}
      </div>
    </div>
  )
}
