import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { PartnerProvider } from './contexts/PartnerContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import Signup from './pages/Signup'
import Signin from './pages/Signin'
import Dashboard from './pages/Dashboard'
import PartnerSetup from './pages/PartnerSetup'

/**
 * App is the root component.
 * 
 * Structure:
 * - BrowserRouter: enables client-side routing
 * - AuthProvider: wraps routes, bootstraps auth state on mount (GET /auth/me)
 * - Routes:
 *   - /signup: Signup page (public)
 *   - /signin: Signin page (public)
 *   - /dashboard: Dashboard page (protected — requires authentication)
 *   - /: redirects to /signin (unauthenticated users see signin; authenticated see dashboard)
 * 
 * **Contract assumptions:**
 * - Backend provides GET /auth/me endpoint (AuthContext.tsx)
 * - Backend provides POST /auth/signup, POST /auth/signin, POST /auth/signout endpoints
 * - Session is cookie-based (backend sets signed cookie; frontend sends it automatically)
 * - ProtectedRoute guards /dashboard; unauthenticated access redirects to /signin
 * 
 * **Client state:**
 * - Auth state (user, loading) lives in AuthContext
 * - No app-wide state beyond auth (partner profile, dashboard data will be fetched per-route)
 * 
 * **UI states implemented:**
 * - loading: AuthProvider's useEffect fetches /auth/me; ProtectedRoute shows "Loading..." while in flight
 * - authenticated: user is set, /dashboard renders
 * - unauthenticated: user is null, redirect to /signin
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PartnerProvider>
          <Routes>
            <Route path="/signup" element={<Signup />} />
            <Route path="/signin" element={<Signin />} />
            <Route
              path="/partner-setup"
              element={
                <ProtectedRoute>
                  <PartnerSetup />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/signin" replace />} />
          </Routes>
        </PartnerProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
