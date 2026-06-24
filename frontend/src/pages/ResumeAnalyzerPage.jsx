/**
 * pages/ResumeAnalyzerPage.jsx — Phase 9 full implementation
 */
import React, { useState } from 'react'
import { FileSearch, Target, TrendingUp, AlertCircle, CheckCircle2, Lightbulb, Briefcase } from 'lucide-react'
import FileDropzone from '../components/common/FileDropzone'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function ResumeAnalyzerPage() {
  useTitle('Resume Analyzer')
  const [targetRole, setTargetRole] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)

  const handleUpload = async (file) => {
    setUploading(true)
    setProgress(0)
    setResult(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_role', targetRole)
    try {
      const { data } = await apiClient.post('/api/resume/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => setProgress(Math.round((e.loaded * 100) / e.total)),
      })
      setResult(data.data)
      toast.success('Resume analyzed!')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Analysis failed')
    } finally {
      setUploading(false)
    }
  }

  const scoreColor = (score) => score >= 75 ? 'text-green-500' : score >= 50 ? 'text-amber-500' : 'text-red-500'
  const scoreRing = (score) => score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div className="page-container max-w-3xl">
      <div className="page-header">
        <h1 className="page-title">Resume Analyzer</h1>
        <p className="page-subtitle">Get an ATS score, skill gap analysis, and improvement tips — powered by Qwen 3</p>
      </div>

      {!result && (
        <div className="card p-6 space-y-4">
          <div>
            <label className="label">Target job role <span className="text-gray-400 font-normal">(optional)</span></label>
            <input type="text" value={targetRole} onChange={e => setTargetRole(e.target.value)}
              placeholder="e.g. Software Engineer, Data Analyst" className="input" disabled={uploading} />
          </div>
          <FileDropzone
            accept={{ 'application/pdf': ['.pdf'] }}
            maxSizeMB={10}
            onUpload={handleUpload}
            uploading={uploading}
            progress={progress}
            label="Drag & drop your resume (PDF), or click to browse"
            hint="PDF format only, max 10MB"
          />
        </div>
      )}

      {result && (
        <div className="space-y-5 animate-fade-in">
          {/* Score card */}
          <div className="card p-6 flex items-center gap-6">
            <div className="relative w-24 h-24 shrink-0">
              <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="8" className="text-gray-100 dark:text-dark-600" />
                <circle cx="50" cy="50" r="42" fill="none" stroke={scoreRing(result.analysis.ats_score)} strokeWidth="8"
                  strokeDasharray={`${(result.analysis.ats_score / 100) * 264} 264`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-2xl font-bold ${scoreColor(result.analysis.ats_score)}`}>{result.analysis.ats_score}</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-gray-400">ATS Compatibility Score</p>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{result.filename}</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 max-w-md">{result.analysis.summary}</p>
            </div>
          </div>

          {/* Strengths / Weaknesses */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-500" /> Strengths
              </h3>
              <ul className="space-y-1.5">
                {result.analysis.strengths?.map((s, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-300 flex gap-2">
                    <span className="text-green-500">•</span>{s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-amber-500" /> Areas to Improve
              </h3>
              <ul className="space-y-1.5">
                {result.analysis.weaknesses?.map((w, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-300 flex gap-2">
                    <span className="text-amber-500">•</span>{w}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Skills */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <Target className="w-4 h-4 text-primary-500" /> Skills Analysis
            </h3>
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1.5">Found in resume</p>
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.extracted_skills?.map(s => <span key={s} className="badge-success capitalize">{s}</span>)}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1.5">Missing / recommended</p>
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.missing_skills?.map(s => <span key={s} className="badge-warning capitalize">{s}</span>)}
              </div>
            </div>
          </div>

          {/* Suggested roles */}
          {result.analysis.suggested_job_roles?.length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-primary-500" /> Suggested Job Roles
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.analysis.suggested_job_roles.map(r => <span key={r} className="badge-primary">{r}</span>)}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" /> Recommendations
            </h3>
            <ol className="space-y-2">
              {result.analysis.recommendations?.map((r, i) => (
                <li key={i} className="text-sm text-gray-600 dark:text-gray-300 flex gap-2">
                  <span className="text-primary-500 font-medium">{i + 1}.</span>{r}
                </li>
              ))}
            </ol>
          </div>

          <button onClick={() => setResult(null)} className="btn-secondary w-full justify-center">
            Analyze Another Resume
          </button>
        </div>
      )}
    </div>
  )
}
