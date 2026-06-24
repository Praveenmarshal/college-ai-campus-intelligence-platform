import React, { useState } from 'react'
import { Library, Search, BookOpen, Send, Loader2 } from 'lucide-react'
import { routerAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import ReactMarkdown from 'react-markdown'

export default function LibraryPage() {
  useTitle('Library')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const { data } = await routerAPI.ask({ query, context: { collection: 'library' } })
      setResult(data.data)
    } catch { /* handled globally */ }
    finally { setLoading(false) }
  }

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Library Assistant</h1>
        <p className="page-subtitle">Search books, check availability, and ask about fines</p>
      </div>

      <div className="card p-5">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()}
              placeholder="e.g. Is 'Clean Code' available?" className="input pl-9" />
          </div>
          <button onClick={search} disabled={loading || !query.trim()} className="btn-primary px-4">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>

        {result && (
          <div className="mt-4 chat-bubble-ai max-w-none">
            <ReactMarkdown>{result.answer}</ReactMarkdown>
            {result.data?.books?.length > 0 && (
              <div className="mt-3 space-y-2">
                {result.data.books.map(b => (
                  <div key={b._id} className="flex items-center gap-2 text-xs p-2 bg-gray-50 dark:bg-dark-700 rounded-lg">
                    <BookOpen className="w-3.5 h-3.5 text-primary-500" />
                    <span className="font-medium">{b.title}</span> — {b.author}
                    <span className="ml-auto badge-neutral">{b.available_copies}/{b.total_copies} available</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
