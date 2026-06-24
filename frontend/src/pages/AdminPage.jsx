/**
 * pages/AdminPage.jsx — Admin overview dashboard
 */
import React, { useEffect, useState } from 'react'
import { Users, FileText, Activity, Database, Loader2, ArrowRight, Upload, Shield, BarChart3 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'

export default function AdminPage() {
  useTitle('Admin Panel')
  const navigate = useNavigate()
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/api/admin/system-overview').then(({ data }) => setOverview(data.data)).finally(() => setLoading(false))
  }, [])

  const actions = [
    { label: 'Upload PDF', icon: Upload, path: '/admin/upload-pdf', color: 'from-primary-500 to-primary-600' },
    { label: 'Upload Excel', icon: Upload, path: '/admin/upload-excel', color: 'from-accent-500 to-accent-600' },
    { label: 'Manage Users', icon: Users, path: '/admin/users', color: 'from-green-500 to-green-600' },
    { label: 'View Documents', icon: FileText, path: '/admin/documents', color: 'from-amber-500 to-amber-600' },
    { label: 'System Health', icon: Activity, path: '/admin/system-health', color: 'from-red-500 to-red-600' },
    { label: 'Audit Logs', icon: Shield, path: '/admin/reports', color: 'from-purple-500 to-purple-600' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Admin Panel</h1>
        <p className="page-subtitle">Manage the platform, users, and data</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {overview?.mongodb_collections && Object.entries(overview.mongodb_collections).slice(0, 4).map(([name, count]) => (
            <div key={name} className="stat-card">
              <div className="stat-icon bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{count}</p>
                <p className="text-xs text-gray-400 capitalize">{name}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {actions.map(({ label, icon: Icon, path, color }) => (
          <button key={path} onClick={() => navigate(path)}
            className={`rounded-xl p-5 bg-gradient-to-br ${color} text-white text-left hover:scale-[1.02] transition-transform`}>
            <Icon className="w-5 h-5 mb-3 opacity-90" />
            <p className="text-sm font-medium">{label}</p>
            <ArrowRight className="w-3.5 h-3.5 mt-2 opacity-70" />
          </button>
        ))}
      </div>
    </div>
  )
}
