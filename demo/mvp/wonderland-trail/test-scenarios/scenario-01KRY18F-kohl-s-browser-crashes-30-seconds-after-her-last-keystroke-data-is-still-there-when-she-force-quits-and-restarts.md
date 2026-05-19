## Scenario 244: Kohl's browser crashes 30 seconds after her last keystroke — data is still there when she force-quits and restarts

**GUID:** 01KRY18F88GKW92A57SY2C1JVP
**Severity:** breakage

**Setup:**

Kohl has typed 'Experiment 7: thermal resonance at 450K' into the title and 'Initial readings suggest...' into the body. At least 300ms have passed since her last keystroke (debounce window has closed and localStorage write has completed).

**Trigger:**

The browser process crashes hard (simulated: no graceful close, just termination). Kohl force-quits and restarts the browser, reopens the app.

**Expected:**

The note editor loads with 'Experiment 7: thermal resonance at 450K' in the title and 'Initial readings suggest...' in the body. The data persisted through the crash because it was written to localStorage before the crash occurred.

**Concern:**

If the data is only in memory and hasn't flushed to localStorage, the crash wipes it. The debounce timing has to actually complete the write before a crash can wipe it. This tests the end-to-end flow, not just the happy path.

**Property:**

localStorage flush completes before debounce window closes
