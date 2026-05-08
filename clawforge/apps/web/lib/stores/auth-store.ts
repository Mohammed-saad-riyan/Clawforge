import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { createClient } from '@/lib/supabase/client'
import type { User, Session } from '@supabase/supabase-js'

interface AuthState {
  user: User | null
  session: Session | null
  isLoading: boolean
  isInitialized: boolean
  error: string | null
}

interface AuthActions {
  initialize: () => Promise<void>
  signUp: (email: string, password: string, fullName?: string) => Promise<{ error?: string; needsVerification?: boolean }>
  signIn: (email: string, password: string) => Promise<{ error?: string }>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<{ error?: string }>
  updatePassword: (newPassword: string) => Promise<{ error?: string }>
  setUser: (user: User | null) => void
  setSession: (session: Session | null) => void
  clearError: () => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      session: null,
      isLoading: false,
      isInitialized: false,
      error: null,

      // Actions
      initialize: async () => {
        const supabase = createClient()

        try {
          set({ isLoading: true })

          // Get current session
          const { data: { session }, error } = await supabase.auth.getSession()

          if (error) {
            console.error('Auth initialization error:', error)
            set({ error: error.message })
          }

          set({
            session,
            user: session?.user ?? null,
            isInitialized: true,
            isLoading: false
          })

          // Listen to auth state changes
          supabase.auth.onAuthStateChange((event, session) => {
            console.log('Auth state changed:', event)
            set({
              session,
              user: session?.user ?? null
            })
          })
        } catch (err) {
          console.error('Auth initialization failed:', err)
          set({
            isLoading: false,
            isInitialized: true,
            error: 'Failed to initialize authentication'
          })
        }
      },

      signUp: async (email, password, fullName) => {
        const supabase = createClient()
        set({ isLoading: true, error: null })

        try {
          const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
              data: {
                full_name: fullName,
              },
              emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
          })

          if (error) {
            set({ isLoading: false, error: error.message })
            return { error: error.message }
          }

          // Check if email confirmation is required
          if (data.user && !data.session) {
            set({ isLoading: false })
            return { needsVerification: true }
          }

          set({
            user: data.user,
            session: data.session,
            isLoading: false
          })
          return {}
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Sign up failed'
          set({ isLoading: false, error: message })
          return { error: message }
        }
      },

      signIn: async (email, password) => {
        const supabase = createClient()
        set({ isLoading: true, error: null })

        try {
          const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
          })

          if (error) {
            set({ isLoading: false, error: error.message })
            return { error: error.message }
          }

          set({
            user: data.user,
            session: data.session,
            isLoading: false
          })
          return {}
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Sign in failed'
          set({ isLoading: false, error: message })
          return { error: message }
        }
      },

      signOut: async () => {
        const supabase = createClient()
        set({ isLoading: true })

        try {
          await supabase.auth.signOut()
          set({
            user: null,
            session: null,
            isLoading: false
          })
        } catch (err) {
          console.error('Sign out error:', err)
          set({ isLoading: false })
        }
      },

      resetPassword: async (email) => {
        const supabase = createClient()
        set({ isLoading: true, error: null })

        try {
          const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`,
          })

          if (error) {
            set({ isLoading: false, error: error.message })
            return { error: error.message }
          }

          set({ isLoading: false })
          return {}
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Password reset failed'
          set({ isLoading: false, error: message })
          return { error: message }
        }
      },

      updatePassword: async (newPassword) => {
        const supabase = createClient()
        set({ isLoading: true, error: null })

        try {
          const { error } = await supabase.auth.updateUser({
            password: newPassword,
          })

          if (error) {
            set({ isLoading: false, error: error.message })
            return { error: error.message }
          }

          set({ isLoading: false })
          return {}
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Password update failed'
          set({ isLoading: false, error: message })
          return { error: message }
        }
      },

      setUser: (user) => set({ user }),
      setSession: (session) => set({ session, user: session?.user ?? null }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'clawforge-auth',
      partialize: (state) => ({
        // Only persist minimal auth indicator, not sensitive data
        // Actual session is managed by Supabase cookies
      }),
    }
  )
)
