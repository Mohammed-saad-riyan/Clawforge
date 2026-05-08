'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuthStore } from '@/lib/stores/auth-store'
import { Mail, Loader2, AlertCircle, ArrowLeft } from 'lucide-react'

export default function ForgotPasswordPage() {
  const { resetPassword, isLoading, error, clearError } = useAuthStore()

  const [email, setEmail] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    clearError()

    if (!email) {
      setLocalError('Please enter your email address')
      return
    }

    const result = await resetPassword(email)

    if (result.error) {
      setLocalError(result.error)
    } else {
      setSuccess(true)
    }
  }

  const displayError = localError || error

  // Success state
  if (success) {
    return (
      <div className="space-y-6 text-center">
        <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto">
          <Mail className="w-8 h-8 text-green-400" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white">Check your email</h1>
          <p className="text-zinc-400">
            If an account exists for <span className="text-white font-medium">{email}</span>,
            we&apos;ve sent password reset instructions.
          </p>
        </div>
        <div className="space-y-3">
          <Link
            href="/login"
            className="w-full block text-center bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-lg py-3 transition-colors"
          >
            Back to sign in
          </Link>
          <button
            onClick={() => {
              setSuccess(false)
              setEmail('')
            }}
            className="w-full text-center text-zinc-400 hover:text-white text-sm transition-colors"
          >
            Try a different email
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link
        href="/login"
        className="inline-flex items-center gap-2 text-zinc-400 hover:text-white text-sm transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to sign in
      </Link>

      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white">Forgot your password?</h1>
        <p className="text-zinc-400">
          Enter your email address and we&apos;ll send you a link to reset your password.
        </p>
      </div>

      {/* Error Alert */}
      {displayError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <p className="text-red-400 text-sm">{displayError}</p>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email */}
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium text-zinc-300">
            Email
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isLoading}
              autoFocus
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 disabled:cursor-not-allowed text-white font-medium rounded-lg py-3 flex items-center justify-center gap-2 transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Sending...
            </>
          ) : (
            'Send reset link'
          )}
        </button>
      </form>
    </div>
  )
}
