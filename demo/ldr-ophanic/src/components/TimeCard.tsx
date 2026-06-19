import { useEffect, useState } from 'react'
import { PartnerProfile } from '../contexts/PartnerContext'

/**
 * TimeCard component.
 * 
 * Accepts partner profile with timezone (IANA string, e.g., 'Europe/Vienna').
 * Renders partner's current local time in their timezone.
 * Uses browser's Intl.DateTimeFormat to compute local time client-side.
 * Updates every second using setInterval; clears on component unmount.
 * 
 * Contract assumptions:
 * - profile.iana_timezone is a valid IANA timezone string (e.g., 'Europe/Vienna')
 * - profile.name is the partner's display name
 * 
 * UI states:
 * - loading: profile is null or undefined
 * - display: profile loaded, time is rendered and ticking
 * 
 * Client state:
 * - currentTime: the displayed time, re-computed every second
 * - setInterval hook manages the tick timer; cleared on unmount
 */
export interface TimeCardProps {
  profile: PartnerProfile | null | undefined
}

export default function TimeCard({ profile }: TimeCardProps) {
  const [currentTime, setCurrentTime] = useState<string>('')

  useEffect(() => {
    // If no profile, don't render a time
    if (!profile) {
      setCurrentTime('')
      return
    }

    /**
     * Compute and update the time display every second.
     * Uses Intl.DateTimeFormat with the partner's IANA timezone.
     */
    const updateTime = () => {
      try {
        const now = new Date()
        const formatter = new Intl.DateTimeFormat('en-US', {
          timeZone: profile.iana_timezone,
          hour: 'numeric',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        })
        const timeString = formatter.format(now)
        setCurrentTime(timeString)
      } catch (error) {
        // If timezone is invalid, show error state
        console.error(`Invalid timezone: ${profile.iana_timezone}`, error)
        setCurrentTime('Invalid timezone')
      }
    }

    // Compute initial time immediately
    updateTime()

    // Set up interval to tick every second
    const intervalId = setInterval(updateTime, 1000)

    // Clean up interval on unmount
    return () => clearInterval(intervalId)
  }, [profile])

  if (!profile) {
    return (
      <div className="card time-card">
        <h2>Time</h2>
        <p>Loading partner's timezone...</p>
      </div>
    )
  }

  return (
    <div className="card time-card">
      <h2>Time</h2>
      <div className="time-card-content">
        <p className="partner-name">{profile.name} is at</p>
        <p className="time-display">{currentTime}</p>
        <p className="timezone-label">{profile.iana_timezone}</p>
      </div>
    </div>
  )
}
