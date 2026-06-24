/**
 * pages/QuestionPaperPage.jsx — Phase 12
 */
import React, { useState } from 'react'
import { BrainCircuit, Hash, BarChart2, Layers } from 'lucide-react'
import FileDropzone from '../components/common/FileDropzone'
import { ocrAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function QuestionPaperPage() {
  useTitle('Question Paper Analyzer')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)

  const handleUpload = async (file) => {
    setUploading(true); setProgress(0); setResult(null)
    try {
      const { data } = await ocrAPI.analyzeQuestionPaper(file, setProgress)
      setResult(data.data)
      toast.success('Question paper analyzed')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Analysis failed')
    } finally { setUploading(false) }
  }

  const difficultyColor = { easy: 'badge-success', medium: 'badge-warning', hard: 'badge-danger' }

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Question Paper Analyzer</h1>
        <p className="page-subtitle">Extract topics, difficulty, and question patterns via OCR + AI</p>
      </div>

      {!result && (
        <div className="card p-6">
          <FileDropzone
            accept={{ 'application/pdf': ['.pdf'], 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'] }}
            maxSizeMB={20} onUpload={handleUpload} uploading={uploading} progress={progress}
            label="Upload a question paper (PDF or scanned image)" hint="PDF, PNG, or JPG — up to 20MB" />
        </div>
      )}

      {result && (
        <div className="space-y-5 animate-fade-in">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-primary-500" /> {result.filename}
              </h3>
              <span className={difficultyColor[result.analysis.difficulty_level] || 'badge-neutral'}>
                {result.analysis.difficulty_level} difficulty
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 mb-5">
              <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-3 text-center">
                <Hash className="w-4 h-4 mx-auto text-primary-500 mb-1" />
                <p className="text-lg font-bold text-gray-900 dark:text-white">{result.analysis.question_count}</p>
                <p className="text-2xs text-gray-400">Questions</p>
              </div>
              <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-3 text-center">
                <Layers className="w-4 h-4 mx-auto text-primary-500 mb-1" />
                <p className="text-lg font-bold text-gray-900 dark:text-white">{result.analysis.topics?.length || 0}</p>
                <p className="text-2xs text-gray-400">Topics Found</p>
              </div>
              <div className="bg-gray-50 dark:bg-dark-700 rounded-lg p-3 text-center">
                <BarChart2 className="w-4 h-4 mx-auto text-primary-500 mb-1" />
                <p className="text-sm font-bold text-gray-900 dark:text-white truncate">{result.analysis.subject_area}</p>
                <p className="text-2xs text-gray-400">Subject</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-xs text-gray-400 mb-2">Topics Covered</p>
              <div className="flex flex-wrap gap-1.5">
                {result.analysis.topics?.map(t => <span key={t} className="badge-primary">{t}</span>)}
              </div>
            </div>

            {result.analysis.question_types?.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-2">Question Types</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.analysis.question_types.map(t => <span key={t} className="badge-neutral">{t}</span>)}
                </div>
              </div>
            )}
          </div>

          <button onClick={() => setResult(null)} className="btn-secondary w-full justify-center">
            Analyze Another Paper
          </button>
        </div>
      )}
    </div>
  )
}
