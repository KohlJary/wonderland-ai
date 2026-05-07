/**
 * Focus Session App — Main component.
 * Renders the session timer, break manager, settings, and history views.
 */

import { useEffect, useState } from 'react';
import {
  startSession,
  getCurrentSession,
  stopSession,
  getCurrentBreak,
  skipBreak,
  getSettings,
  updateSettings,
  getSessionHistory,
  getWeekStats,
  getAllTimeStats,
  getUser,
  type Session,
  type Break,
  type Settings,
  type SessionHistory,
  type WeekStats,
  type AllTimeStats,
  type User,
} from './api';

type View = 'session' | 'break' | 'history' | 'stats' | 'settings';

export function App() {
  const [view, setView] = useState<View>('session');
  const [session, setSession] = useState<Session | null>(null);
  const [breakInfo, setBreakInfo] = useState<Break | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [history, setHistory] = useState<SessionHistory[]>([]);
  const [weekStats, setWeekStats] = useState<WeekStats | null>(null);
  const [allTimeStats, setAllTimeStats] = useState<AllTimeStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Poll session and break state every second
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const sess = await getCurrentSession().catch(() => null);
        setSession(sess);

        if (sess?.state === 'completed') {
          const brk = await getCurrentBreak().catch(() => null);
          setBreakInfo(brk);
        }
      } catch (e) {
        // No active session
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Load settings and user on mount
  useEffect(() => {
    const load = async () => {
      try {
        const [s, u] = await Promise.all([getSettings(), getUser()]);
        setSettings(s);
        setUser(u);
      } catch (e) {
        setError(String(e));
      }
    };
    load();
  }, []);

  const handleStartSession = async () => {
    try {
      setLoading(true);
      const s = await startSession();
      setSession(s);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleStopSession = async () => {
    if (!session) return;
    try {
      setLoading(true);
      const s = await stopSession(session.id);
      setSession(s);
      setError(null);
      // Refresh break
      const brk = await getCurrentBreak().catch(() => null);
      setBreakInfo(brk);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleSkipBreak = async () => {
    if (!breakInfo) return;
    try {
      setLoading(true);
      await skipBreak();
      setBreakInfo(null);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSettings = async (updates: Partial<Settings>) => {
    try {
      setLoading(true);
      const updated = await updateSettings(updates);
      setSettings(updated);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleLoadHistory = async () => {
    try {
      setLoading(true);
      const h = await getSessionHistory();
      setHistory(h);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleLoadStats = async () => {
    try {
      setLoading(true);
      const [w, a] = await Promise.all([getWeekStats(), getAllTimeStats()]);
      setWeekStats(w);
      setAllTimeStats(a);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const formatSeconds = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    return `${mins} minutes`;
  };

  return (
    <main style={{ fontFamily: 'system-ui', maxWidth: 800, margin: '0 auto', padding: '2em' }}>
      <h1>Focus Session Tracker</h1>

      {/* Navigation */}
      <div style={{ marginBottom: '2em', display: 'flex', gap: '1em', flexWrap: 'wrap' }}>
        <button
          onClick={() => setView('session')}
          style={{ fontWeight: view === 'session' ? 'bold' : 'normal' }}
        >
          Session
        </button>
        <button
          onClick={() => { setView('history'); handleLoadHistory(); }}
          style={{ fontWeight: view === 'history' ? 'bold' : 'normal' }}
        >
          History
        </button>
        <button
          onClick={() => { setView('stats'); handleLoadStats(); }}
          style={{ fontWeight: view === 'stats' ? 'bold' : 'normal' }}
        >
          Stats
        </button>
        <button
          onClick={() => setView('settings')}
          style={{ fontWeight: view === 'settings' ? 'bold' : 'normal' }}
        >
          Settings
        </button>
      </div>

      {/* Error display */}
      {error && <p style={{ color: 'crimson' }}>{error}</p>}

      {/* Session view */}
      {view === 'session' && (
        <div>
          {!session ? (
            <div>
              <p>No active session</p>
              <button onClick={handleStartSession} disabled={loading}>
                {loading ? 'Starting...' : 'Start Session'}
              </button>
            </div>
          ) : (
            <div>
              <h2>Active Session</h2>
              <p>Duration: {session.duration_minutes} minutes</p>
              <p style={{ fontSize: '3em', fontWeight: 'bold' }}>
                {formatSeconds(session.remaining_seconds)}
              </p>
              <button onClick={handleStopSession} disabled={loading}>
                {loading ? 'Stopping...' : 'Stop Session'}
              </button>
            </div>
          )}

          {breakInfo && breakInfo.state === 'active' && (
            <div style={{ marginTop: '2em', padding: '1em', backgroundColor: '#f0f0f0' }}>
              <h3>Break Time</h3>
              <p>Duration: {breakInfo.duration_minutes} minutes</p>
              <p style={{ fontSize: '2em', fontWeight: 'bold' }}>
                {formatSeconds(breakInfo.remaining_seconds)}
              </p>
              <button onClick={handleSkipBreak} disabled={loading}>
                {loading ? 'Skipping...' : 'Skip Break'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* History view */}
      {view === 'history' && (
        <div>
          <h2>Session History</h2>
          {history.length === 0 ? (
            <p>No completed sessions</p>
          ) : (
            <div>
              <p>Total sessions: {history.length}</p>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {history.map((item) => (
                  <li
                    key={item.id}
                    style={{
                      padding: '1em',
                      marginBottom: '0.5em',
                      backgroundColor: '#f9f9f9',
                      border: '1px solid #ddd',
                    }}
                  >
                    <strong>Session {item.id}</strong>
                    <p>Duration: {formatDuration(item.duration_seconds)}</p>
                    <p>Break: {item.break_skipped ? 'Skipped' : `Took ${formatDuration(item.break_duration_seconds)}`}</p>
                    <p style={{ fontSize: '0.9em', color: '#666' }}>
                      Completed: {new Date(item.completed_at).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Stats view */}
      {view === 'stats' && (
        <div>
          <h2>Statistics</h2>
          {weekStats && (
            <div style={{ padding: '1em', backgroundColor: '#f9f9f9', marginBottom: '2em' }}>
              <h3>This Week</h3>
              <p>Sessions: {weekStats.session_count}</p>
              <p>Total Time: {formatDuration(weekStats.total_duration_seconds)}</p>
            </div>
          )}
          {allTimeStats && (
            <div style={{ padding: '1em', backgroundColor: '#f9f9f9' }}>
              <h3>All-Time</h3>
              <p>Sessions: {allTimeStats.session_count}</p>
              <p>Total Time: {formatDuration(allTimeStats.total_duration_seconds)}</p>
              <p>Days Tracked: {allTimeStats.membership_duration_days}</p>
            </div>
          )}
          {user?.launch_date && (
            <p style={{ fontSize: '0.9em', color: '#666', marginTop: '1em' }}>
              Tracking since: {new Date(user.launch_date).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      {/* Settings view */}
      {view === 'settings' && settings && (
        <div>
          <h2>Settings</h2>
          <div style={{ marginBottom: '1em' }}>
            <label>
              Session Duration (minutes):
              <input
                type="number"
                min="1"
                max="180"
                value={settings.session_duration_minutes}
                onChange={(e) =>
                  handleUpdateSettings({
                    session_duration_minutes: parseInt(e.target.value) || 25,
                  })
                }
                disabled={loading}
              />
            </label>
          </div>
          <div>
            <label>
              Break Duration (minutes):
              <input
                type="number"
                min="1"
                max="180"
                value={settings.break_duration_minutes}
                onChange={(e) =>
                  handleUpdateSettings({
                    break_duration_minutes: parseInt(e.target.value) || 5,
                  })
                }
                disabled={loading}
              />
            </label>
          </div>
        </div>
      )}
    </main>
  );
}
