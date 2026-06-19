import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PartnerForm from '../components/PartnerForm'
import apiClient from '../api/client'
import { usePartner, PartnerProfile } from '../contexts/PartnerContext'
import '../styles/PartnerSetup.css'

/**
 * PartnerSetupPage component.
 * 
 * Renders the "Tell us about your partner" flow.
 * 
 * On mount, attempts to fetch GET /partner to see if profile already exists.
 * If profile exists, pre-populates the form for editing.
 * If no profile, renders empty form for initial setup.
 * 
 * UI states:
 * - loading: GET /partner is in flight
 * - form-ready: form is displayed (empty or pre-populated)
 * - no-auth: user is not authenticated (should not happen if ProtectedRoute works)
 * 
 * Client state: fetches profile once on mount; PartnerForm handles submission state.
 */
export default function PartnerSetup() {
  const navigate = useNavigate()
  const { setProfile } = usePartner()
  const [loading, setLoading] = useState(true)
  const [existingProfile, setExistingProfile] = useState<PartnerProfile | null>(null)

  useEffect(() => {
    /**
     * Fetch existing partner profile if any.
     * If 200, populate form with existing data.
     * If 404, form is empty (user hasn't set profile yet).
     * If 401, user is not authenticated (shouldn't happen).
     */
    const fetchProfile = async () => {
      try {
        const response = await apiClient.get<PartnerProfile>('/partner')
        if (response.status === 200) {
          setExistingProfile(response.data)
          setProfile(response.data) // Populate context for dashboard
        }
      } catch (error) {
        // 404 is expected — no profile yet, form will be empty
        const axiosError = error as any
        if (axiosError.response?.status === 401) {
          // Not authenticated — redirect to signin
          navigate('/signin')
        }
        // Otherwise (404 or network error), treat as "no profile yet"
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [navigate, setProfile])

  if (loading) {
    return (
      <div className="partner-setup-page">
        <div className="setup-container">
          <div className="loading">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="partner-setup-page">
      <div className="setup-container">
        <header className="setup-header">
          <h1>Tell us about your partner</h1>
          <p>So we can show you their local time, weather, and news.</p>
        </header>

        <PartnerForm initialProfile={existingProfile || undefined} />
      </div>
    </div>
  )
}
