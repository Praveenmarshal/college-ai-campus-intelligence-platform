/**
 * components/common/LoadingScreen.jsx
 * Full-screen loading spinner shown during auth bootstrap.
 */

import React from 'react'
import { BrainCircuit } from 'lucide-react'

export default function LoadingScreen() {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-dark-900 z-50">
      <div className="relative">
        {/* Outer spin ring */}
        <div className="w-16 h-16 rounded-full border-4 border-primary-100 dark:border-primary-950 border-t-primary-500 animate-spin" />
        {/* Inner icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <BrainCircuit className="w-7 h-7 text-primary-500 animate-pulse-slow" />
        </div>
      </div>
      <p className="mt-4 text-sm text-gray-500 dark:text-gray-400 font-medium">
        Loading Campus AI…
      </p>
    </div>
  )
}
