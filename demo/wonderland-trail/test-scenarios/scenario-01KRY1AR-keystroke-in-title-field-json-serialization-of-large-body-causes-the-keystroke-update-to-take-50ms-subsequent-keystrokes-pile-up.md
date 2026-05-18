## Scenario 302: Keystroke in title field; JSON serialization of large body causes the keystroke update to take 50ms; subsequent keystrokes pile up

**GUID:** 01KRY1ARRE8QYC9GT63D0YD5H1
**Severity:** degradation

**Setup:**

Editor has a small title and a very large body (~15KB of markdown with code blocks and tables). User is typing into the title field.

**Trigger:**

User types the 20th character of the title. The keystroke handler calls handleTitleChange, which calls localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(newState)). The JSON stringify takes 40ms because it's serializing the entire 15KB body. Meanwhile, the user is still typing the 21st character.

**Expected:**

The keystroke is registered and visible in the input field immediately (React state update). The localStorage write happens asynchronously (or is scheduled) so it does not block the input field responsiveness. Subsequent keystrokes do not queue up or feel sluggish.

**Concern:**

If JSON.stringify and localStorage.setItem are not debounced, and the body is very large, the keystroke handler becomes slow. Kohl types into the title and feels a perceptible lag — 'the input feels sluggish'. This is a degradation of responsiveness. Or if multiple concurrent setItem calls queue up (because the previous one hasn't finished), memory grows.

**Property:**

Keystroke handling must not introduce observable lag in the input field, even with large body content.

**Implies:**
- Implies implementation detail: consider debouncing the localStorage write (e.g., 100ms) so that rapid keystrokes batch into a single write. Or consider using localStorage.setItem async wrapper or Web Workers.
- Implies: there is a tradeoff between 'immediate persistence' (every keystroke flushed) and 'responsive input' (debounce to batch writes). The story should clarify the requirement.
