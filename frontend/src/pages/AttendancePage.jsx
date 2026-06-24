/**
 * pages/AttendancePage.jsx — Phase 10
 */
import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { Activity, AlertTriangle, Loader2 } from 'lucide-react'
import { analyticsAPI } from '../api/services'
import apiClient from '../api/client'
import { useTitle } from '../hooks/index'
import { attendanceStatus } from '../utils/helpers'

export default function AttendancePage() {
  useTitle('Attendance')
  const [data, setData] = useState(null)
  const [atRisk, setAtRisk] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsAPI.getAttendance(),
      apiClient.get('/api/ml/at-risk-students').catch(() => null),
    ]).then(([res, riskRes]) => {
      setData(res.data.data)
      setAtRisk(riskRes?.data?.data?.at_risk_students || [])
      setLoading(false)
    })
  }, [])

  if (loading) return <div className="page-container flex items-center justify-center py-20 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Attendance Analytics</h1>
        <p className="page-subtitle">Department trends, risk detection, and historical patterns</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary-500" /> By Department
          </h3>
          {data?.by_department?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.by_department}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="_id" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="attendance_pct" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">30-Day Trend</h3>
          {data?.trend_30_days?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.trend_30_days}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 9 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line type="monotone" dataKey="attendance_pct" stroke="#06b6d4" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
        </div>
      </div>

      {/* At-risk students */}
      <div className="card p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500" /> At-Risk Students (below 75%)
        </h3>
        {atRisk.length === 0 ? (
          <p className="text-sm text-gray-400 py-6 text-center">No at-risk students detected — great work! 🎉</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Student ID</th><th>Attendance %</th><th>Status</th></tr></thead>
              <tbody>
                {atRisk.map(s => {
                  const status = attendanceStatus(s.attendance_pct)
                  return (
                    <tr key={s.student_id}>
                      <td className="font-medium">{s.student_id}</td>
                      <td>{s.attendance_pct}%</td>
                      <td><span className={`badge-${status.color}`}>{status.label}</span></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
