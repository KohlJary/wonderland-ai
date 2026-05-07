## Story 008: Feature 001 Happy Path — Marcus starts and completes a focus session

**Feature:** Start and complete a focus session with breaks (feature-001)

**Persona:** Marcus, 28, a freelance writer who works from home and loses track of time in deep focus.

**Happy-path scenario:**

1. Marcus opens the app on his laptop. The home screen shows a large "Start Session" button and displays current settings (25 min focus, 5 min break).

2. Marcus taps "Start Session." The screen transitions to a full-screen countdown timer showing "25:00" and the label "FOCUS."

3. Marcus closes his email client and opens his brief. Over 25 minutes, he writes uninterrupted. The timer counts down, visible but not demanding.

4. At 25:00 mark, the timer hits 0:00. A clear visual transition happens (screen flashes, color change, or animation) and audio notification plays. The screen shows "Session Complete! Take a break?" with two buttons: "Start Break" and "Skip to Next Session."

5. Marcus taps "Start Break." The screen transitions to a 5-minute break timer, visually distinct from the session timer (e.g., different color, labeled "BREAK," inviting tone). Marcus stretches, gets water, checks his phone.

6. At the 5-minute mark, the break timer hits 0:00. Another clear transition and notification fires. The screen shows "Break's over! Ready to focus?" and presents the home screen with "Start Session" prominent.

7. Marcus taps "Start Session" again and another 25-minute countdown begins.

8. Marcus completes three 25-minute sessions in a row (with breaks between). After the third session ends and he skips the break, the home screen shows a "Today's Count: 3 sessions / 75 minutes" card at the top, confirming he's tracked his work.

**Expected result:**

Marcus never watches the clock. He trusts the timer, gets clear notifications at boundaries, and feels permission to rest. His session count accumulates on screen, proving he worked.

**Contract assumptions validated:**

- Session state transitions are instant and obvious (phase change fires immediately).
- Frontend holds and displays timer state (backend does not tick the clock).
- Session completion is recorded (backend persists the fact).
- Settings (25 min, 5 min) are applied from the start and don't change mid-session.
