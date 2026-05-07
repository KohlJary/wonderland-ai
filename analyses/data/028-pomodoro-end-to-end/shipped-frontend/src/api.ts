/**
 * Backend API wrapper for Focus Session app.
 * Centralizes HTTP details so components don't repeat fetch+JSON+error handling.
 */

// Session types
export interface Session {
  id: number;
  state: string;
  duration_minutes: number;
  start_time: string;
  completed_at: string | null;
  remaining_seconds: number;
}

// Break types
export interface Break {
  id: number;
  state: string;
  duration_minutes: number;
  start_time: string;
  completed_at: string | null;
  remaining_seconds: number;
  skip_available: boolean;
}

// Settings types
export interface Settings {
  session_duration_minutes: number;
  break_duration_minutes: number;
}

// History types
export interface SessionHistory {
  id: number;
  start_time: string;
  completed_at: string;
  duration_seconds: number;
  break_duration_seconds: number;
  break_skipped: boolean;
}

// Stats types
export interface WeekStats {
  session_count: number;
  total_duration_seconds: number;
  week_start_date: string;
  week_end_date: string;
}

export interface AllTimeStats {
  session_count: number;
  total_duration_seconds: number;
  membership_duration_days: number;
}

// User types
export interface User {
  id: number;
  launch_date: string | null;
  days_tracked: number;
}

// Session endpoints
export async function startSession(): Promise<Session> {
  const res = await fetch('/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    throw new Error(`startSession failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getCurrentSession(): Promise<Session> {
  const res = await fetch('/session/current');
  if (!res.ok) {
    throw new Error(`getCurrentSession failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function stopSession(sessionId: number): Promise<Session> {
  const res = await fetch(`/session/${sessionId}/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    throw new Error(`stopSession failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Break endpoints
export async function getCurrentBreak(): Promise<Break> {
  const res = await fetch('/break/current');
  if (!res.ok) {
    throw new Error(`getCurrentBreak failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function skipBreak(): Promise<Break> {
  const res = await fetch('/break/skip', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) {
    throw new Error(`skipBreak failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Settings endpoints
export async function getSettings(): Promise<Settings> {
  const res = await fetch('/settings');
  if (!res.ok) {
    throw new Error(`getSettings failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
  const res = await fetch('/settings', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) {
    throw new Error(`updateSettings failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// History endpoint
export async function getSessionHistory(sinceTimestamp?: number): Promise<SessionHistory[]> {
  let url = '/sessions/history';
  if (sinceTimestamp !== undefined) {
    url += `?since_timestamp=${sinceTimestamp}`;
  }
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`getSessionHistory failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Stats endpoints
export async function getWeekStats(): Promise<WeekStats> {
  const res = await fetch('/stats/week');
  if (!res.ok) {
    throw new Error(`getWeekStats failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getAllTimeStats(): Promise<AllTimeStats> {
  const res = await fetch('/stats/all-time');
  if (!res.ok) {
    throw new Error(`getAllTimeStats failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// User endpoint
export async function getUser(): Promise<User> {
  const res = await fetch('/user');
  if (!res.ok) {
    throw new Error(`getUser failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Health check
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch('/health');
  if (!res.ok) {
    throw new Error(`checkHealth failed: ${res.status}`);
  }
  return res.json();
}
