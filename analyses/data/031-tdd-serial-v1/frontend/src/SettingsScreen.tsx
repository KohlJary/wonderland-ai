/**
 * SettingsScreen — UI for persistent settings.
 * 
 * Lets user modify focus/break durations, audio volume, audio enable/disable,
 * and theme preference. Changes are persisted to localStorage immediately
 * upon save. UI shows error states when persistence fails.
 */

import { useEffect, useState } from 'react';
import { getSettingsManager, type Settings } from './settings';

export function SettingsScreen() {
  const manager = getSettingsManager();
  
  // Local form state (before save)
  const [formState, setFormState] = useState<Settings>(manager.current());
  
  // Error state (e.g., save failed)
  const [error, setError] = useState<string | null>(null);
  
  // Success feedback (e.g., saved successfully)
  const [saving, setSaving] = useState(false);

  // Subscribe to external settings changes (e.g., from another tab/window)
  useEffect(() => {
    const unsubscribe = manager.onChange((settings) => {
      setFormState(settings);
      setError(null);
    });

    // Load current settings on mount
    setFormState(manager.current());

    return unsubscribe;
  }, [manager]);

  const handleFocusDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const minutes = parseInt(e.target.value, 10);
    if (!isNaN(minutes) && minutes > 0) {
      setFormState(prev => ({
        ...prev,
        focus_duration_ms: minutes * 60 * 1000, // Convert minutes to milliseconds
      }));
      setError(null);
    }
  };

  const handleBreakDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const minutes = parseInt(e.target.value, 10);
    if (!isNaN(minutes) && minutes > 0) {
      setFormState(prev => ({
        ...prev,
        break_duration_ms: minutes * 60 * 1000,
      }));
      setError(null);
    }
  };

  const handleAudioEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormState(prev => ({
      ...prev,
      audio_enabled: e.target.checked,
    }));
    setError(null);
  };

  const handleAudioVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const volume = parseInt(e.target.value, 10);
    if (!isNaN(volume) && volume >= 0 && volume <= 100) {
      setFormState(prev => ({
        ...prev,
        audio_volume: volume,
      }));
      setError(null);
    }
  };

  const handleThemeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const theme = e.target.value as 'light' | 'dark';
    setFormState(prev => ({
      ...prev,
      theme,
    }));
    setError(null);
  };

  const handleSave = async () => {
    setSaving(true);
    const success = manager.save(formState);
    setSaving(false);

    if (!success) {
      setError('Could not save settings. Please try again.');
    }
  };

  const handleCancel = () => {
    // Reset form to current saved state
    setFormState(manager.current());
    setError(null);
  };

  // Convert milliseconds back to minutes for display
  const focusMinutes = formState.focus_duration_ms / (60 * 1000);
  const breakMinutes = formState.break_duration_ms / (60 * 1000);

  // Check if form has unsaved changes
  const current = manager.current();
  const hasChanges =
    JSON.stringify(formState) !== JSON.stringify(current);

  return (
    <div style={{ maxWidth: 500, margin: '2em auto', fontFamily: 'system-ui' }}>
      <h2>Settings</h2>

      {error && (
        <div style={{
          backgroundColor: '#fee',
          color: '#c33',
          padding: '1em',
          borderRadius: 4,
          marginBottom: '1em',
          border: '1px solid #fcc',
        }}>
          {error}
        </div>
      )}

      <form style={{ display: 'flex', flexDirection: 'column', gap: '1.5em' }}>
        {/* Focus Duration */}
        <fieldset style={{ border: 'none', padding: 0 }}>
          <label style={{ display: 'block', marginBottom: '0.5em', fontWeight: 'bold' }}>
            Focus Duration (minutes)
          </label>
          <input
            type="number"
            min="1"
            max="120"
            value={focusMinutes}
            onChange={handleFocusDurationChange}
            style={{
              width: '100%',
              padding: '0.5em',
              fontSize: '1em',
              boxSizing: 'border-box',
            }}
          />
          <small style={{ color: '#666', display: 'block', marginTop: '0.25em' }}>
            Current: {focusMinutes} minutes
          </small>
        </fieldset>

        {/* Break Duration */}
        <fieldset style={{ border: 'none', padding: 0 }}>
          <label style={{ display: 'block', marginBottom: '0.5em', fontWeight: 'bold' }}>
            Break Duration (minutes)
          </label>
          <input
            type="number"
            min="1"
            max="60"
            value={breakMinutes}
            onChange={handleBreakDurationChange}
            style={{
              width: '100%',
              padding: '0.5em',
              fontSize: '1em',
              boxSizing: 'border-box',
            }}
          />
          <small style={{ color: '#666', display: 'block', marginTop: '0.25em' }}>
            Current: {breakMinutes} minutes
          </small>
        </fieldset>

        {/* Audio Enable/Disable */}
        <fieldset style={{ border: 'none', padding: 0 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5em' }}>
            <input
              type="checkbox"
              checked={formState.audio_enabled}
              onChange={handleAudioEnabledChange}
              style={{ width: '1.2em', height: '1.2em' }}
            />
            <span style={{ fontWeight: 'bold' }}>Enable Audio</span>
          </label>
        </fieldset>

        {/* Audio Volume */}
        <fieldset style={{ border: 'none', padding: 0 }}>
          <label style={{ display: 'block', marginBottom: '0.5em', fontWeight: 'bold' }}>
            Audio Volume: {formState.audio_volume}%
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={formState.audio_volume}
            onChange={handleAudioVolumeChange}
            disabled={!formState.audio_enabled}
            style={{
              width: '100%',
              cursor: formState.audio_enabled ? 'pointer' : 'not-allowed',
            }}
          />
          <small style={{ color: '#666', display: 'block', marginTop: '0.25em' }}>
            {formState.audio_enabled ? 'Mute to disable audio above' : 'Enable audio to adjust volume'}
          </small>
        </fieldset>

        {/* Theme Selection */}
        <fieldset style={{ border: 'none', padding: 0 }}>
          <label style={{ display: 'block', marginBottom: '0.5em', fontWeight: 'bold' }}>
            Theme
          </label>
          <select
            value={formState.theme}
            onChange={handleThemeChange}
            style={{
              width: '100%',
              padding: '0.5em',
              fontSize: '1em',
              boxSizing: 'border-box',
            }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </fieldset>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '1em', marginTop: '1em' }}>
          <button
            type="button"
            onClick={handleSave}
            disabled={!hasChanges || saving}
            style={{
              flex: 1,
              padding: '0.75em',
              fontSize: '1em',
              backgroundColor: hasChanges ? '#0066cc' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: hasChanges && !saving ? 'pointer' : 'not-allowed',
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={handleCancel}
            disabled={!hasChanges || saving}
            style={{
              flex: 1,
              padding: '0.75em',
              fontSize: '1em',
              backgroundColor: '#999',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: hasChanges && !saving ? 'pointer' : 'not-allowed',
              opacity: saving ? 0.7 : 1,
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
