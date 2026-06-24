/**
 * pages/PlacementsPage.jsx — Phase 10
 */
import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { GraduationCap, TrendingUp, Building2, Loader2 } from 'lucide-react'
import { analyticsAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import { CHART_COLORS, formatCurrency } from '../utils/helpers'

export default function PlacementsPage() {
  useTitle('Placements')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsAPI.getPlacements().then(res => { setData(res.data.data); setLoading(false) })
  }, [])

  if (loading) return <div className="page-container flex items-center justify-center py-20 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>

  const o = data?.overall || {}

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Placement Analytics</h1>
        <p className="page-subtitle">Packages, recruiters, and placement trends</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Stat icon={GraduationCap} label="Total Placed" value={o.placed ?? '—'} />
        <Stat icon={TrendingUp} label="Highest Package" value={o.max_package ? `₹${o.max_package} LPA` : '—'} />
        <Stat icon={TrendingUp} label="Average Package" value={o.avg_package ? `₹${o.avg_package} LPA` : '—'} />
        <Stat icon={Building2} label="Total Students" value={o.total ?? '—'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Placements by Year</h3>
          {data?.by_year?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.by_year}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="placed_count" fill="#6366f1" radius={[4, 4, 0, 0]} name="Placed" />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Top Recruiters</h3>
          {data?.top_recruiters?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={data.top_recruiters} dataKey="hires" nameKey="company" cx="50%" cy="50%" outerRadius={85} label={{ fontSize: 10 }}>
                  {data.top_recruiters.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip /><Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
        </div>
      </div>

      {data?.by_year?.length > 0 && (
        <div className="card p-5 mt-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Average Package by Year</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_year}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="avg_package" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Avg Package (LPA)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400">
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-xs text-gray-400 mt-0.5">{label}</p>
      </div>
    </div>
  )
}
