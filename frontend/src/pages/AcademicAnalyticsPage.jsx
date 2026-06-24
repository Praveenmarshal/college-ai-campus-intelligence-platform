/**
 * pages/AcademicAnalyticsPage.jsx — Phase 10
 */
import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Award, BookOpen, Loader2 } from 'lucide-react'
import { analyticsAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import { cgpaGrade } from '../utils/helpers'

export default function AcademicAnalyticsPage() {
  useTitle('Academic Analytics')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    analyticsAPI.getAcademic().then(res => { setData(res.data.data); setLoading(false) })
  }, [])

  if (loading) return <div className="page-container flex items-center justify-center py-20 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Academic Analytics</h1>
        <p className="page-subtitle">CGPA trends, department performance, and top performers</p>
      </div>

      <div className="card p-5 mb-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary-500" /> Average CGPA by Department
        </h3>
        {data?.by_department?.length ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.by_department}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="department" tick={{ fontSize: 10 }} />
              <YAxis domain={[0, 10]} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="avg_cgpa" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Award className="w-4 h-4 text-amber-500" /> Top Performers
        </h3>
        {data?.top_performers?.length ? (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Rank</th><th>Name</th><th>Student ID</th><th>Department</th><th>CGPA</th><th>Grade</th></tr></thead>
              <tbody>
                {data.top_performers.map((s, i) => (
                  <tr key={s.id}>
                    <td className="font-bold text-primary-600">#{i + 1}</td>
                    <td className="font-medium">{s.name}</td>
                    <td>{s.student_id}</td>
                    <td>{s.department}</td>
                    <td className="font-semibold">{s.cgpa}</td>
                    <td><span className="badge-success text-2xs">{cgpaGrade(s.cgpa)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm text-gray-400 py-10 text-center">No data yet</p>}
      </div>
    </div>
  )
}
