/**
 * routes/RoleRoute.jsx
 * Restricts routes to users with specific roles.
 * Redirects to /dashboard with a toast if unauthorised.
 */

import React, { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'

export default function RoleRoute({ allowedRoles = [] }) {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated) return <Navigate to="/login" replace />

  const hasPermission = allowedRoles.includes(user?.role)

  useEffect(() => {
    if (!hasPermission) {
      toast.error("You don't have permission to access that page.")
    }
  }, [hasPermission])

  if (!hasPermission) return <Navigate to="/dashboard" replace />

  return <Outlet />
}
