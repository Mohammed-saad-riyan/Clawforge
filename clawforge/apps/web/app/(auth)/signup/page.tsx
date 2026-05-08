'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/stores/auth-store'
import { Mail, Lock, User, Loader2, AlertCircle, Check } from 'lucide-react'

export default function SignUpPage() {
  const router = useRouter()
  const { signUp, isLoading, error, clearError, user, initialize, isInitialized } = useAuthStore()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!isInitialized) {
      initialize()
    }
  }, [isInitialized, initialize])

  useEffect(() => {
    if (user) {
      router.push('/')
    }
  }, [user, router])

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

    // Validate fields
    if (!fullName || !email || !password || !confirmPassword) {
      setLocalError('Please fill in all fields')
      return
    }

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

    const result = await signUp(email, password, fullName)

    if (result.error) {
      setLocalError(result.error)
    } else if (result.needsVerification) {
      setSuccess(true)
    } else {
      router.push('/')
    }
  }

  const displayError = localError || error

  // Success state - email verification needed
  if (success) {
    return (
      <div className="space-y-6 text-center">
        <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto">
          <Mail className="w-8 h-8 text-green-400" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white">Check your email</h1>
          <p className="text-zinc-400">
            We&apos;ve sent a verification link to <span className="text-white font-medium">{email}</span>
          </p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-left">
          <h3 className="text-sm font-medium text-white mb-2">Next steps:</h3>
          <ol className="text-sm text-zinc-400 space-y-2">
            <li className="flex items-start gap-2">
              <span className="w-5 h-5 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0 text-xs">1</span>
              Open the email we sent you
            </li>
            <li className="flex items-start gap-2">
              <span className="w-5 h-5 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0 text-xs">2</span>
              Click the verification link
            </li>
            <li className="flex items-start gap-2">
              <span className="w-5 h-5 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0 text-xs">3</span>
              Start building Flutter apps with AI
            </li>
          </ol>
        </div>
        <p className="text-sm text-zinc-500">
          Didn&apos;t receive the email?{' '}
          <button
            onClick={() => setSuccess(false)}
            className="text-violet-400 hover:text-violet-300 transition-colors"
          >
            Try again
          </button>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-white">Create your account</h1>
        <p className="text-zinc-400">Start building Flutter apps with AI</p>
      </div>

      {/* Error Alert */}
      {displayError && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <p className="text-red-400 text-sm">{displayError}</p>
        </div>
      )}

      {/* Sign Up Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full Name */}
        <div className="space-y-2">
          <label htmlFor="fullName" className="text-sm font-medium text-zinc-300">
            Full Name
          </label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
              disabled={isLoading}
            />
          </div>
        </div>

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
            />
          </div>
        </div>

        {/* Password */}
        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium text-zinc-300">
            Password
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
            Confirm Password
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
              Creating account...
            </>
          ) : (
            'Create account'
          )}
        </button>
      </form>

      {/* Terms */}
      <p className="text-xs text-zinc-500 text-center">
        By creating an account, you agree to our{' '}
        <Link href="/terms" className="text-violet-400 hover:text-violet-300">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="/privacy" className="text-violet-400 hover:text-violet-300">
          Privacy Policy
        </Link>
      </p>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-zinc-800" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-zinc-950 text-zinc-500">Already have an account?</span>
        </div>
      </div>

      {/* Sign In Link */}
      <Link
        href="/login"
        className="w-full block text-center border border-zinc-800 hover:border-zinc-700 text-white font-medium rounded-lg py-3 transition-colors"
      >
        Sign in
      </Link>
    </div>
  )
}
