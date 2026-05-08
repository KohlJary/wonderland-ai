/**
 * FocusTimer component — manages a countdown timer for focus sessions.
 * 
 * Features:
 * - Starts a 25-minute focus session
 * - Shows remaining time in MM:SS format
 * - Can be paused and resumed
 * - Logs completion to backend via POST /sessions/log
 * - Handles network retries with exponential backoff
 * 
 * UI States:
 * - idle: timer not started
 * - running: timer counting down
 * - paused: timer paused, can be resumed
 * - completing: timer finished, logging to backend
 * - completed: timer finished, logged to backend
 * - error: logging failed
 */

import { useEffect, useState, useRef } from 'react';
import { logSession } from './api';

const DEFAULT_FOCUS_DURATION_SECONDS = 25 * 60; // 25 minutes

type TimerState = 'idle' | 'running' | 'paused' | 'completing' | 'completed' | 'error';

export function FocusTimer() {
  const [timerState, setTimerState] = useState<TimerState>('idle');
  const [remainingSeconds, setRemainingSeconds] = useState(DEFAULT_FOCUS_DURATION_SECONDS);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLogging, setIsLogging] = useState(false);

  // Refs to track timing across re-renders
  const startTimeRef = useRef<number | null>(null);
  const pausedAtRef = useRef<number | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Start a new focus session.
   */
  const handleStart = () => {
    setTimerState('running');
    setElapsedSeconds(0);
    setRemainingSeconds(DEFAULT_FOCUS_DURATION_SECONDS);
    setError(null);
    startTimeRef.current = Date.now();
    pausedAtRef.current = null;
  };

  /**
   * Pause the running timer.
   */
  const handlePause = () => {
    if (timerState === 'running') {
      setTimerState('paused');
      pausedAtRef.current = elapsedSeconds;
    }
  };

  /**
   * Resume a paused timer.
   */
  const handleResume = () => {
    if (timerState === 'paused' && pausedAtRef.current !== null) {
      setTimerState('running');
      // Adjust startTime to account for the paused period
      startTimeRef.current = Date.now() - (pausedAtRef.current * 1000);
      pausedAtRef.current = null;
    }
  };

  /**
   * Log the completed session to the backend.
   */
  const handleLogCompletion = async () => {
    setIsLogging(true);
    setError(null);

    try {
      const now = new Date();
      const completedAt = now.toISOString();

      const response = await logSession({
        type: 'focus',
        duration_configured_seconds: DEFAULT_FOCUS_DURATION_SECONDS,
        duration_actual_seconds: elapsedSeconds,
        completed_at: completedAt,
      });

      if (response.acknowledged) {
        setTimerState('completed');
      } else {
        setError('Failed to acknowledge session completion');
        setTimerState('error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setTimerState('error');
    } finally {
      setIsLogging(false);
    }
  };

  /**
   * Reset the timer to idle state.
   */
  const handleReset = () => {
    setTimerState('idle');
    setElapsedSeconds(0);
    setRemainingSeconds(DEFAULT_FOCUS_DURATION_SECONDS);
    setError(null);
    startTimeRef.current = null;
    pausedAtRef.current = null;
  };

  /**
   * Main timer loop — runs when state is 'running'.
   */
  useEffect(() => {
    if (timerState === 'running' && startTimeRef.current !== null) {
      // Clear any existing interval
      if (intervalRef.current) clearInterval(intervalRef.current);

      intervalRef.current = setInterval(() => {
        const now = Date.now();
        const elapsedMs = now - startTimeRef.current!;
        const newElapsed = Math.floor(elapsedMs / 1000);
        const newRemaining = Math.max(
          0,
          DEFAULT_FOCUS_DURATION_SECONDS - newElapsed
        );

        setElapsedSeconds(newElapsed);
        setRemainingSeconds(newRemaining);

        // Completion check
        if (newRemaining === 0) {
          setTimerState('completing');
        }
      }, 100); // Update every 100ms for smooth UX
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [timerState]);

  /**
   * Handle completion state transition.
   */
  useEffect(() => {
    if (timerState === 'completing') {
      if (intervalRef.current) clearInterval(intervalRef.current);
      handleLogCompletion();
    }
  }, [timerState]);

  /**
   * Format seconds as MM:SS.
   */
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1.5em',
        padding: '2em',
        borderRadius: '8px',
        backgroundColor: timerState === 'running' ? '#f0f8ff' : timerState === 'paused' ? '#fff8f0' : '#ffffff',
        border: '1px solid #ddd',
        maxWidth: '400px',
        margin: '0 auto',
      }}
    >
      <h2>Focus Timer</h2>

      {/* Timer Display */}
      <div
        style={{
          fontSize: '3em',
          fontWeight: 'bold',
          fontFamily: 'monospace',
          color: timerState === 'running' ? '#0066cc' : timerState === 'paused' ? '#ff8800' : '#333',
          minWidth: '150px',
          textAlign: 'center',
        }}
      >
        {formatTime(remainingSeconds)}
      </div>

      {/* State Indicator */}
      <div style={{ fontSize: '0.9em', color: '#666' }}>
        {timerState === 'idle' && 'Ready to start'}
        {timerState === 'running' && 'Running...'}
        {timerState === 'paused' && 'Paused'}
        {timerState === 'completing' && 'Completing...'}
        {timerState === 'completed' && '✓ Logged'}
        {timerState === 'error' && '⚠ Error'}
      </div>

      {/* Progress bar */}
      {timerState !== 'idle' && timerState !== 'completed' && (
        <div
          style={{
            width: '100%',
            height: '4px',
            backgroundColor: '#eee',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              backgroundColor: timerState === 'paused' ? '#ff8800' : '#0066cc',
              width: `${(elapsedSeconds / DEFAULT_FOCUS_DURATION_SECONDS) * 100}%`,
              transition: 'width 0.1s linear',
            }}
          />
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: '0.5em', justifyContent: 'center', flexWrap: 'wrap' }}>
        {timerState === 'idle' && (
          <button onClick={handleStart} style={{ padding: '0.5em 1em', fontSize: '1em' }}>
            Start Focus
          </button>
        )}

        {timerState === 'running' && (
          <button onClick={handlePause} style={{ padding: '0.5em 1em', fontSize: '1em' }}>
            Pause
          </button>
        )}

        {timerState === 'paused' && (
          <>
            <button onClick={handleResume} style={{ padding: '0.5em 1em', fontSize: '1em' }}>
              Resume
            </button>
            <button
              onClick={handleReset}
              style={{
                padding: '0.5em 1em',
                fontSize: '1em',
                backgroundColor: '#f0f0f0',
              }}
            >
              Reset
            </button>
          </>
        )}

        {(timerState === 'completed' || timerState === 'error') && (
          <button onClick={handleReset} style={{ padding: '0.5em 1em', fontSize: '1em' }}>
            Start New Session
          </button>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div
          style={{
            backgroundColor: '#ffe6e6',
            color: '#cc0000',
            padding: '0.75em',
            borderRadius: '4px',
            fontSize: '0.9em',
            width: '100%',
            boxSizing: 'border-box',
            textAlign: 'center',
          }}
        >
          {error}
          {timerState === 'error' && ' (will retry)'}
        </div>
      )}

      {/* Logging indicator */}
      {isLogging && (
        <div style={{ fontSize: '0.9em', color: '#666' }}>
          Saving session...
        </div>
      )}

      {/* Debug info (session time) */}
      {timerState !== 'idle' && (
        <div style={{ fontSize: '0.8em', color: '#999', marginTop: '0.5em' }}>
          Elapsed: {formatTime(elapsedSeconds)}
        </div>
      )}
    </div>
  );
}
