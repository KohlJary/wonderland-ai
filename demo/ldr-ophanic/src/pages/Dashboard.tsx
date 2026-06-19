import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { usePartner, PartnerProfile } from '../contexts/PartnerContext'
import TimeCard from '../components/TimeCard'
import WeatherCard from '../components/WeatherCard'
import NewsCard from '../components/NewsCard'
import '../styles/Dashboard.css'

/**
 * Dashboard response type (from GET /api/dashboard).
 * Includes partner timezone for time card, weather and news data.
 */
interface WeatherResponse {
  current_conditions: string | null
  temp_f: number | null
  is_stale: boolean
  last_updated_at: string | null
  error: 'not_yet_available' | 'unavailable' | 'degraded' | null
}

interface NewsResponse {
  headlines: { title: string; excerpt: string; source: string; url: string }[] | null
  is_stale: boolean
  last_updated_at: string | null
  error: 'not_yet_available' | 'unavailable' | 'degraded' | null
}

interface DashboardResponse {
  partner_timezone: string
  weather: WeatherResponse
  news: NewsResponse
}

/**
 * Dashboard page component.
 * 
 * On mount, fetches GET /api/dashboard to retrieve the authenticated user's dashboard data:
 * weather cache, news cache, and timezone.
 * Also fetches GET /partner separately to populate PartnerContext for TimeCard + WeatherCard display.
 * If no profile exists (404), redirects to /partner-setup so user can set up first.
 * 
 * Contract assumptions:
 * - GET /api/dashboard returns DashboardResponse { partner_timezone, weather, news }
 * - GET /partner returns PartnerProfile { partner_id, name, city, country, iana_timezone, latitude, longitude, created_at }
 * - GET /api/dashboard returns 404 if no partner profile has been set (same condition as GET /partner)
 * - Session is validated by ProtectedRoute before this component mounts
 * 
 * UI states:
 * - loading: both GET /partner and GET /api/dashboard are in flight
 * - dashboard-ready: both profile and dashboard data loaded, cards can render
 * - no-profile: 404 from either endpoint, redirect to partner-setup
 * - degraded: dashboard data loaded but weather/news show error states
 * 
 * Client state:
 * - profile: partner profile (from PartnerContext)
 * - dashboardData: dashboard response (weather, news, timezone) — stored locally to avoid context sprawl
 */
export default function Dashboard() {
  const navigate = useNavigate()
  const { profile, setProfile } = usePartner()
  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null)

  useEffect(() => {
    /**
     * Fetch both partner profile and dashboard data on mount.
     * Partner profile is needed for display names in cards.
     * Dashboard data provides weather, news, and timezone confirmation.
     * 
     * If no profile (404 from either endpoint), redirect to /partner-setup.
     * If 401, user is not authenticated (shouldn't happen if ProtectedRoute works).
     * Network errors: let user stay on dashboard; cards will show placeholders.
     */
    const fetchDashboard = async () => {
      try {
        // Fetch dashboard data (includes weather, news, timezone)
        const dashboardResponse = await apiClient.get<DashboardResponse>('/dashboard')
        if (dashboardResponse.status === 200) {
          setDashboardData(dashboardResponse.data)
        }
      } catch (error) {
        const axiosError = error as any
        if (axiosError.response?.status === 404) {
          // No profile set yet — redirect to setup
          navigate('/partner-setup')
          return
        } else if (axiosError.response?.status === 401) {
          // Not authenticated (shouldn't happen)
          navigate('/signin')
          return
        }
        // Other errors (network): let user stay on dashboard; cards will show placeholder
      }
    }

    // Fetch partner profile (for name display)
    const fetchPartnerProfile = async () => {
      try {
        const response = await apiClient.get<PartnerProfile>('/partner')
        if (response.status === 200) {
          setProfile(response.data)
        }
      } catch (error) {
        const axiosError = error as any
        if (axiosError.response?.status === 404) {
          // No profile set yet — redirect to setup
          navigate('/partner-setup')
          return
        } else if (axiosError.response?.status === 401) {
          // Not authenticated (shouldn't happen)
          navigate('/signin')
          return
        }
        // Other errors (network): let user stay on dashboard; cards will show placeholder
      }
    }

    // Only fetch if profile is not already in context
    if (!profile) {
      fetchPartnerProfile()
    }

    // Always fetch dashboard data (weather, news, timezone)
    fetchDashboard()
  }, [profile, setProfile, navigate])

  return (
    <div className="dashboard-container">
      <h1>Dashboard</h1>
      <div className="cards-grid">
        <TimeCard profile={profile} />
        <WeatherCard
          weather={dashboardData?.weather}
          partnerName={profile?.name}
        />
        <NewsCard
          news={dashboardData?.news}
          partnerName={profile?.name}
        />
      </div>
    </div>
  )
}
