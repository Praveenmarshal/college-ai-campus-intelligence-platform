/**
 * pages/UploadPDFPage.jsx — Phase 3 full implementation
 */
import React, { useState } from 'react'
import { FileText, CheckCircle2, Loader2 } from 'lucide-react'
import FileDropzone from '../components/common/FileDropzone'
import { documentsAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function UploadPDFPage() {
  useTitle('Upload PDF')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)

  const handleUpload = async (file) => {
    setUploading(true)
    setProgress(0)
    setResult(null)
    try {
      const { data } = await documentsAPI.uploadPDF(file, { description }, setProgress)
      setResult(data.data)
      toast.success(data.message || 'PDF processed successfully')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Upload PDF Document</h1>
        <p className="page-subtitle">Upload a PDF to make it searchable via the AI chat (RAG pipeline)</p>
      </div>

      <div className="card p-6 space-y-4">
        <div>
          <label className="label">Description <span className="text-gray-400 font-normal">(optional)</span></label>
          <textarea value={description} onChange={e => setDescription(e.target.value)}
            placeholder="e.g. Final exam syllabus for CS301, Semester 5"
            rows={2} className="input resize-none" disabled={uploading} />
        </div>

        <FileDropzone
          accept={{ 'application/pdf': ['.pdf'] }}
          maxSizeMB={50}
          onUpload={handleUpload}
          uploading={uploading}
          progress={progress}
          label="Drag & drop a PDF here, or click to browse"
          hint="PDF files only, up to 50MB"
        />

        {result && (
          <div className="rounded-xl bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 p-4 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-green-800 dark:text-green-300">Document processed successfully</p>
              <ul className="text-green-700 dark:text-green-400 mt-1 space-y-0.5">
                <li>📄 {result.page_count} pages extracted</li>
                <li>🧩 {result.chunks_created} chunks indexed in vector store</li>
                <li>📦 {result.file_size_readable}</li>
              </ul>
              <a href="/chat" className="inline-block mt-2 text-green-700 dark:text-green-400 underline text-xs font-medium">
                Ask questions about this document →
              </a>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 card p-5">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary-500" /> How the RAG pipeline works
        </h3>
        <ol className="text-sm text-gray-500 dark:text-gray-400 space-y-1.5 list-decimal list-inside">
          <li>Text is extracted from every page of the PDF</li>
          <li>Content is cleaned and split into ~800-character chunks</li>
          <li>Each chunk is embedded using all-MiniLM-L6-v2</li>
          <li>Vectors are stored in ChromaDB for semantic search</li>
          <li>Ask anything in the AI Chat — relevant chunks are retrieved and sent to Qwen 3</li>
        </ol>
      </div>
    </div>
  )
}
