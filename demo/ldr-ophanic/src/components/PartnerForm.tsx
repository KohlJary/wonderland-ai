import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { usePartner, PartnerProfile } from '../contexts/PartnerContext'
import '../styles/PartnerForm.css'

/**
 * PartnerForm component.
 * 
 * Contract: POSTs {name, city, country} to /partner.
 * Handles three response cases per contract-note-01KV9PFH:
 * 
 * 1. 200 OK — stores response in PartnerContext, navigates to dashboard
 * 2. 400 Bad Request — displays error message ("We couldn't find that city...")
 * 3. 409 Conflict — displays conflict message ("You've already set Sarah's location...")
 * 
 * UI states:
 * - idle: form is ready for input
 * - submitting: POST is in flight, submit button is disabled
 * - error: server returned 400 or 409, error message is shown
 * 
 * Client state: form inputs (name, city, country) are local state.
 * On success, PartnerContext.setProfile stores the resolved profile (with timezone, coordinates).
 */
export default function PartnerForm({ initialProfile }: { initialProfile?: PartnerProfile }) {
  const navigate = useNavigate()
  const { setProfile } = usePartner()

  const [name, setName] = useState(initialProfile?.name || '')
  const [city, setCity] = useState(initialProfile?.city || '')
  const [country, setCountry] = useState(initialProfile?.country || '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const response = await apiClient.post<PartnerProfile>('/partner', {
        name,
        city,
        country,
      })

      // 200 OK — store profile and navigate to dashboard
      if (response.status === 200) {
        setProfile(response.data)
        navigate('/dashboard')
      }
    } catch (err) {
      // Handle error responses
      if (err instanceof Error) {
        // Axios AxiosError has response field
        const axiosError = err as any
        if (axiosError.response?.status === 400) {
          // 400 Bad Request — geolocation failed or missing fields
          setError(
            axiosError.response.data?.error ||
              "We couldn't find that city; try spelling it differently."
          )
        } else if (axiosError.response?.status === 409) {
          // 409 Conflict — already have a profile for this user
          setError(
            axiosError.response.data?.error ||
              "You've already set Sarah's location. To change it, you'll need to delete the profile first and re-enter."
          )
        } else {
          // Other error (network, 5xx, etc.)
          setError('An error occurred. Please try again.')
        }
      } else {
        setError('An unknown error occurred.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="partner-form">
      <div className="form-group">
        <label htmlFor="name">Partner's Display Name</label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Sarah"
          required
          disabled={submitting}
        />
      </div>

      <div className="form-group">
        <label htmlFor="city">City</label>
        <input
          id="city"
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="e.g., Vienna"
          required
          disabled={submitting}
        />
      </div>

      <div className="form-group">
        <label htmlFor="country">Country</label>
        <input
          id="country"
          type="text"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          placeholder="e.g., Austria"
          required
          disabled={submitting}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      <button type="submit" disabled={submitting} className="submit-button">
        {submitting ? 'Setting up...' : 'Set Partner Profile'}
      </button>
    </form>
  )
}
