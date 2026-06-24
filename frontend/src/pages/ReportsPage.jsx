/**
 * pages/ReportsPage.jsx — Admin audit log + report viewer
 */
import React, { useEffect, useState } from 'react'
import { Shield, Loader2, Filter } from 'lucide-react'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'
import { formatDateTime } from '../utils/helpers'

export default function ReportsPage() {
  useTitle('Reports & Audit Logs')
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState('')

  useEffect(() => {
    setLoading(true)
    apiClient.get('/api/admin/audit-logs', { params: { action: actionFilter || undefined, limit: 100 } })
      .then(({ data }) => setLogs(data.data || []))
      .finally(() => setLoading(false))
  }, [actionFilter])

  const statusBadge = { success: 'badge-success', failure: 'badge-danger' }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Reports & Audit Logs</h1>
        <p className="page-subtitle">System activity log — every significant action is recorded</p>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-gray-400" />
        <select value={actionFilter} onChange={e => setActionFilter(e.target.value)} className="input w-56">
          <option value="">All actions</option>
          <option value="login">Login</option>
          <option value="register">Register</option>
          <option value="upload_pdf">Upload PDF</option>
          <option value="upload_excel">Upload Excel</option>
          <option value="delete_document">Delete Document</option>
          <option value="update_role">Update Role</option>
        </select>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Shield className="w-10 h-10 mb-2" /><p>No audit logs found</p>
          </div>
        ) : (
          <table className="table text-xs">
            <thead><tr><th>Action</th><th>Resource</th><th>Status</th><th>IP</th><th>Timestamp</th></tr></thead>
            <tbody>
              {logs.map(l => (
                <tr key={l.id}>
                  <td className="font-medium">{l.action}</td>
                  <td>{l.resource || '—'}</td>
                  <td><span className={statusBadge[l.status] || 'badge-neutral'}>{l.status}</span></td>
                  <td>{l.ip_address || '—'}</td>
                  <td>{formatDateTime(l.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
