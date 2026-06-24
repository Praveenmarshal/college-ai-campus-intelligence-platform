/**
 * pages/AnalyticsPage.jsx — Admin combined analytics + MongoDB NL query tool
 */
import React, { useState, useEffect } from 'react'
import { Database, Send, Loader2, BarChart3 } from 'lucide-react'
import { mongoQueryAPI } from '../api/services'
import { useTitle } from '../hooks/index'

export default function AnalyticsPage() {
  useTitle('Analytics')
  const [collections, setCollections] = useState({})
  const [collection, setCollection] = useState('students')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    mongoQueryAPI.collections().then(({ data }) => setCollections(data.data || {}))
  }, [])

  const ask = async () => {
    if (!question.trim()) return
    setLoading(true); setResult(null)
    try {
      const { data } = await mongoQueryAPI.ask({ question, collection })
      setResult(data.data)
    } catch (err) {
      setResult({ error: err?.response?.data?.error || 'Query failed' })
    } finally { setLoading(false) }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Analytics — Database Query Tool</h1>
        <p className="page-subtitle">Ask natural language questions directly against MongoDB collections</p>
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-4 h-4 text-primary-500" />
          <select value={collection} onChange={e => setCollection(e.target.value)} className="input w-48">
            {Object.keys(collections).map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <span className="text-xs text-gray-400">Fields: {collections[collection]?.join(', ')}</span>
        </div>

        <div className="flex gap-2">
          <input value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()}
            placeholder="e.g. Average CGPA per department" className="input flex-1" />
          <button onClick={ask} disabled={loading || !question.trim()} className="btn-primary px-4">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>

        {result?.error && <p className="text-sm text-red-500 mt-3">{result.error}</p>}

        {result?.results && (
          <div className="mt-4">
            <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
              <BarChart3 className="w-3.5 h-3.5" /> {result.result_count} result(s)
            </p>
            <div className="table-container">
              <table className="table text-xs">
                <thead>
                  <tr>{result.results[0] && Object.keys(result.results[0]).map(k => <th key={k}>{k}</th>)}</tr>
                </thead>
                <tbody>
                  {result.results.slice(0, 20).map((row, i) => (
                    <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
