import { createContext, useContext, useState, ReactNode } from 'react'

/**
 * Partner profile type matching POST /partner response contract.
 * Returned by backend on successful POST /partner.
 * 
 * Schema: { partner_id, name, city, country, iana_timezone, latitude, longitude, created_at }
 */
export interface PartnerProfile {
  partner_id: number
  name: string
  city: string
  country: string
  iana_timezone: string
  latitude: number
  longitude: number
  created_at: string
}

/**
 * PartnerContext provides:
 * - profile: current partner profile (null if not set)
 * - setProfile: function to store profile in state after successful POST /partner
 * - clearProfile: function to clear profile (on logout or explicit action)
 */
interface PartnerContextType {
  profile: PartnerProfile | null
  setProfile: (profile: PartnerProfile) => void
  clearProfile: () => void
}

const PartnerContext = createContext<PartnerContextType | undefined>(undefined)

export interface PartnerProviderProps {
  children: ReactNode
}

/**
 * PartnerProvider wraps the app, manages partner profile state.
 * 
 * Client state: partner profile (in context) is the cached version.
 * Reconciles with backend: Dashboard fetches GET /partner on mount to populate;
 * PartnerForm POSTs to /partner and updates context on success.
 * No persistence beyond the session — profile is cleared on app unmount.
 * 
 * Invariant: profile lives in context, nowhere else. Prevents state sprawl.
 * When user logs out, clear profile. When user logs in, fetch fresh from GET /partner.
 */
export function PartnerProvider({ children }: PartnerProviderProps) {
  const [profile, setProfile] = useState<PartnerProfile | null>(null)

  const clearProfile = () => {
    setProfile(null)
  }

  return (
    <PartnerContext.Provider value={{ profile, setProfile, clearProfile }}>
      {children}
    </PartnerContext.Provider>
  )
}

/**
 * Hook: usePartner — access partner profile state and setter.
 * Throws if used outside PartnerProvider.
 */
export function usePartner() {
  const context = useContext(PartnerContext)
  if (!context) {
    throw new Error('usePartner must be used within PartnerProvider')
  }
  return context
}
