/**
 * pages/ProfilePage.jsx — Profile settings for Google OAuth users
 */
import React, { useState } from 'react'
import { User, Phone, Building2, Shield, Calendar, Save, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/index'
import { usersAPI } from '../api/services'
import toast from 'react-hot-toast'
import { formatDate } from '../utils/helpers'

export default function ProfilePage() {
  useTitle('Profile')
  const { user, updateUser } = useAuth()

  const [form, setForm] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    department: user?.department || '',
  })
  const [saving, setSaving] = useState(false)

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const { data } = await usersAPI.updateProfile(form)
      updateUser(data.data)
      toast.success('Profile updated!')
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const roleColors = { admin: 'badge-danger', faculty: 'badge-primary', student: 'badge-success' }

  return (
    <div className="page-container max-w-3xl">
      <div className="page-header">
        <h1 className="page-title">My Profile</h1>
        <p className="page-subtitle">Manage your account information</p>
      </div>

      <div className="space-y-6">
        {/* Avatar + meta */}
        <div className="card p-6 flex items-center gap-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center text-white text-2xl font-bold shrink-0">
            {user?.profile_picture ? (
              <img src={user.profile_picture} alt={user.name} className="w-full h-full rounded-2xl object-cover" />
            ) : (
              user?.name?.charAt(0)?.toUpperCase()
            )}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{user?.name}</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm">{user?.email}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`badge ${roleColors[user?.role] || 'badge-neutral'} capitalize`}>
                <Shield className="w-3 h-3 mr-1" />{user?.role}
              </span>
              {user?.department && <span className="badge badge-neutral">{user.department}</span>}
            </div>
          </div>
          <div className="ml-auto text-right text-sm text-gray-400">
            <div className="flex items-center gap-1 justify-end"><Calendar className="w-3.5 h-3.5" /> Joined</div>
            <div className="text-gray-600 dark:text-gray-300">{formatDate(user?.created_at)}</div>
          </div>
        </div>

        {/* Edit profile */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <User className="w-4 h-4 text-primary-500" /> Personal Information
          </h3>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Full name</label>
                <input type="text" value={form.name} onChange={set('name')} className="input" />
              </div>
              <div>
                <label className="label">Phone</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input type="tel" value={form.phone} onChange={set('phone')} className="input pl-9" placeholder="+91..." />
                </div>
              </div>
            </div>
            <div>
              <label className="label">Department</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" value={form.department} onChange={set('department')} className="input pl-9" />
              </div>
            </div>
            <div className="flex justify-end">
              <button type="submit" disabled={saving} className="btn-primary">
                {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</> : <><Save className="w-4 h-4" /> Save Changes</>}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
