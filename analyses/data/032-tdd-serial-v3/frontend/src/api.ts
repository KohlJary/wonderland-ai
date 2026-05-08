/**
 * Backend API wrapper. Centralizes the HTTP details so feature
 * components don't repeat fetch+JSON+error handling. Vite's dev
 * server proxies /api → http://localhost:8000 (see vite.config.ts).
 */

export interface SessionLogRequest {
  type: 'focus' | 'break';
  duration_configured_seconds: number;
  duration_actual_seconds: number;
  completed_at: string;
}

export interface SessionLogResponse {
  session_id: string;
  acknowledged: boolean;
}

export interface SessionRecord {
  session_id: string;
  user_id: string;
  type: 'focus' | 'break';
  duration_configured_seconds: number;
  duration_actual_seconds: number;
  completed_at: string;
  created_at: string;
}

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch('/health');
  if (!res.ok) {
    throw new Error(`checkHealth failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Log a completed session to the backend.
 * Implements retry logic with exponential backoff (max 3 attempts).
 */
export async function logSession(
  payload: SessionLogRequest,
  maxRetries: number = 3
): Promise<SessionLogResponse> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await fetch('/api/sessions/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        throw new Error(`logSession failed: ${res.status} ${res.statusText}`);
      }
      
      return res.json();
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      
      if (attempt < maxRetries - 1) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError || new Error('logSession failed after retries');
}

/**
 * Retrieve all sessions for a given date.
 */
export async function getSessionsForDate(date: string): Promise<SessionRecord[]> {
  const res = await fetch(`/api/sessions?date=${encodeURIComponent(date)}`);
  if (!res.ok) {
    throw new Error(`getSessionsForDate failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
