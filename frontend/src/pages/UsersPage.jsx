/**
 * pages/UsersPage.jsx — Admin user management (Phase 2)
 */
import React, { useState, useEffect } from 'react'
import { Users, Search, Plus, Shield, Loader2, Trash2, ToggleLeft, ToggleRight, ChevronLeft, ChevronRight } from 'lucide-react'
import { usersAPI } from '../api/services'
import { useTitle, useDebounce } from '../hooks/index'
import { formatDate, initials } from '../utils/helpers'
import toast from 'react-hot-toast'

const ROLE_BADGE = { admin: 'badge-danger', faculty: 'badge-primary', student: 'badge-success' }

export default function UsersPage() {
  useTitle('Users')
  const [users, setUsers]     = useState([])
  const [total, setTotal]     = useState(0)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [roleFilter, setRole] = useState('')
  const debouncedSearch       = useDebounce(search, 400)
  const perPage = 15

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await usersAPI.getAll({ page, per_page: perPage, search: debouncedSearch || undefined, role: roleFilter || undefined })
      setUsers(data.data || [])
      setTotal(data.pagination?.total || 0)
    } catch { toast.error('Failed to load users') }
    finally { setLoading(false) }
  }

  useEffect(() => { setPage(1) }, [debouncedSearch, roleFilter])
  useEffect(() => { load() }, [page, debouncedSearch, roleFilter])

  const toggleStatus = async (u) => {
    try {
      await usersAPI.update(u.id, undefined) // placeholder — use status endpoint
      const { data } = await fetch(`/api/users/${u.id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify({ is_active: !u.is_active }),
      }).then(r => r.json())
      toast.success(`User ${!u.is_active ? 'activated' : 'deactivated'}`)
      load()
    } catch { toast.error('Failed to update status') }
  }

  const deleteUser = async (id) => {
    if (!confirm('Delete this user? This cannot be undone.')) return
    try {
      await usersAPI.delete(id)
      toast.success('User deleted')
      load()
    } catch (err) { toast.error(err?.response?.data?.error || 'Failed to delete') }
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Users</h1>
          <p className="page-subtitle">{total} total users</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or email…" className="input pl-9" />
        </div>
        <select value={roleFilter} onChange={e => setRole(e.target.value)} className="input w-36">
          <option value="">All roles</option>
          <option value="admin">Admin</option>
          <option value="faculty">Faculty</option>
          <option value="student">Student</option>
        </select>
      </div>

      {/* Table */}
      <div className="table-container">
        {loading ? (
          <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin" /> Loading users…
          </div>
        ) : users.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <Users className="w-10 h-10 mb-2" />
            <p>No users found</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Department</th>
                <th>Status</th>
                <th>Joined</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-xs font-bold text-primary-700 dark:text-primary-300">
                        {initials(u.name)}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white text-sm">{u.name}</div>
                        <div className="text-xs text-gray-400">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className={`badge ${ROLE_BADGE[u.role] || 'badge-neutral'} capitalize`}><Shield className="w-3 h-3 mr-1" />{u.role}</span></td>
                  <td><span className="text-sm text-gray-500">{u.department || '—'}</span></td>
                  <td>
                    <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td><span className="text-sm text-gray-500">{formatDate(u.created_at)}</span></td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button onClick={() => toggleStatus(u)}
                        className="btn-ghost p-1.5" title={u.is_active ? 'Deactivate' : 'Activate'}>
                        {u.is_active ? <ToggleRight className="w-4 h-4 text-green-500" /> : <ToggleLeft className="w-4 h-4 text-gray-400" />}
                      </button>
                      <button onClick={() => deleteUser(u.id)}
                        className="btn-ghost p-1.5 hover:text-red-500" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>Page {page} of {totalPages} · {total} users</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary btn-sm">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary btn-sm">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
