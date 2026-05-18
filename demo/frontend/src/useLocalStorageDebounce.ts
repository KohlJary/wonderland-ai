import { useEffect, useRef } from 'react';

/**
 * useLocalStorageDebounce — manages debounced localStorage writes
 *
 * Usage:
 *   const debouncedWrite = useLocalStorageDebounce('key', 300);
 *   debouncedWrite({ title: 'foo', body: 'bar' });
 *
 * The hook debounces writes so that fast keystrokes don't thrash the storage.
 * Each call resets the debounce timer; the write happens 300ms after the last call.
 *
 * @param key localStorage key to write to
 * @param delayMs debounce delay in milliseconds (default 300)
 * @returns function that accepts any serializable value
 */
export function useLocalStorageDebounce<T>(key: string, delayMs: number = 300) {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return (value: T) => {
    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (err) {
        console.error(`Failed to write to localStorage[${key}]:`, err);
      }
    }, delayMs);
  };
}
