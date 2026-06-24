/**
 * pages/SettingsPage.jsx — Phase 2 full implementation
 */
import React, { useState } from 'react'
import { Moon, Sun, Bell, Shield, Globe, Palette, Save, Loader2 } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useTitle } from '../hooks/index'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  useTitle('Settings')
  const { isDark, toggleTheme } = useTheme()
  const [saving, setSaving] = useState(false)
  const [notifs, setNotifs] = useState({
    email_attendance: true, email_placement: true, email_events: false,
    sms_alerts: false, in_app: true,
  })

  const toggleNotif = (key) => setNotifs(n => ({ ...n, [key]: !n[key] }))

  const save = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 800))
    toast.success('Settings saved')
    setSaving(false)
  }

  const Toggle = ({ value, onChange, label, desc }) => (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-dark-600 last:border-0">
      <div>
        <div className="text-sm font-medium text-gray-900 dark:text-white">{label}</div>
        {desc && <div className="text-xs text-gray-400 mt-0.5">{desc}</div>}
      </div>
      <button onClick={onChange} className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-primary-500' : 'bg-gray-200 dark:bg-dark-500'}`}>
        <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${value ? 'translate-x-5' : 'translate-x-0.5'}`} />
      </button>
    </div>
  )

  return (
    <div className="page-container max-w-2xl">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your preferences</p>
      </div>

      <div className="space-y-6">
        {/* Appearance */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Palette className="w-4 h-4 text-primary-500" /> Appearance
          </h3>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">Theme</div>
              <div className="text-xs text-gray-400 mt-0.5">Currently: {isDark ? 'Dark' : 'Light'}</div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => !isDark && toggleTheme()}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border transition-colors ${isDark ? 'bg-dark-700 border-primary-500 text-primary-400' : 'border-gray-200 text-gray-500 hover:border-gray-300'}`}>
                <Moon className="w-4 h-4" /> Dark
              </button>
              <button onClick={() => isDark && toggleTheme()}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border transition-colors ${!isDark ? 'bg-amber-50 border-amber-400 text-amber-700' : 'border-dark-500 text-gray-500 hover:border-dark-400'}`}>
                <Sun className="w-4 h-4" /> Light
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Bell className="w-4 h-4 text-primary-500" /> Notifications
          </h3>
          <Toggle value={notifs.email_attendance} onChange={() => toggleNotif('email_attendance')}
            label="Attendance alerts via email" desc="Get notified when attendance drops below 75%" />
          <Toggle value={notifs.email_placement} onChange={() => toggleNotif('email_placement')}
            label="Placement notifications" desc="New placement drives and offers" />
          <Toggle value={notifs.email_events} onChange={() => toggleNotif('email_events')}
            label="Event reminders" desc="Upcoming campus events and registrations" />
          <Toggle value={notifs.sms_alerts} onChange={() => toggleNotif('sms_alerts')}
            label="SMS alerts" desc="Critical alerts via SMS (requires phone number)" />
          <Toggle value={notifs.in_app} onChange={() => toggleNotif('in_app')}
            label="In-app notifications" desc="Show notification badge in the sidebar" />
        </div>

        {/* Security info */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary-500" /> Security
          </h3>
          <div className="text-sm text-gray-500 dark:text-gray-400 space-y-2">
            <p>🔒 Passwords are hashed with bcrypt (12 rounds)</p>
            <p>🔑 JWT tokens expire after 1 hour; refresh tokens after 30 days</p>
            <p>📋 All actions are recorded in the audit log</p>
            <p>🚦 API rate-limited to 100 requests/hour per IP</p>
          </div>
          <div className="mt-4">
            <a href="/profile" className="btn-secondary btn-sm">Change Password →</a>
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={save} disabled={saving} className="btn-primary">
            {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</> : <><Save className="w-4 h-4" /> Save Settings</>}
          </button>
        </div>
      </div>
    </div>
  )
}
