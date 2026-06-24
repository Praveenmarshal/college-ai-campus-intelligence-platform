/**
 * pages/DashboardPage.jsx — Phase 10 full implementation
 */
import React, { useEffect, useState } from 'react'
import { Users, GraduationCap, FileText, MessageSquare, TrendingUp, Loader2, ArrowRight } from 'lucide-react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { analyticsAPI } from '../api/services'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/index'
import { CHART_COLORS } from '../utils/helpers'

export default function DashboardPage() {
  useTitle('Dashboard')
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [attendance, setAttendance] = useState(null)
  const [placements, setPlacements] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsAPI.getDashboard().catch(() => null),
      analyticsAPI.getAttendance().catch(() => null),
      analyticsAPI.getPlacements().catch(() => null),
    ]).then(([d, a, p]) => {
      setStats(d?.data?.data)
      setAttendance(a?.data?.data)
      setPlacements(p?.data?.data)
      setLoading(false)
    })
  }, [])

  const quickLinks = [
    { label: 'Ask AI Assistant', icon: MessageSquare, path: '/chat', color: 'from-primary-500 to-primary-600' },
    { label: 'Resume Analyzer', icon: FileText, path: '/resume-analyzer', color: 'from-accent-500 to-accent-600' },
    { label: 'Attendance', icon: TrendingUp, path: '/attendance', color: 'from-green-500 to-green-600' },
    { label: 'Placements', icon: GraduationCap, path: '/placements', color: 'from-amber-500 to-amber-600' },
  ]

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="page-subtitle">Here's what's happening across campus today</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 gap-2 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin" /> Loading dashboard…
        </div>
      ) : (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-3">
            <StatCard icon={Users} label="Total Students" value={stats?.total_students ?? '—'} color="primary" />
            <StatCard icon={GraduationCap} label="Faculty" value={stats?.total_faculty ?? '—'} color="accent" />
            <StatCard icon={FileText} label="Documents" value={stats?.total_documents ?? '—'} color="amber" />
            <StatCard icon={TrendingUp} label="Placed (YTD)" value={stats?.total_placed ?? '—'} color="green" />
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <StatCard icon={TrendingUp} label="Avg Attendance" value={stats?.avg_attendance != null ? `${stats.avg_attendance}%` : '—'} color="green" />
            <StatCard icon={GraduationCap} label="Avg CGPA" value={stats?.avg_cgpa ?? '—'} color="primary" />
            <StatCard icon={TrendingUp} label="Highest Package" value={stats?.highest_package != null ? `${stats.highest_package} LPA` : '—'} color="amber" />
          </div>

          {/* Quick links */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {quickLinks.map(({ label, icon: Icon, path, color }) => (
              <button key={path} onClick={() => navigate(path)}
                className={`rounded-xl p-4 bg-gradient-to-br ${color} text-white text-left hover:scale-[1.02] transition-transform`}>
                <Icon className="w-5 h-5 mb-3 opacity-90" />
                <p className="text-sm font-medium">{label}</p>
                <ArrowRight className="w-3.5 h-3.5 mt-2 opacity-70" />
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Attendance trend */}
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Attendance Trend (30 days)</h3>
              {attendance?.trend_30_days?.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={attendance.trend_30_days}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-tertiary, #eee)" />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="attendance_pct" stroke="#6366f1" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : <EmptyChart />}
            </div>

            {/* Placement by year */}
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Placements by Year</h3>
              {placements?.by_year?.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={placements.by_year}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar dataKey="placed_count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyChart />}
            </div>

            {/* Department attendance */}
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Attendance by Department</h3>
              {attendance?.by_department?.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={attendance.by_department} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <YAxis dataKey="_id" type="category" tick={{ fontSize: 10 }} width={100} />
                    <Tooltip />
                    <Bar dataKey="attendance_pct" fill="#22c55e" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyChart />}
            </div>

            {/* Top recruiters */}
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Top Recruiters</h3>
              {placements?.top_recruiters?.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={placements.top_recruiters} dataKey="hires" nameKey="company" cx="50%" cy="50%" outerRadius={80} label={{ fontSize: 10 }}>
                      {placements.top_recruiters.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : <EmptyChart />}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    primary: 'bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400',
    accent: 'bg-accent-50 text-accent-600 dark:bg-accent-950 dark:text-accent-400',
    amber: 'bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400',
    green: 'bg-green-50 text-green-600 dark:bg-green-950 dark:text-green-400',
  }
  return (
    <div className="stat-card">
      <div className={`stat-icon ${colors[color]}`}><Icon className="w-5 h-5" /></div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
        <p className="text-xs text-gray-400 mt-0.5">{label}</p>
      </div>
    </div>
  )
}

function EmptyChart() {
  return (
    <div className="h-[220px] flex items-center justify-center text-sm text-gray-400">
      No data available yet
    </div>
  )
}
