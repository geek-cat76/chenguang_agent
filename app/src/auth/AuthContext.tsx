import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useQuery } from '@tanstack/react-query'
import { userApi } from '../services/api'
import { tokenStorage } from '../services/token'
import type { User } from '../types/api'
import { queryClient } from '../queryClient'

interface AuthContextValue {
  token: string | null
  user: User | undefined
  isLoading: boolean
  error: Error | null
  loginWithToken: (token: string) => Promise<void>
  logout: () => void
  retry: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)
const currentUserQueryKey = ['auth', 'current-user'] as const

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => tokenStorage.get())

  const currentUserQuery = useQuery({
    queryKey: currentUserQueryKey,
    queryFn: userApi.me,
    enabled: Boolean(token),
    retry: false,
  })

  const logout = useCallback(() => {
    tokenStorage.clear()
    setToken(null)
    queryClient.removeQueries({ queryKey: currentUserQueryKey })
  }, [])

  useEffect(() => {
    const handleUnauthorized = () => logout()
    window.addEventListener('chenguang:unauthorized', handleUnauthorized)
    return () =>
      window.removeEventListener('chenguang:unauthorized', handleUnauthorized)
  }, [logout])

  const loginWithToken = useCallback(async (accessToken: string) => {
    tokenStorage.set(accessToken)
    setToken(accessToken)

    try {
      await queryClient.fetchQuery({
        queryKey: currentUserQueryKey,
        queryFn: userApi.me,
      })
    } catch (error) {
      tokenStorage.clear()
      setToken(null)
      throw error
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user: currentUserQuery.data,
      isLoading: Boolean(token) && currentUserQuery.isLoading,
      error: currentUserQuery.error,
      loginWithToken,
      logout,
      retry: () => void currentUserQuery.refetch(),
    }),
    [
      token,
      currentUserQuery.data,
      currentUserQuery.isLoading,
      currentUserQuery.error,
      currentUserQuery.refetch,
      loginWithToken,
      logout,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth 必须在 AuthProvider 内使用')
  }
  return context
}
