## Scenario 300: localStorage.setItem throws a QuotaExceededError mid-keystroke; keystroke handler crashes and input is not registered

**GUID:** 01KRY1ARRE8QYC9GT63D0YD5GZ
**Severity:** breakage

**Setup:**

Device's localStorage is nearly full (4.99 MB used of 5 MB). Editor is open with a 2000-char title and 10000-char body already saved to localStorage.

**Trigger:**

User types 'a' into the body field. The onChange handler calls handleBodyChange, which calls localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(newState)). The JSON serialization produces ~13KB (title + body + tags). localStorage throws QuotaExceededError because 4.99MB + 13KB > 5MB.

**Expected:**

One of: (a) the keystroke handler wraps setItem in a try-catch, logs the error, and does NOT re-throw. The keystroke is NOT saved to localStorage, but the input field still registers the 'a' (React state is updated). User can still click Save to persist to the backend. Or (b) the keystroke is debounced and the error is shown as a subtle warning: 'Storage full. Save or clear drafts.'

**Concern:**

If localStorage.setItem throws an unhandled exception, the entire onChange handler crashes. React's error boundary catches it, but the keystroke may not be registered in the input field (React state update before the exception is lost). Or the error propagates to the top level and the editor crashes.

**Property:**

localStorage.setItem errors must not crash the keystroke handler or prevent input from being registered in React state.

**Implies:**
- Implies error handling: wrap setItem in try-catch inside handleTitleChange and handleBodyChange.
- Implies decision: when quota is exceeded, what is the user experience? Fail silently? Warn? Allow Save to backend even if localStorage failed?
