## Scenario: Marcus starts a 25-minute session and receives notification when it ends

**Severity:** breakage

**Setup:**
Marcus opens the app after a morning meeting, ready for deep work. No session is currently active. His settings are at defaults: 25-minute sessions, 5-minute breaks.

**Trigger:**
Marcus taps the prominent 'Start Session' button on the home screen.

**Expected:**
1. The app immediately shows a countdown timer starting at 25:00
2. The timer updates visibly every second, counting down
3. The display is readable from 3 feet away (font size, contrast)
4. After 25 minutes, an audible notification plays (chime or tone)
5. A visual alert appears and persists for 5 seconds or until dismissed
6. The completed session is recorded in history

**Concern:**
The core workflow will break if:
- POST /session/start fails or returns wrong duration
- /session/current doesn't return remaining_seconds
- Timer doesn't advance on subsequent /session/current polls
- Completion signal is missing or delayed

This is breakage because without a working timer, the entire feature is non-functional. Every user depends on this path.

**Property:**
For any session S with duration D minutes starting at time T_start:
- When user requests /session/current within ε seconds of T_start, remaining_seconds ≈ D*60
- When user requests /session/current after (D*60 - n) seconds have elapsed, remaining_seconds ≈ n
- When D*60 seconds have elapsed, session transitions to state=completed and completed_at is set

**Implies:**
- Implies contract clarification: what is "audible notification"? (Device sound settings? Force sound even in silent mode?)
- Implies UX decision: where is the notification displayed? (Full-screen modal, toast, both?)
