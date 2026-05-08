'use client'

import Link from 'next/link'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-amber-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">CF</span>
          </div>
          <span className="text-xl font-semibold text-white">ClawForge</span>
        </Link>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-6 py-4 text-center text-zinc-500 text-sm">
        <p>&copy; {new Date().getFullYear()} ClawForge. AI-powered Flutter app generation.</p>
      </footer>
    </div>
  )
}
