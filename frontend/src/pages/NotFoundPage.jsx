import React from 'react'
import { Link } from 'react-router-dom'
import { Home, SearchX } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-dark-900 px-4 text-center">
      <SearchX className="w-16 h-16 text-gray-300 dark:text-dark-500 mb-4" />
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">404</h1>
      <p className="text-gray-500 dark:text-gray-400 mb-6">The page you're looking for doesn't exist.</p>
      <Link to="/dashboard" className="btn-primary">
        <Home className="w-4 h-4" /> Back to Dashboard
      </Link>
    </div>
  )
}
