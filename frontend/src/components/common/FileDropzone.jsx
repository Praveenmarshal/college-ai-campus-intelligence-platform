/**
 * components/common/FileDropzone.jsx
 * Reusable drag-and-drop file upload zone with progress bar.
 */
import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, File, X, CheckCircle2, Loader2 } from 'lucide-react'
import { formatFileSize } from '../../utils/helpers'

export default function FileDropzone({
  accept, maxSizeMB = 50, onUpload, uploading, progress,
  label = 'Drag & drop a file here, or click to browse',
  hint = '',
}) {
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')

  const onDrop = useCallback((accepted, rejected) => {
    setError('')
    if (rejected?.length) {
      setError(rejected[0].errors[0]?.message || 'Invalid file')
      return
    }
    if (accepted?.length) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept, maxSize: maxSizeMB * 1024 * 1024, multiple: false,
  })

  const handleUpload = () => {
    if (file) onUpload(file)
  }

  const clear = () => { setFile(null); setError('') }

  return (
    <div>
      {!file ? (
        <div {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-primary-400 bg-primary-50 dark:bg-primary-950/30' : 'border-gray-200 dark:border-dark-500 hover:border-primary-300'}`}>
          <input {...getInputProps()} />
          <UploadCloud className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</p>
          {hint && <p className="text-xs text-gray-400 mt-1">{hint}</p>}
        </div>
      ) : (
        <div className="border border-gray-200 dark:border-dark-500 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900 flex items-center justify-center shrink-0">
              <File className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{file.name}</p>
              <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
            </div>
            {!uploading && (
              <button onClick={clear} className="btn-ghost p-1.5"><X className="w-4 h-4" /></button>
            )}
          </div>

          {uploading && (
            <div className="mt-3">
              <div className="h-1.5 bg-gray-100 dark:bg-dark-600 rounded-full overflow-hidden">
                <div className="h-full bg-primary-500 transition-all duration-300" style={{ width: `${progress || 0}%` }} />
              </div>
              <p className="text-xs text-gray-400 mt-1">{progress || 0}% uploaded</p>
            </div>
          )}

          {!uploading && (
            <button onClick={handleUpload} className="btn-primary btn-sm w-full justify-center mt-3">
              Upload & Process
            </button>
          )}
        </div>
      )}
      {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
    </div>
  )
}
