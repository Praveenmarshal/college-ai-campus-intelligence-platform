/**
 * components/layout/Topbar.jsx
 * Top navigation bar: menu toggle, search, theme, notifications, profile.
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Menu, Sun, Moon, Bell, Search, PanelLeft } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'

export default function Topbar({ onMenuClick, onToggleSidebar }) {
  const { user } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/chat?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  return (
    <header className="h-16 flex items-center gap-3 px-4 border-b border-gray-100 dark:border-dark-600 bg-white dark:bg-dark-800 shrink-0">

      {/* Mobile menu */}
      <button
        onClick={onMenuClick}
        className="btn-ghost p-2 lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Desktop sidebar toggle */}
      <button
        onClick={onToggleSidebar}
        className="btn-ghost p-2 hidden lg:flex"
        aria-label="Toggle sidebar"
      >
        <PanelLeft className="w-5 h-5" />
      </button>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Ask anything about campus…"
            className="input pl-9 py-1.5 text-sm"
          />
        </div>
      </form>

      <div className="flex items-center gap-1 ml-auto">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="btn-ghost p-2"
          aria-label="Toggle theme"
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/notifications')}
          className="btn-ghost p-2 relative"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* Avatar */}
        <button
          onClick={() => navigate('/profile')}
          className="ml-1 w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent-500 flex items-center justify-center"
          aria-label="Profile"
        >
          <span className="text-xs font-bold text-white">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </span>
        </button>
      </div>
    </header>
  )
}
