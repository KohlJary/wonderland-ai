## Story 002: Take a break and return to focus

**Persona:** Dev, 28, a backend engineer building microservices. He does deep focus work but often skips breaks because there's no signal that a break is due. He notices he gets slower and more error-prone by mid-afternoon.

**Situation:**

Dev's focus session just ended. He got the notification. Now he needs to know: is there a next step? Does he get a break timer too? Or does he just decide when to start the next session?

**Need:**

As Dev, I want the app to automatically start a 5-minute break timer after my focus session ends, so that I don't skip breaks and lose momentum across the day.

**Acceptance:**
- When a focus session completes, a break timer begins automatically (no extra tap needed)
- The break timer shows 5 minutes and counts down visibly
- When the break ends, I get another notification
- After the break notification, I can tap to start a new focus session without any extra navigation

**Tier:** core

**Confusion-flags:**
- Does the user get a choice about the break, or is it forced? Some pomodoro practitioners skip breaks intentionally when flow is hot.
- Is the break timer always 5 minutes, or can users adjust it (which ties to settings)? The directive says settings exist but I'm not sure if break length is a v1 setting or fast-follow.
