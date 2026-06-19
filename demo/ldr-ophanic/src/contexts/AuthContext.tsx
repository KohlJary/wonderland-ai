import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import apiClient from '../api/client'

/**
 * User type matching backend UserResponse contract
 */
export interface User {
  id: number
  email: string
  created_at: string
}

/**
 * AuthContext provides:
 * - user: current authenticated user (null if not authenticated)
 * - loading: boolean while /auth/me call is in flight (prevents race conditions)
 * - logout: function to clear session and reset state
 */
interface AuthContextType {
  user: User | null
  loading: boolean
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export interface AuthProviderProps {
  children: ReactNode
}

/**
 * AuthProvider wraps the app, bootstraps auth state on mount.
 * 
 * On mount: calls GET /auth/me to validate session cookie
 * - 200: stores user in context, sets loading=false
 * - 401: user stays null, sets loading=false (triggers redirect to signin)
 * - Other errors: logs but treats as unauthenticated (loading=false, user=null)
 * 
 * Client state: user (in context) is the canonical auth state.
 * Reconciles with backend: /auth/me call happens once on mount; 
 * after that, frontend trusts the session cookie (backend validates).
 * Sign-in/signup operations update user; sign-out clears it.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    /**
     * Bootstrap: call GET /auth/me to validate session + populate user.
     * Handles the "page refresh" case — if cookie is valid, user is restored.
     */
    const bootstrapAuth = async () => {
      try {
        const response = await apiClient.get<User>('/auth/me')
        setUser(response.data)
      } catch (error) {
        // 401 or network error — user is unauthenticated
        // Don't log; this is expected when no session cookie exists
        setUser(null)
      } finally {
        // Mark loading complete, allowing ProtectedRoute to render
        setLoading(false)
      }
    }

    bootstrapAuth()
  }, [])

  const logout = async () => {
    try {
      // POST /auth/signout clears cookie and server session (if implemented)
      // Timeout 5s per contract note: if backend unreachable, clear state anyway
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Logout timeout')), 5000)
      )
      await Promise.race([apiClient.post('/auth/signout'), timeoutPromise])
    } catch (error) {
      // Even if sign-out fails, clear client state to avoid UI hang
      console.warn('Sign-out error; clearing client state anyway', error)
    } finally {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook: useAuth — access auth state and logout function.
 * Throws if used outside AuthProvider.
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
