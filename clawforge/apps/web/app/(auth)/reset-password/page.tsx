'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/stores/auth-store'
import { Lock, Loader2, AlertCircle, Check, CheckCircle } from 'lucide-react'

export default function ResetPasswordPage() {
  const router = useRouter()
  const { updatePassword, isLoading, error, clearError, initialize, isInitialized } = useAuthStore()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!isInitialized) {
      initialize()
    }
  }, [isInitialized, initialize])

  const validatePassword = (pwd: string) => {
    if (pwd.length < 8) return 'Password must be at least 8 characters'
    if (!/[A-Z]/.test(pwd)) return 'Password must contain at least one uppercase letter'
    if (!/[a-z]/.test(pwd)) return 'Password must contain at least one lowercase letter'
    if (!/[0-9]/.test(pwd)) return 'Password must contain at least one number'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError(null)
    clearError()

    // Validate password
    const passwordError = validatePassword(password)
    if (passwordError) {
      setLocalError(passwordError)
      return
    }

    // Check passwords match
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match')
      return
    }

    const result = await updatePassword(password)

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
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white">Password updated</h1>
          <p className="text-zinc-400">
            Your password has been successfully updated. You can now sign in with your new password.
          </p>
        </div>
        <Link
          href="/login"
          className="w-full block text-center bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-lg py-3 transition-colors"
        >
          Sign in
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-white">Reset your password</h1>
        <p className="text-zinc-400">
          Enter your new password below.
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
        {/* New Password */}
        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium text-zinc-300">
            New Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isLoading}
              autoFocus
            />
          </div>
          <ul className="text-xs text-zinc-500 space-y-1 ml-1">
            <li className={`flex items-center gap-1.5 ${password.length >= 8 ? 'text-green-400' : ''}`}>
              <Check className="w-3 h-3" /> At least 8 characters
            </li>
            <li className={`flex items-center gap-1.5 ${/[A-Z]/.test(password) ? 'text-green-400' : ''}`}>
              <Check className="w-3 h-3" /> One uppercase letter
            </li>
            <li className={`flex items-center gap-1.5 ${/[0-9]/.test(password) ? 'text-green-400' : ''}`}>
              <Check className="w-3 h-3" /> One number
            </li>
          </ul>
        </div>

        {/* Confirm Password */}
        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="text-sm font-medium text-zinc-300">
            Confirm New Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isLoading}
            />
          </div>
          {confirmPassword && password !== confirmPassword && (
            <p className="text-xs text-red-400 ml-1">Passwords do not match</p>
          )}
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
              Updating password...
            </>
          ) : (
            'Update password'
          )}
        </button>
      </form>
    </div>
  )
}
