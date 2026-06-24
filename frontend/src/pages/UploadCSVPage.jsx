/**
 * pages/UploadCSVPage.jsx — Phase 5
 */
import React, { useState } from 'react'
import { FileSpreadsheet, CheckCircle2, MessageSquareText, Send, Loader2 } from 'lucide-react'
import FileDropzone from '../components/common/FileDropzone'
import { documentsAPI } from '../api/services'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function UploadCSVPage() {
  useTitle('Upload CSV')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [queryResult, setQueryResult] = useState(null)

  const handleUpload = async (file) => {
    setUploading(true); setProgress(0); setResult(null); setQueryResult(null)
    try {
      const { data } = await documentsAPI.uploadCSV(file, { description }, setProgress)
      setResult(data.data)
      toast.success(data.message || 'CSV processed')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Upload failed')
    } finally { setUploading(false) }
  }

  const handleQuery = async () => {
    if (!question.trim() || !result) return
    setQuerying(true)
    try {
      const { data } = await apiClient.post(`/api/csv/${result.document.id}/query`, { question })
      setQueryResult(data.data)
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Query failed')
    } finally { setQuerying(false) }
  }

  const profile = result?.result?.profile

  return (
    <div className="page-container max-w-3xl">
      <div className="page-header">
        <h1 className="page-title">Upload CSV Dataset</h1>
        <p className="page-subtitle">Profile your data and ask natural language questions about it</p>
      </div>

      {!result && (
        <div className="card p-6 space-y-4">
          <div>
            <label className="label">Description <span className="text-gray-400 font-normal">(optional)</span></label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2}
              placeholder="e.g. Raw placement records 2024" className="input resize-none" disabled={uploading} />
          </div>
          <FileDropzone accept={{ 'text/csv': ['.csv'] }} maxSizeMB={50}
            onUpload={handleUpload} uploading={uploading} progress={progress}
            label="Drag & drop a CSV file, or click to browse" hint=".csv up to 50MB" />
        </div>
      )}

      {result && profile && (
        <div className="space-y-5 animate-fade-in">
          <div className="rounded-xl bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 p-4 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
            <p className="text-sm text-green-800 dark:text-green-300">
              Detected type: <strong className="capitalize">{result.result.detected_type}</strong> — {profile.row_count} rows analysed
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Stat label="Rows" value={profile.row_count} />
            <Stat label="Columns" value={profile.column_count} />
            <Stat label="Completeness" value={`${profile.completeness_pct}%`} />
            <Stat label="Duplicates" value={profile.duplicate_rows} />
          </div>

          {/* Column types */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-primary-500" /> Column Types
            </h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(profile.column_types || {}).map(([col, type]) => (
                <span key={col} className="badge-neutral">{col}: <strong className="ml-1">{type}</strong></span>
              ))}
            </div>
          </div>

          {/* NL Query */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <MessageSquareText className="w-4 h-4 text-primary-500" /> Ask a question about this data
            </h3>
            <div className="flex gap-2">
              <input value={question} onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleQuery()}
                placeholder="e.g. What's the average package by department?" className="input flex-1" />
              <button onClick={handleQuery} disabled={querying || !question.trim()} className="btn-primary px-4">
                {querying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>

            {queryResult && (
              <div className="mt-4 table-container">
                <table className="table text-xs">
                  {Array.isArray(queryResult.result) ? (
                    <>
                      <thead><tr>{Object.keys(queryResult.result[0] || {}).map(c => <th key={c}>{c}</th>)}</tr></thead>
                      <tbody>
                        {queryResult.result.slice(0, 15).map((row, i) => (
                          <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}</tr>
                        ))}
                      </tbody>
                    </>
                  ) : (
                    <tbody>
                      {Object.entries(queryResult.result || {}).map(([k, v]) => (
                        <tr key={k}><td className="font-medium">{k}</td><td>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td></tr>
                      ))}
                    </tbody>
                  )}
                </table>
                <p className="text-2xs text-gray-400 px-3 py-2">{queryResult.row_count} result(s) · operation: {queryResult.operation}</p>
              </div>
            )}
          </div>

          <button onClick={() => { setResult(null); setQueryResult(null) }} className="btn-secondary w-full justify-center">
            Upload Another File
          </button>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-3">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-base font-semibold text-gray-900 dark:text-white">{value}</p>
    </div>
  )
}
