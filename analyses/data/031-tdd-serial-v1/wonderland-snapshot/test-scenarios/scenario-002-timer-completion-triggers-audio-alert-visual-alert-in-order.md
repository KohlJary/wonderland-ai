## Scenario 002: Timer completion triggers audio alert + visual alert in order

**Severity:** breakage

**Setup:**

A focus session has been running for 24:59, approaching the 25-minute boundary.

**Trigger:**

The timer reaches exactly 25:00 elapsed.

**Expected:**

Before audio plays, a visual alert (color change or animation) appears. Audio alert plays immediately after visual. Display shows session complete. Start button re-enables.

**Concern:**

Audio will play but visual won't, or they'll fire out of order, or the visual will appear *after* audio (jarring UX). The contract says visual should signal end 'before' sound plays — this timing matters for user experience.

**Property:**

On timer_completion event, (visual_alert_timestamp < audio_alert_timestamp) AND (audio_alert_timestamp - visual_alert_timestamp < 200ms). Session state transitions to completed.
