'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/lib/stores/auth-store'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { initialize, isInitialized } = useAuthStore()

  useEffect(() => {
    if (!isInitialized) {
      initialize()
    }
  }, [isInitialized, initialize])

  return <>{children}</>
}
