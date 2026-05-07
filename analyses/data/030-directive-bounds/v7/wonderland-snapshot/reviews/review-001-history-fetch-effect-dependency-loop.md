## Review 001: History fetch effect dependency loop

**Files reviewed:** frontend/src/App.tsx
**Verdict:** request-changes

### Findings

#### change-required: useEffect dependency array includes state variables that are set inside the effect
**Location:** frontend/src/App.tsx:65-88
**Quote:**

```
useEffect(() => {
  const loadHistory = async () => {
    // ...
    setHistory(data);
    setHistoryCacheTime(now);
  };
  loadHistory();
}, [historyWindow, history, historyCacheTime]);
```

**Read:** The effect runs loadHistory(), which calls setHistory and setHistoryCacheTime. Both 'history' and 'historyCacheTime' are in the dependency array. Every time these states update, the array changes and the effect re-runs, causing unnecessary re-renders. While the 5-minute cache check prevents repeated API calls, the effect still re-executes on every state update caused by setHistory.
**Concern:** Including state variables in a dependency array when you're setting those variables inside the effect is a React anti-pattern. While the cache check prevents tight loops, this wastes render cycles and represents a fragile pattern. If the cache logic breaks, rapid re-fetch loops could result.
**Request:** Remove 'history' and 'historyCacheTime' from the dependency array. Keep only 'historyWindow'. Use useRef to track cache metadata without triggering re-renders: const cacheRef = useRef({ lastWindow: null, lastFetchTime: 0 }). Check the ref inside the effect before fetching.

### Approvals

- Session start/stop/break cycle logic is clean and correctly tracks state transitions
