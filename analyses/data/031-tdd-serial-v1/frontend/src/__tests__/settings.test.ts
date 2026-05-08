/**
 * Unit tests for SettingsManager — localStorage-backed settings with validation.
 * These tests run in Vitest (frontend test runner) and exercise the core
 * settings persistence logic.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  SettingsManager,
  DEFAULT_SETTINGS,
  resetSettingsManagerForTesting,
} from '../settings';

describe('SettingsManager', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    resetSettingsManagerForTesting();
  });

  afterEach(() => {
    localStorage.clear();
    resetSettingsManagerForTesting();
  });

  describe('initialization and defaults', () => {
    it('should load defaults when localStorage is empty', () => {
      const manager = new SettingsManager();
      const settings = manager.current();

      expect(settings.focus_duration_ms).toBe(1500000); // 25 minutes
      expect(settings.break_duration_ms).toBe(300000);  // 5 minutes
      expect(settings.audio_enabled).toBe(true);
      expect(settings.audio_volume).toBe(50);
      expect(settings.theme).toBe('light');
    });

    it('should restore previously saved settings', () => {
      // Save custom settings
      const manager1 = new SettingsManager();
      manager1.save({
        focus_duration_ms: 1380000,
        break_duration_ms: 420000,
        theme: 'dark',
      });

      // New manager instance should restore those settings
      resetSettingsManagerForTesting();
      const manager2 = new SettingsManager();
      const settings = manager2.current();

      expect(settings.focus_duration_ms).toBe(1380000);
      expect(settings.break_duration_ms).toBe(420000);
      expect(settings.theme).toBe('dark');
      expect(settings.audio_enabled).toBe(true); // Not changed, should be default
    });
  });

  describe('saving and persistence', () => {
    it('should write settings to localStorage', () => {
      const manager = new SettingsManager();
      const success = manager.save({
        focus_duration_ms: 1800000,
      });

      expect(success).toBe(true);
      const stored = localStorage.getItem('app_settings');
      expect(stored).toBeDefined();
      const parsed = JSON.parse(stored!);
      expect(parsed.focus_duration_ms).toBe(1800000);
    });

    it('should support partial updates (merge, not replace)', () => {
      const manager = new SettingsManager();
      manager.save({ focus_duration_ms: 1200000 });
      manager.save({ audio_volume: 75 }); // Partial update

      const settings = manager.current();
      expect(settings.focus_duration_ms).toBe(1200000); // Retained from first save
      expect(settings.audio_volume).toBe(75); // Updated in second save
      expect(settings.break_duration_ms).toBe(300000); // Default, unchanged
    });

    it('should validate and normalize invalid durations', () => {
      const manager = new SettingsManager();
      
      // Try to save invalid durations
      manager.save({
        focus_duration_ms: -1000, // Invalid: negative
        break_duration_ms: 0,      // Invalid: zero
      });

      const settings = manager.current();
      // Should fall back to defaults
      expect(settings.focus_duration_ms).toBe(DEFAULT_SETTINGS.focus_duration_ms);
      expect(settings.break_duration_ms).toBe(DEFAULT_SETTINGS.break_duration_ms);
    });

    it('should clamp audio volume to 0-100', () => {
      const manager = new SettingsManager();
      
      manager.save({ audio_volume: 150 });
      expect(manager.current().audio_volume).toBe(100);

      manager.save({ audio_volume: -50 });
      expect(manager.current().audio_volume).toBe(0);

      manager.save({ audio_volume: 75 });
      expect(manager.current().audio_volume).toBe(75);
    });

    it('should reject invalid theme values', () => {
      const manager = new SettingsManager();
      
      manager.save({ theme: 'invalid-theme' as any });
      expect(manager.current().theme).toBe(DEFAULT_SETTINGS.theme);

      manager.save({ theme: 'dark' });
      expect(manager.current().theme).toBe('dark');
    });

    it('should preserve audio_enabled and audio_volume independently', () => {
      const manager = new SettingsManager();
      
      manager.save({ audio_enabled: true, audio_volume: 60 });
      manager.save({ audio_enabled: false }); // Disable audio
      
      let settings = manager.current();
      expect(settings.audio_enabled).toBe(false);
      expect(settings.audio_volume).toBe(60); // Volume should be preserved
      
      manager.save({ audio_enabled: true }); // Re-enable audio
      settings = manager.current();
      expect(settings.audio_volume).toBe(60); // Volume should still be 60
    });
  });

  describe('error handling', () => {
    it('should handle corrupted JSON in localStorage', () => {
      localStorage.setItem('app_settings', '{invalid json}');
      
      const manager = new SettingsManager();
      const settings = manager.current();
      
      // Should fall back to defaults
      expect(settings).toEqual(DEFAULT_SETTINGS);
    });

    it('should handle storage quota exceeded gracefully', () => {
      const manager = new SettingsManager();
      manager.save({ focus_duration_ms: 1500000 });

      // Mock localStorage.setItem to throw quota exceeded error
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = vi.fn(() => {
        throw new Error('QuotaExceededError');
      });

      const success = manager.save({ audio_volume: 75 });
      expect(success).toBe(false);

      // Settings should revert to last valid state
      Storage.prototype.setItem = originalSetItem;
      const reloadedManager = new SettingsManager();
      const settings = reloadedManager.current();
      expect(settings.focus_duration_ms).toBe(1500000); // Last valid save
    });

    it('should handle storage disabled/permission denied', () => {
      // Mock localStorage to be unavailable
      const originalGetItem = Storage.prototype.getItem;
      Storage.prototype.getItem = vi.fn(() => {
        throw new Error('localStorage is not available');
      });

      const manager = new SettingsManager();
      const settings = manager.current();
      
      expect(settings).toEqual(DEFAULT_SETTINGS);

      Storage.prototype.getItem = originalGetItem;
    });
  });

  describe('listeners and notifications', () => {
    it('should notify listeners when settings change', () => {
      const manager = new SettingsManager();
      const listener = vi.fn();

      manager.onChange(listener);
      manager.save({ audio_volume: 75 });

      expect(listener).toHaveBeenCalledTimes(1);
      const notifiedSettings = listener.mock.calls[0][0];
      expect(notifiedSettings.audio_volume).toBe(75);
    });

    it('should allow unsubscribing from changes', () => {
      const manager = new SettingsManager();
      const listener = vi.fn();

      const unsubscribe = manager.onChange(listener);
      manager.save({ audio_volume: 75 });
      expect(listener).toHaveBeenCalledTimes(1);

      unsubscribe();
      manager.save({ audio_volume: 80 });
      expect(listener).toHaveBeenCalledTimes(1); // Not called again
    });

    it('should handle listener errors gracefully', () => {
      const manager = new SettingsManager();
      const errorListener = vi.fn(() => {
        throw new Error('Listener error');
      });
      const okListener = vi.fn();

      manager.onChange(errorListener);
      manager.onChange(okListener);
      
      manager.save({ audio_volume: 75 });

      expect(errorListener).toHaveBeenCalledTimes(1);
      expect(okListener).toHaveBeenCalledTimes(1); // Should still be called
    });
  });

  describe('reset', () => {
    it('should clear storage and return to defaults', () => {
      const manager = new SettingsManager();
      manager.save({ focus_duration_ms: 1200000, theme: 'dark' });
      
      manager.reset();
      
      const settings = manager.current();
      expect(settings).toEqual(DEFAULT_SETTINGS);
      expect(localStorage.getItem('app_settings')).toBeNull();
    });
  });

  describe('forward compatibility', () => {
    it('should ignore unknown fields when loading', () => {
      const stored = JSON.stringify({
        focus_duration_ms: 1500000,
        break_duration_ms: 300000,
        audio_enabled: true,
        audio_volume: 50,
        theme: 'light',
        future_field: 'should be ignored',
      });
      localStorage.setItem('app_settings', stored);

      const manager = new SettingsManager();
      const settings = manager.current();
      
      expect(settings.focus_duration_ms).toBe(1500000);
      expect('future_field' in settings).toBe(false);
    });
  });

  describe('type safety', () => {
    it('should normalize non-boolean audio_enabled', () => {
      const manager = new SettingsManager();
      
      manager.save({ audio_enabled: 'yes' as any });
      expect(manager.current().audio_enabled).toBe(DEFAULT_SETTINGS.audio_enabled);

      manager.save({ audio_enabled: 1 as any });
      expect(manager.current().audio_enabled).toBe(DEFAULT_SETTINGS.audio_enabled);
    });

    it('should reject fractional durations', () => {
      const manager = new SettingsManager();
      
      manager.save({ focus_duration_ms: 1500.5 });
      expect(manager.current().focus_duration_ms).toBe(DEFAULT_SETTINGS.focus_duration_ms);
    });
  });
});
