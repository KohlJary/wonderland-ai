import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * ProtectedRoute guards a route to require authentication.
 * 
 * **Loading state:** while /auth/me is in flight, shows a minimal loading view.
 * This prevents race condition where dashboard briefly renders before auth 
 * check completes. Once loading=false, either:
 * - user is set: render children
 * - user is null: redirect to /signin
 * 
 * **UI states handled:**
 * - loading: shows "Loading..." view (could be enhanced with spinner)
 * - authenticated: renders children normally
 * - unauthenticated: redirects to /signin
 * 
 * **Known limitation:** redirect happens client-side (React Router).
 * If browser JS is disabled, this won't work (out of scope for v1).
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  // Loading state: show minimal UI while /auth/me is in flight
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <p>Loading...</p>
      </div>
    )
  }

  // Unauthenticated: redirect to signin
  if (!user) {
    navigate('/signin')
    return null
  }

  // Authenticated: render route
  return <>{children}</>
}
