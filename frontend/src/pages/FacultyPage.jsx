/**
 * pages/FacultyPage.jsx — Faculty self-service portal
 */
import React, { useEffect, useState } from 'react'
import { Users, BookOpen, Loader2 } from 'lucide-react'
import { facultyAPI } from '../api/services'
import { useTitle } from '../hooks/index'

export default function FacultyPage() {
  useTitle('Faculty Portal')
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    facultyAPI.getMyProfile().then(({ data }) => setProfile(data.data)).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-container flex items-center justify-center py-20 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /></div>

  if (!profile) {
    return (
      <div className="page-container max-w-lg">
        <div className="card p-10 text-center">
          <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">No faculty profile linked to your account yet. Contact an administrator.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Faculty Portal</h1>
        <p className="page-subtitle">{profile.faculty_id} · {profile.department} · {profile.designation}</p>
      </div>

      <div className="card p-5 mb-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary-500" /> Subjects Taught
        </h3>
        <div className="flex flex-wrap gap-2">
          {profile.subjects?.length ? profile.subjects.map(s => <span key={s} className="badge-primary">{s}</span>) : <p className="text-sm text-gray-400">No subjects assigned</p>}
        </div>
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Profile Details</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <Field label="Full Name" value={profile.name} />
          <Field label="Email" value={profile.email} />
          <Field label="Phone" value={profile.phone || '—'} />
          <Field label="Qualification" value={profile.qualification || '—'} />
          <Field label="Experience" value={`${profile.experience_years || 0} years`} />
        </div>
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
