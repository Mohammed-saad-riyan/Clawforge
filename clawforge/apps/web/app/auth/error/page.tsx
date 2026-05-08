'use client'

import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { AlertCircle } from 'lucide-react'

export default function AuthErrorPage() {
  const searchParams = useSearchParams()
  const message = searchParams.get('message') || 'An authentication error occurred'

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6 text-center">
        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle className="w-8 h-8 text-red-400" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white">Authentication Error</h1>
          <p className="text-zinc-400">{message}</p>
        </div>
        <div className="space-y-3">
          <Link
            href="/login"
            className="w-full block text-center bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-lg py-3 transition-colors"
          >
            Back to sign in
          </Link>
          <Link
            href="/"
            className="w-full block text-center text-zinc-400 hover:text-white text-sm transition-colors"
          >
            Go to homepage
          </Link>
        </div>
      </div>
    </div>
  )
}
