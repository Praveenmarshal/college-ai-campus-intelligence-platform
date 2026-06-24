/**
 * context/AuthContext.jsx
 * Global authentication state.
 * Provides: user, isAuthenticated, login, googleLogin, logout, register.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import toast from 'react-hot-toast'
import { authAPI } from '../api/services'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]               = useState(null)
  const [isLoading, setIsLoading]     = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // ── Bootstrap — restore session from localStorage ──────
  useEffect(() => {
    const storedUser  = localStorage.getItem('user')
    const accessToken = localStorage.getItem('access_token')

    if (storedUser && accessToken) {
      try {
        setUser(JSON.parse(storedUser))
        setIsAuthenticated(true)
      } catch {
        _clearSession()
      }
    }
    setIsLoading(false)
  }, [])

  // ── Login (email/password — kept as fallback) ──────────
  const login = useCallback(async (email, password) => {
    setIsLoading(true)
    try {
      const { data } = await authAPI.login({ email, password })
      const { user: userData, access_token, refresh_token } = data.data

      localStorage.setItem('access_token',  access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user',          JSON.stringify(userData))

      setUser(userData)
      setIsAuthenticated(true)
      toast.success(`Welcome back, ${userData.name}!`)
      return { success: true, user: userData }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Login failed'
      toast.error(msg)
      return { success: false, error: msg }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // ── Google OAuth Login ─────────────────────────────────
  const googleLogin = useCallback(async (credential) => {
    setIsLoading(true)
    try {
      const { data } = await authAPI.googleLogin(credential)
      const { user: userData, access_token, refresh_token } = data.data

      localStorage.setItem('access_token',  access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user',          JSON.stringify(userData))

      setUser(userData)
      setIsAuthenticated(true)
      toast.success(`Welcome, ${userData.name}!`)
      return { success: true, user: userData }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Google login failed'
      toast.error(msg)
      return { success: false, error: msg }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // ── Register ───────────────────────────────────────────
  const register = useCallback(async (formData) => {
    setIsLoading(true)
    try {
      const { data } = await authAPI.register(formData)
      toast.success('Account created! Please log in.')
      return { success: true }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Registration failed'
      toast.error(msg)
      return { success: false, error: msg }
    } finally {
      setIsLoading(false)
    }
  }, [])

  // ── Logout ─────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await authAPI.logout()
    } catch {
      // silent — clear local state regardless
    } finally {
      _clearSession()
      toast.success('Logged out successfully')
    }
  }, [])

  // ── Update user in context (after profile edit) ────────
  const updateUser = useCallback((updated) => {
    const merged = { ...user, ...updated }
    setUser(merged)
    localStorage.setItem('user', JSON.stringify(merged))
  }, [user])

  // ── Helpers ────────────────────────────────────────────
  function _clearSession() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
    setIsAuthenticated(false)
  }

  const hasRole = (role) => user?.role === role
  const hasAnyRole = (roles) => roles.includes(user?.role)

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        googleLogin,
        logout,
        register,
        updateUser,
        hasRole,
        hasAnyRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
