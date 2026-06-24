/**
 * pages/NotificationsPage.jsx — Phase 13
 */
import React, { useEffect, useState } from 'react'
import { Bell, CheckCheck, Trash2, Loader2, Mail, AlertTriangle, GraduationCap, Calendar } from 'lucide-react'
import { notificationsAPI } from '../api/services'
import { useTitle } from '../hooks/index'
import { timeAgo } from '../utils/helpers'
import toast from 'react-hot-toast'

const TYPE_ICONS = {
  attendance: AlertTriangle, fee: Mail, placement: GraduationCap, event: Calendar, system: Bell,
}
const TYPE_COLORS = {
  attendance: 'text-red-500 bg-red-50 dark:bg-red-950',
  fee: 'text-amber-500 bg-amber-50 dark:bg-amber-950',
  placement: 'text-green-500 bg-green-50 dark:bg-green-950',
  event: 'text-primary-500 bg-primary-50 dark:bg-primary-950',
  system: 'text-gray-500 bg-gray-50 dark:bg-dark-700',
}

export default function NotificationsPage() {
  useTitle('Notifications')
  const [notifs, setNotifs] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await notificationsAPI.getAll({ per_page: 50 })
      setNotifs(data.data || [])
    } catch { toast.error('Failed to load notifications') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const markRead = async (id) => {
    try { await notificationsAPI.markRead(id); setNotifs(n => n.map(x => x.id === id ? { ...x, is_read: true } : x)) }
    catch { toast.error('Failed to mark as read') }
  }

  const markAllRead = async () => {
    try { await notificationsAPI.markAllRead(); setNotifs(n => n.map(x => ({ ...x, is_read: true }))); toast.success('All marked as read') }
    catch { toast.error('Failed') }
  }

  const remove = async (id) => {
    try { await notificationsAPI.delete(id); setNotifs(n => n.filter(x => x.id !== id)) }
    catch { toast.error('Failed to delete') }
  }

  const unreadCount = notifs.filter(n => !n.is_read).length

  return (
    <div className="page-container max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">{unreadCount} unread</p>
        </div>
        {unreadCount > 0 && (
          <button onClick={markAllRead} className="btn-secondary btn-sm">
            <CheckCheck className="w-3.5 h-3.5" /> Mark all read
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 gap-2 text-gray-400"><Loader2 className="w-5 h-5 animate-spin" /> Loading…</div>
      ) : notifs.length === 0 ? (
        <div className="card p-12 flex flex-col items-center text-center gap-3">
          <Bell className="w-10 h-10 text-gray-300" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">You're all caught up!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifs.map(n => {
            const Icon = TYPE_ICONS[n.notification_type] || Bell
            return (
              <div key={n.id} className={`card p-4 flex items-start gap-3 ${!n.is_read ? 'border-l-2 border-l-primary-500' : ''}`}>
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${TYPE_COLORS[n.notification_type] || TYPE_COLORS.system}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{n.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{n.message}</p>
                  <p className="text-2xs text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
                </div>
                <div className="flex gap-1 shrink-0">
                  {!n.is_read && (
                    <button onClick={() => markRead(n.id)} className="btn-ghost p-1.5" title="Mark as read">
                      <CheckCheck className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button onClick={() => remove(n.id)} className="btn-ghost p-1.5 hover:text-red-500" title="Delete">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
