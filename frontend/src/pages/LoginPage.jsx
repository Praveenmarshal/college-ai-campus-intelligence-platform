/**
 * pages/LoginPage.jsx — Google OAuth login
 * Beautiful "Continue with Google" login page.
 */
import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { BrainCircuit, Loader2 } from 'lucide-react'
import { useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/index'

export default function LoginPage() {
  useTitle('Login')
  const { googleLogin, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true })
  }, [isAuthenticated])

  const handleGoogleLogin = useGoogleLogin({
    flow: 'implicit',
    onSuccess: async (tokenResponse) => {
      setLoading(true)
      setError('')
      try {
        // Use the access token to get user info, then pass the id_token
        // With implicit flow, we get access_token — we need to exchange it
        // Actually, let's use the credential flow instead
        // We'll fetch the user's info using the access_token
        const userInfoRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        })
        const userInfo = await userInfoRes.json()

        // Send the access token to our backend
        const result = await googleLogin(tokenResponse.access_token)
        if (result.success) {
          navigate(from, { replace: true })
        } else {
          setError(result.error)
        }
      } catch (err) {
        setError('Google login failed. Please try again.')
      } finally {
        setLoading(false)
      }
    },
    onError: (err) => {
      console.error('Google login error:', err)
      setError('Google login was cancelled or failed.')
    },
  })

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-dark-900">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-accent-600 flex-col items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        <div className="relative z-10 text-center text-white max-w-md">
          <div className="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center mx-auto mb-6">
            <BrainCircuit className="w-11 h-11 text-white" />
          </div>
          <h1 className="text-3xl font-bold mb-3">AI Campus Intelligence</h1>
          <p className="text-primary-200 text-lg leading-relaxed">
            Your unified AI-powered educational operating system — powered by local LLMs.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-4 text-left">
            {[
              ['📄', 'PDF RAG Engine', 'Ask questions about any document'],
              ['📊', 'Excel Analytics', 'Natural language data queries'],
              ['🧠', 'Multi-Agent AI', '9 specialised AI agents'],
              ['🔮', 'ML Predictions', 'Attendance & placement forecasts'],
            ].map(([icon, title, desc]) => (
              <div key={title} className="bg-white/10 rounded-xl p-4">
                <div className="text-2xl mb-2">{icon}</div>
                <div className="font-medium text-sm">{title}</div>
                <div className="text-primary-300 text-xs mt-1">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — Google login */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <BrainCircuit className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-gray-900 dark:text-white">Campus AI</span>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">Welcome</h2>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-8">
            Sign in to your account to continue
          </p>

          {error && (
            <div className="mb-6 p-3 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Google Sign-In Button */}
          <button
            onClick={() => handleGoogleLogin()}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-6 py-3.5 rounded-xl
                       bg-white dark:bg-dark-700 border-2 border-gray-200 dark:border-dark-500
                       hover:border-primary-400 dark:hover:border-primary-500
                       hover:shadow-lg hover:shadow-primary-500/10
                       transition-all duration-200 group
                       disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
            ) : (
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
            )}
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-200 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
              {loading ? 'Signing in…' : 'Continue with Google'}
            </span>
          </button>

          {/* Divider */}
          <div className="mt-8 flex items-center gap-4">
            <div className="flex-1 h-px bg-gray-200 dark:bg-dark-600" />
            <span className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider">Secured by</span>
            <div className="flex-1 h-px bg-gray-200 dark:bg-dark-600" />
          </div>

          {/* Security info */}
          <div className="mt-6 text-center space-y-2">
            <div className="flex items-center justify-center gap-2 text-xs text-gray-400 dark:text-gray-500">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>Your data is encrypted and secure</span>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500">
              By signing in, you agree to our terms of service and privacy policy
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
