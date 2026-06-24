/**
 * pages/StudentPage.jsx — Student self-service portal
 */
import React, { useEffect, useState } from 'react'
import { GraduationCap, Activity, TrendingUp, AlertTriangle, Loader2 } from 'lucide-react'
import { studentsAPI, mlAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import { cgpaGrade, attendanceStatus } from '../utils/helpers'

export default function StudentPage() {
  useTitle('Student Portal')
  const [profile, setProfile] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    studentsAPI.getMyProfile()
      .then(({ data }) => {
        setProfile(data.data)
        return mlAPI.predictAll(data.data.student_id)
      })
      .then(({ data }) => setPredictions(data.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-container flex items-center justify-center py-20 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>

  if (!profile) {
    return (
      <div className="page-container max-w-lg">
        <div className="card p-10 text-center">
          <GraduationCap className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            No student profile linked to your account yet. Contact an administrator.
          </p>
        </div>
      </div>
    )
  }

  const att = attendanceStatus(predictions?.attendance_pct ?? 100)

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">My Academic Profile</h1>
        <p className="page-subtitle">{profile.student_id} · {profile.department} · Semester {profile.semester}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Stat icon={GraduationCap} label="CGPA" value={profile.cgpa} sub={cgpaGrade(profile.cgpa)} />
        <Stat icon={Activity} label="Attendance" value={predictions?.attendance_pct ? `${predictions.attendance_pct}%` : '—'}
          sub={att.label} subColor={att.color} />
        <Stat icon={TrendingUp} label="CGPA Trend" value={predictions?.cgpa_prediction || '—'} />
        <Stat icon={AlertTriangle} label="Fee Status" value={predictions?.fee_default_risk || '—'} />
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Profile Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <Field label="Full Name" value={profile.name} />
          <Field label="Email" value={profile.email} />
          <Field label="Phone" value={profile.phone || '—'} />
          <Field label="Section" value={profile.section || '—'} />
          <Field label="Batch Year" value={profile.batch_year} />
          <Field label="Hostel Resident" value={profile.is_hostel ? 'Yes' : 'No'} />
        </div>
      </div>
    </div>
  )
}

function Stat({ icon: Icon, label, value, sub, subColor }) {
  return (
    <div className="stat-card">
      <div className="stat-icon bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400">
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-xl font-bold text-gray-900 dark:text-white capitalize">{value}</p>
        <p className="text-xs text-gray-400 mt-0.5">{label}</p>
        {sub && <span className={`badge-${subColor || 'neutral'} text-2xs mt-1 inline-block`}>{sub}</span>}
      </div>
    </div>
  )
}

function Field({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-gray-900 dark:text-white font-medium">{value}</p>
    </div>
  )
}
