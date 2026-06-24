/**
 * components/layout/Sidebar.jsx
 * Left navigation sidebar with role-based menu items.
 */

import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, MessageSquare, History, User, Settings,
  FileText, Table2, Users, BarChart3, Bell, Activity,
  BookOpen, GraduationCap, Calendar, Library, Home, PartyPopper,
  BrainCircuit, FileSearch, LogOut, ChevronRight,
  Upload, Shield,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

// ── Nav item definition ────────────────────────────────────
const navItems = [
  {
    group: 'Main',
    items: [
      { label: 'Dashboard',    path: '/dashboard',          icon: LayoutDashboard },
      { label: 'AI Chat',      path: '/chat',               icon: MessageSquare },
      { label: 'Chat History', path: '/chat-history',       icon: History },
    ],
  },
  {
    group: 'Academics',
    items: [
      { label: 'Attendance',         path: '/attendance',          icon: Activity },
      { label: 'Academic Analytics', path: '/academic-analytics',  icon: BarChart3 },
      { label: 'Placements',         path: '/placements',          icon: GraduationCap },
      { label: 'Timetable',          path: '/timetable',           icon: Calendar },
      { label: 'Academic Calendar',  path: '/calendar',            icon: Calendar },
    ],
  },
  {
    group: 'Tools',
    items: [
      { label: 'Resume Analyzer',      path: '/resume-analyzer',         icon: FileSearch },
      { label: 'Question Analyzer',    path: '/question-paper-analyzer', icon: BrainCircuit },
      { label: 'Library',              path: '/library',                 icon: Library },
      { label: 'Hostel',               path: '/hostel',                  icon: Home },
      { label: 'Events',               path: '/events',                  icon: PartyPopper },
    ],
  },
  {
    group: 'Admin',
    roles: ['admin'],
    items: [
      { label: 'Admin Panel',    path: '/admin',                    icon: Shield },
      { label: 'Upload PDF',     path: '/admin/upload-pdf',         icon: Upload },
      { label: 'Upload Excel',   path: '/admin/upload-excel',       icon: Table2 },
      { label: 'Documents',      path: '/admin/documents',          icon: FileText },
      { label: 'Users',          path: '/admin/users',              icon: Users },
      { label: 'Reports',        path: '/admin/reports',            icon: BookOpen },
      { label: 'System Health',  path: '/admin/system-health',      icon: Activity },
    ],
  },
]

export default function Sidebar({ collapsed, mobileOpen, onMobileClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const sidebarClass = clsx(
    'fixed inset-y-0 left-0 z-30 flex flex-col',
    'bg-white dark:bg-dark-800 border-r border-gray-100 dark:border-dark-600',
    'transition-all duration-300',
    // Desktop
    'lg:relative lg:translate-x-0',
    collapsed ? 'lg:w-16' : 'lg:w-64',
    // Mobile
    mobileOpen ? 'translate-x-0 w-64' : '-translate-x-full w-64 lg:translate-x-0'
  )

  return (
    <aside className={sidebarClass}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-100 dark:border-dark-600 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shrink-0">
          <BrainCircuit className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="text-sm font-bold text-gray-900 dark:text-white truncate leading-tight">
              Campus AI
            </p>
            <p className="text-2xs text-gray-400 truncate">Intelligence Platform</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 no-scrollbar">
        {navItems.map((group) => {
          // Hide admin-only groups from non-admins
          if (group.roles && !group.roles.includes(user?.role)) return null

          return (
            <div key={group.group} className="mb-4">
              {!collapsed && (
                <p className="px-4 mb-1 text-2xs font-semibold uppercase tracking-wider text-gray-400">
                  {group.group}
                </p>
              )}
              {group.items.map((item) => (
                <SidebarItem
                  key={item.path}
                  item={item}
                  collapsed={collapsed}
                  onClick={onMobileClose}
                />
              ))}
            </div>
          )
        })}
      </nav>

      {/* User footer */}
      <div className="border-t border-gray-100 dark:border-dark-600 p-3 shrink-0">
        {!collapsed ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-primary-700 dark:text-primary-300">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{user?.name}</p>
              <p className="text-2xs text-gray-400 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        )}
      </div>
    </aside>
  )
}

function SidebarItem({ item, collapsed, onClick }) {
  const { icon: Icon, label, path } = item

  return (
    <NavLink
      to={path}
      onClick={onClick}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 mx-2 px-2 py-2 rounded-lg text-sm font-medium transition-colors duration-150 group',
          isActive
            ? 'bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-dark-700 dark:hover:text-gray-100',
          collapsed && 'justify-center'
        )
      }
      title={collapsed ? label : undefined}
    >
      <Icon className="w-4 h-4 shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
    </NavLink>
  )
}
