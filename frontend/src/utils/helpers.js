/**
 * utils/helpers.js
 * Common utility functions used across the frontend.
 */

import { format, formatDistanceToNow, parseISO } from 'date-fns'

// ── Date formatting ────────────────────────────────────────

export const formatDate = (dateStr, fmt = 'dd MMM yyyy') => {
  if (!dateStr) return '—'
  try {
    return format(typeof dateStr === 'string' ? parseISO(dateStr) : dateStr, fmt)
  } catch {
    return '—'
  }
}

export const formatDateTime = (dateStr) => formatDate(dateStr, 'dd MMM yyyy, h:mm a')

export const timeAgo = (dateStr) => {
  if (!dateStr) return '—'
  try {
    return formatDistanceToNow(
      typeof dateStr === 'string' ? parseISO(dateStr) : dateStr,
      { addSuffix: true }
    )
  } catch {
    return '—'
  }
}

// ── Number formatting ──────────────────────────────────────

export const formatNumber = (n, decimals = 0) => {
  if (n == null) return '—'
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export const formatCurrency = (n, currency = '₹') => {
  if (n == null) return '—'
  return `${currency}${formatNumber(n, 2)}`
}

export const formatPercent = (n, decimals = 1) => {
  if (n == null) return '—'
  return `${Number(n).toFixed(decimals)}%`
}

// ── File size ──────────────────────────────────────────────

export const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let i = 0
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

// ── String utils ───────────────────────────────────────────

export const capitalize = (s) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1) : ''

export const truncate = (s, max = 80) =>
  s && s.length > max ? `${s.slice(0, max)}…` : s

export const initials = (name) => {
  if (!name) return 'U'
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

// ── Attendance helpers ─────────────────────────────────────

export const attendanceStatus = (pct) => {
  if (pct >= 85) return { label: 'Good',     color: 'success' }
  if (pct >= 75) return { label: 'Average',  color: 'warning' }
  return            { label: 'At Risk',   color: 'danger'  }
}

// ── Grade helpers ──────────────────────────────────────────

export const cgpaGrade = (cgpa) => {
  if (cgpa >= 9.0) return 'O (Outstanding)'
  if (cgpa >= 8.0) return 'A+ (Excellent)'
  if (cgpa >= 7.0) return 'A (Very Good)'
  if (cgpa >= 6.0) return 'B+ (Good)'
  if (cgpa >= 5.0) return 'B (Above Average)'
  return 'C (Average)'
}

// ── Clipboard ──────────────────────────────────────────────

export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

// ── Debounce ───────────────────────────────────────────────

export const debounce = (fn, delay = 300) => {
  let timer
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

// ── Download helper ────────────────────────────────────────

export const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// ── Chart colour palette ───────────────────────────────────

export const CHART_COLORS = [
  '#6366f1', '#06b6d4', '#22c55e', '#f59e0b',
  '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6',
  '#f97316', '#84cc16',
]

export const chartColorAlpha = (hex, alpha = 0.2) => {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}
