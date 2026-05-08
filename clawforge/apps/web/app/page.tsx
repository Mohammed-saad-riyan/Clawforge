'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/stores/auth-store'
import {
  Plus,
  FolderGit2,
  Loader2,
  LogOut,
  User,
  Zap,
  Clock,
  DollarSign,
  GitBranch,
  MessageSquare,
  FileCode,
  ChevronRight,
  Settings,
} from 'lucide-react'

interface Project {
  id: string
  app_name: string
  app_idea: string
  github_repo: string | null
  total_cost_cents: number
  iteration_count: number
  created_at: string
  updated_at: string
}

interface DashboardStats {
  total_projects: number
  active_projects: number
  deployed_projects: number
  total_cost_cents: number
  cost_this_week_cents: number
  total_iterations: number
  total_messages: number
  total_files_generated: number
  recent_projects: Project[]
}

export default function Home() {
  const router = useRouter()
  const { user, signOut, isLoading: authLoading, initialize, isInitialized } = useAuthStore()

  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isInitialized) {
      initialize()
    }
  }, [isInitialized, initialize])

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch('/api/v1/dashboard')
        if (!response.ok) throw new Error('Failed to fetch dashboard')
        const data = await response.json()
        setStats(data)
      } catch (err) {
        console.error('Dashboard fetch error:', err)
        setError('Failed to load dashboard data')
      } finally {
        setIsLoading(false)
      }
    }

    if (isInitialized) {
      fetchDashboard()
    }
  }, [isInitialized])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const formatCost = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  if (!isInitialized || authLoading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-amber-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">CF</span>
            </div>
            <span className="text-xl font-semibold text-white">ClawForge</span>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              href="/new"
              className="bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Project
            </Link>

            <div className="relative group">
              <button className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
                <span className="text-sm">{user?.email?.split('@')[0]}</span>
              </button>

              {/* Dropdown */}
              <div className="absolute right-0 top-full mt-2 w-48 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <div className="p-2">
                  <div className="px-3 py-2 border-b border-zinc-800">
                    <p className="text-sm text-white font-medium truncate">{user?.email}</p>
                    <p className="text-xs text-zinc-500">
                      Member since {user?.created_at ? formatDate(user.created_at) : 'N/A'}
                    </p>
                  </div>
                  <Link
                    href="/settings"
                    className="flex items-center gap-2 px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md transition-colors mt-1"
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </Link>
                  <button
                    onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-zinc-800 rounded-md transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">
            Welcome back, {user?.user_metadata?.full_name || user?.email?.split('@')[0]}
          </h1>
          <p className="text-zinc-400 mt-1">Here&apos;s an overview of your ClawForge projects</p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-red-400">
            {error}
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                    <FolderGit2 className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats?.total_projects || 0}</p>
                    <p className="text-sm text-zinc-400">Total Projects</p>
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats?.deployed_projects || 0}</p>
                    <p className="text-sm text-zinc-400">Deployed</p>
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{stats?.total_iterations || 0}</p>
                    <p className="text-sm text-zinc-400">Total Iterations</p>
                  </div>
                </div>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">
                      {formatCost(stats?.total_cost_cents || 0)}
                    </p>
                    <p className="text-sm text-zinc-400">Total Cost</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Projects */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg">
              <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">Recent Projects</h2>
                <Link
                  href="/new"
                  className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
                >
                  New Project
                </Link>
              </div>

              {stats?.recent_projects && stats.recent_projects.length > 0 ? (
                <div className="divide-y divide-zinc-800">
                  {stats.recent_projects.map((project) => (
                    <Link
                      key={project.id}
                      href={`/project/${project.id}`}
                      className="flex items-center justify-between px-4 py-3 hover:bg-zinc-800/50 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                          <FileCode className="w-5 h-5 text-zinc-400" />
                        </div>
                        <div>
                          <p className="text-white font-medium">{project.app_name}</p>
                          <p className="text-sm text-zinc-500 line-clamp-1 max-w-md">
                            {project.app_idea}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        {project.github_repo && (
                          <div className="flex items-center gap-1.5 text-zinc-500">
                            <GitBranch className="w-4 h-4" />
                            <span className="text-sm">{project.github_repo.split('/').pop()}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-1.5 text-zinc-500">
                          <Clock className="w-4 h-4" />
                          <span className="text-sm">{formatDate(project.updated_at)}</span>
                        </div>
                        <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="px-4 py-12 text-center">
                  <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mx-auto mb-4">
                    <FolderGit2 className="w-8 h-8 text-zinc-600" />
                  </div>
                  <h3 className="text-white font-medium mb-1">No projects yet</h3>
                  <p className="text-zinc-500 text-sm mb-4">
                    Create your first Flutter app with AI
                  </p>
                  <Link
                    href="/new"
                    className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    New Project
                  </Link>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-400 text-sm">Files Generated</span>
                  <FileCode className="w-4 h-4 text-zinc-500" />
                </div>
                <p className="text-2xl font-bold text-white">{stats?.total_files_generated || 0}</p>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-400 text-sm">Chat Messages</span>
                  <MessageSquare className="w-4 h-4 text-zinc-500" />
                </div>
                <p className="text-2xl font-bold text-white">{stats?.total_messages || 0}</p>
              </div>

              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-zinc-400 text-sm">Cost This Week</span>
                  <DollarSign className="w-4 h-4 text-zinc-500" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {formatCost(stats?.cost_this_week_cents || 0)}
                </p>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
