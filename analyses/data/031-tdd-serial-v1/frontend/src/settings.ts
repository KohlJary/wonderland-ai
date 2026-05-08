/**
 * SettingsManager — localStorage-backed settings with validation and defaults.
 * 
 * Client-side only (v1): no backend persistence, no server-side state.
 * Each device/browser has independent settings.
 * 
 * Contract: Settings object shape is stable per .wonderland/contract-notes.
 * Any schema changes must increment the storage key version.
 */

export interface Settings {
  focus_duration_ms: number;
  break_duration_ms: number;
  audio_enabled: boolean;
  audio_volume: number; // 0-100
  theme: 'light' | 'dark';
}

export const DEFAULT_SETTINGS: Settings = {
  focus_duration_ms: 1500000, // 25 minutes in milliseconds
  break_duration_ms: 300000,  // 5 minutes in milliseconds
  audio_enabled: true,
  audio_volume: 50,
  theme: 'light',
};

const STORAGE_KEY = 'app_settings';

type SettingsChangeListener = (settings: Settings) => void;

export class SettingsManager {
  private settings: Settings;
  private listeners: Set<SettingsChangeListener> = new Set();

  constructor() {
    this.settings = this.loadFromStorage();
  }

  /**
   * Load settings from localStorage.
   * Falls back to defaults if storage is unavailable, corrupted, or empty.
   */
  private loadFromStorage(): Settings {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      
      if (!stored) {
        return { ...DEFAULT_SETTINGS };
      }

      const parsed = JSON.parse(stored);
      return this.validateSettings(parsed);
    } catch (e) {
      // Storage unavailable (private browsing, disabled), corrupted JSON, or other error
      console.error('Failed to load settings from localStorage:', e);
      return { ...DEFAULT_SETTINGS };
    }
  }

  /**
   * Validate loaded settings, normalizing invalid values and handling
   * new fields added in future versions (forward compatibility).
   */
  private validateSettings(loaded: unknown): Settings {
    if (typeof loaded !== 'object' || loaded === null) {
      return { ...DEFAULT_SETTINGS };
    }

    const obj = loaded as Record<string, unknown>;

    // Validate focus_duration_ms
    const focus_duration_ms = this.validateDuration(
      obj.focus_duration_ms,
      DEFAULT_SETTINGS.focus_duration_ms
    );

    // Validate break_duration_ms
    const break_duration_ms = this.validateDuration(
      obj.break_duration_ms,
      DEFAULT_SETTINGS.break_duration_ms
    );

    // Validate audio_enabled (normalize non-boolean)
    const audio_enabled = typeof obj.audio_enabled === 'boolean'
      ? obj.audio_enabled
      : DEFAULT_SETTINGS.audio_enabled;

    // Validate audio_volume (clamp to 0-100)
    const audio_volume = this.validateVolume(
      obj.audio_volume,
      DEFAULT_SETTINGS.audio_volume
    );

    // Validate theme (reject invalid values)
    const theme = obj.theme === 'light' || obj.theme === 'dark'
      ? obj.theme
      : DEFAULT_SETTINGS.theme;

    return {
      focus_duration_ms,
      break_duration_ms,
      audio_enabled,
      audio_volume,
      theme,
    };
  }

  /**
   * Validate duration: must be positive integer (milliseconds).
   * Returns the value if valid, default if not.
   */
  private validateDuration(value: unknown, defaultMs: number): number {
    if (typeof value === 'number') {
      if (Number.isInteger(value) && value > 0) {
        return value;
      }
    }
    return defaultMs;
  }

  /**
   * Validate volume: must be integer in range [0, 100].
   * Clamps out-of-range values rather than rejecting them.
   */
  private validateVolume(value: unknown, defaultVol: number): number {
    if (typeof value === 'number') {
      if (Number.isInteger(value)) {
        return Math.max(0, Math.min(100, value));
      }
    }
    return defaultVol;
  }

  /**
   * Get current settings (in-memory copy).
   */
  current(): Settings {
    return { ...this.settings };
  }

  /**
   * Save settings to localStorage and notify listeners.
   * Merges provided partial settings with current settings (partial update).
   * 
   * @throws Error if localStorage is unavailable.
   * @returns true if save succeeded, false if failed.
   */
  save(partial: Partial<Settings>): boolean {
    try {
      // Merge with current settings (partial update, not full replace)
      const updated = { ...this.settings, ...partial };
      
      // Validate the merged result
      const validated = this.validateSettings(updated);
      
      // Write to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(validated));
      
      // Update in-memory state
      this.settings = validated;
      
      // Notify all listeners
      this.notifyListeners();
      
      return true;
    } catch (e) {
      console.error('Failed to save settings to localStorage:', e);
      return false;
    }
  }

  /**
   * Clear all settings and return to defaults.
   * Used for testing or explicit user reset.
   */
  reset(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
      this.settings = { ...DEFAULT_SETTINGS };
      this.notifyListeners();
    } catch (e) {
      console.error('Failed to reset settings:', e);
    }
  }

  /**
   * Subscribe to settings changes.
   * Listener is called whenever save() completes successfully.
   */
  onChange(listener: SettingsChangeListener): () => void {
    this.listeners.add(listener);
    // Return unsubscribe function
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Notify all subscribers of settings changes.
   */
  private notifyListeners(): void {
    const settings = { ...this.settings };
    this.listeners.forEach(listener => {
      try {
        listener(settings);
      } catch (e) {
        console.error('Error in settings listener:', e);
      }
    });
  }
}

// Global singleton instance (one per app lifecycle)
let globalSettingsManager: SettingsManager | null = null;

export function getSettingsManager(): SettingsManager {
  if (!globalSettingsManager) {
    globalSettingsManager = new SettingsManager();
  }
  return globalSettingsManager;
}

export function resetSettingsManagerForTesting(): void {
  globalSettingsManager = null;
}
