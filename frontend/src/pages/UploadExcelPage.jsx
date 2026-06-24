/**
 * pages/UploadExcelPage.jsx — Phase 4
 */
import React, { useState } from 'react'
import { Table2, CheckCircle2, BarChart3 } from 'lucide-react'
import FileDropzone from '../components/common/FileDropzone'
import { documentsAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function UploadExcelPage() {
  useTitle('Upload Excel')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)

  const handleUpload = async (file) => {
    setUploading(true); setProgress(0); setResult(null)
    try {
      const { data } = await documentsAPI.uploadExcel(file, { description }, setProgress)
      setResult(data.data)
      toast.success(data.message || 'Excel processed')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Upload failed')
    } finally { setUploading(false) }
  }

  return (
    <div className="page-container max-w-3xl">
      <div className="page-header">
        <h1 className="page-title">Upload Excel Workbook</h1>
        <p className="page-subtitle">Supports attendance, placements, fees, results, students, faculty & timetable sheets</p>
      </div>

      <div className="card p-6 space-y-4">
        <div>
          <label className="label">Description <span className="text-gray-400 font-normal">(optional)</span></label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={2}
            placeholder="e.g. Semester 5 attendance sheet" className="input resize-none" disabled={uploading} />
        </div>
        <FileDropzone
          accept={{ 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'], 'application/vnd.ms-excel': ['.xls'] }}
          maxSizeMB={50} onUpload={handleUpload} uploading={uploading} progress={progress}
          label="Drag & drop an Excel file, or click to browse" hint=".xlsx or .xls, up to 50MB" />
      </div>

      {result && (
        <div className="mt-6 space-y-4 animate-fade-in">
          <div className="rounded-xl bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 p-4 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
            <p className="text-sm text-green-800 dark:text-green-300">
              Processed {result.sheet_count} sheet(s) — {result.file_size_readable}
            </p>
          </div>

          {Object.entries(result.analysis || {}).map(([sheetName, data]) => (
            <div key={sheetName} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Table2 className="w-4 h-4 text-primary-500" /> {sheetName}
                </h3>
                <span className="badge-primary capitalize">{data.detected_type}</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <Stat label="Rows" value={data.summary.row_count} />
                <Stat label="Columns" value={data.summary.column_count} />
                {data.analysis?.overall_attendance_pct != null && <Stat label="Avg Attendance" value={`${data.analysis.overall_attendance_pct}%`} />}
                {data.analysis?.placement_rate_pct != null && <Stat label="Placement Rate" value={`${data.analysis.placement_rate_pct}%`} />}
                {data.analysis?.average_cgpa != null && <Stat label="Avg CGPA" value={data.analysis.average_cgpa} />}
                {data.analysis?.highest_package != null && <Stat label="Highest Package" value={`${data.analysis.highest_package} LPA`} />}
              </div>

              {data.preview?.length > 0 && (
                <div className="table-container">
                  <table className="table text-xs">
                    <thead><tr>{Object.keys(data.preview[0]).slice(0, 6).map(c => <th key={c}>{c}</th>)}</tr></thead>
                    <tbody>
                      {data.preview.slice(0, 5).map((row, i) => (
                        <tr key={i}>{Object.values(row).slice(0, 6).map((v, j) => <td key={j}>{String(v)}</td>)}</tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}

          <a href="/chat" className="btn-primary w-full justify-center">
            <BarChart3 className="w-4 h-4" /> Ask questions about this data in AI Chat
          </a>
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
