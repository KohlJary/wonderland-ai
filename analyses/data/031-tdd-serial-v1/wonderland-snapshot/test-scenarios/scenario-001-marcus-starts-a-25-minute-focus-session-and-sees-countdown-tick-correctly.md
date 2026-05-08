## Scenario 001: Marcus starts a 25-minute focus session and sees countdown tick correctly

**Severity:** breakage

**Setup:**

Marcus's app is open. The focus session timer UI is visible with a START button. No session is active.

**Trigger:**

Marcus clicks START, then waits 2 seconds and reads the display.

**Expected:**

Timer immediately shows 24:58 (approximately; rounding OK). Display counts down every second. MM:SS format is readable.

**Concern:**

The UI will not update in real-time, or will jitter between updates. Or the initial display will show wrong time. The contract says UI is responsible for MM:SS calculation from elapsed_ms, so frontend precision matters here.

**Property:**

For all elapsed milliseconds E such that 0 <= E <= 1500000 (25 min), display_mm_ss(E) == floor(E / 60000) : (E % 60000) / 1000, and display updates within ±100ms of each tick boundary.

**Implies:**
- Frontend responsibility per contract: state object with elapsed_ms, UI tick rate >= 10 Hz
