/**
 * hooks/index.js
 * Reusable custom hooks used across the app.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

// ── useLocalStorage ────────────────────────────────────────
export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch {
      return initialValue
    }
  })

  const setValue = (value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.error(error)
    }
  }

  return [storedValue, setValue]
}

// ── useAsync ───────────────────────────────────────────────
export function useAsync(asyncFn, deps = []) {
  const [data, setData]       = useState(null)
  const [error, setError]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    asyncFn()
      .then((result) => { if (!cancelled) setData(result) })
      .catch((err)   => { if (!cancelled) setError(err) })
      .finally(()    => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, loading }
}

// ── useFetch ───────────────────────────────────────────────
export function useFetch(url, params = {}) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const refetch = useCallback(async () => {
    if (!url) return
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.get(url, { params })
      setData(res.data?.data ?? res.data)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, [url, JSON.stringify(params)])

  useEffect(() => { refetch() }, [refetch])

  return { data, loading, error, refetch }
}

// ── useDebounce ────────────────────────────────────────────
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

// ── usePagination ──────────────────────────────────────────
export function usePagination(totalItems, perPage = 10) {
  const [page, setPage] = useState(1)
  const totalPages = Math.ceil(totalItems / perPage)

  return {
    page,
    totalPages,
    perPage,
    setPage,
    nextPage: () => setPage((p) => Math.min(p + 1, totalPages)),
    prevPage: () => setPage((p) => Math.max(p - 1, 1)),
    canNext: page < totalPages,
    canPrev: page > 1,
    offset: (page - 1) * perPage,
  }
}

// ── useClipboard ───────────────────────────────────────────
export function useClipboard(resetDelay = 2000) {
  const [copied, setCopied] = useState(false)

  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), resetDelay)
      return true
    } catch {
      toast.error('Failed to copy to clipboard')
      return false
    }
  }, [resetDelay])

  return { copied, copy }
}

// ── useTitle ───────────────────────────────────────────────
export function useTitle(title) {
  useEffect(() => {
    const prev = document.title
    document.title = title ? `${title} — Campus AI` : 'Campus AI'
    return () => { document.title = prev }
  }, [title])
}

// ── useOutsideClick ────────────────────────────────────────
export function useOutsideClick(callback) {
  const ref = useRef(null)
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) callback()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [callback])
  return ref
}
