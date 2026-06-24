/**
 * pages/DocumentsPage.jsx — Phase 3
 */
import React, { useState, useEffect } from 'react'
import { FileText, Search, Trash2, RefreshCw, Loader2, CheckCircle2, XCircle, Upload } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { documentsAPI } from '../api/services'
import { useTitle, useDebounce } from '../hooks/index'
import { formatDate, formatFileSize } from '../utils/helpers'
import toast from 'react-hot-toast'

export default function DocumentsPage() {
  useTitle('Documents')
  const navigate = useNavigate()
  const [docs, setDocs]       = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [typeFilter, setType] = useState('')
  const debounced = useDebounce(search, 400)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await documentsAPI.getAll({ search: debounced || undefined, file_type: typeFilter || undefined, per_page: 50 })
      setDocs(data.data || [])
      setTotal(data.pagination?.total || 0)
    } catch { toast.error('Failed to load documents') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [debounced, typeFilter])

  const handleDelete = async (id) => {
    if (!confirm('Delete this document? Its vectors will also be removed.')) return
    try {
      await documentsAPI.delete(id)
      toast.success('Document deleted')
      load()
    } catch { toast.error('Failed to delete') }
  }

  const handleReprocess = async (id) => {
    try {
      toast.loading('Reprocessing…', { id: 'reprocess' })
      await documentsAPI.reprocess(id)
      toast.success('Reprocessed successfully', { id: 'reprocess' })
      load()
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Reprocess failed', { id: 'reprocess' })
    }
  }

  const typeIcons = { pdf: '📄', excel: '📊', csv: '📋', image: '🖼️' }

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Documents</h1>
          <p className="page-subtitle">{total} document(s) indexed</p>
        </div>
        <button onClick={() => navigate('/admin/upload-pdf')} className="btn-primary btn-sm">
          <Upload className="w-3.5 h-3.5" /> Upload New
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search documents…" className="input pl-9" />
        </div>
        <select value={typeFilter} onChange={e => setType(e.target.value)} className="input w-36">
          <option value="">All types</option>
          <option value="pdf">PDF</option>
          <option value="excel">Excel</option>
          <option value="csv">CSV</option>
          <option value="image">Image</option>
        </select>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /> Loading…</div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <FileText className="w-10 h-10 mb-2" /><p>No documents found</p>
          </div>
        ) : (
          <table className="table">
            <thead><tr><th>Document</th><th>Type</th><th>Size</th><th>Chunks</th><th>Status</th><th>Uploaded</th><th>Actions</th></tr></thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{typeIcons[d.file_type] || '📁'}</span>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white text-sm">{d.original_name}</div>
                        {d.description && <div className="text-xs text-gray-400 max-w-xs truncate">{d.description}</div>}
                      </div>
                    </div>
                  </td>
                  <td><span className="badge-neutral uppercase text-2xs">{d.file_type}</span></td>
                  <td className="text-sm text-gray-500">{formatFileSize(d.file_size)}</td>
                  <td className="text-sm text-gray-500">{d.chunk_count || 0}</td>
                  <td>
                    {d.is_processed ? (
                      <span className="badge-success"><CheckCircle2 className="w-3 h-3 mr-1" />Processed</span>
                    ) : d.processing_error ? (
                      <span className="badge-danger"><XCircle className="w-3 h-3 mr-1" />Failed</span>
                    ) : (
                      <span className="badge-warning">Pending</span>
                    )}
                  </td>
                  <td className="text-sm text-gray-500">{formatDate(d.created_at)}</td>
                  <td>
                    <div className="flex gap-1">
                      {d.file_type === 'pdf' && (
                        <button onClick={() => handleReprocess(d.id)} className="btn-ghost p-1.5" title="Reprocess">
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => handleDelete(d.id)} className="btn-ghost p-1.5 hover:text-red-500" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
