## Scenario 008: Email-based unlock works fine; SMS-based unlock backup fails due to Twilio quota exhaustion under the spike of unlock requests

**Severity:** degradation

**Setup:**

The 47 locked-out users are not evenly distributed across channels. 35 have email on file; 12 have only SMS. The unlock flow sends email to the 35 immediately (fast). For the SMS cohort, the service fires 12 SMS sends in parallel. Twilio's account has a quota of 100 SMS/minute, and baseline traffic is already at 40/minute. The spike pushes the account to 52 SMS/minute, within quota, but on the third unlock wave (mid-afternoon, user demand spikes as people return from lunch), the SMS send rate hits 110/minute and Twilio rate-limits the service. SMS-unlock requests queue or fail. Email-unlock users recover in 10 minutes; SMS-unlock users wait 20+ minutes or receive hard failures.

**Trigger:**

Unlock-request spike from 12 simultaneous SMS sends hits Twilio rate-limit.

**Expected:**

The service should gracefully degrade: either queue SMS-send with clear messaging to the user ('we're sending your code, may take a few minutes'), or offer email as an alternative on the SMS-unlock screen.

**Concern:**

This is a real degradation waiting to happen if the unlock flow has no flow-control or quota-awareness. The Tweedles will ship unlock as implemented; they may not know Twilio has per-account SMS quotas. The test should verify that under high unlock volume, SMS doesn't silently fail.

**Property:**

For all unlock requests R via SMS, the response to R must either complete within 60 seconds with delivery confirmation, or return clear user-facing messaging that the SMS is queued and delivery may be delayed. No silent failure.

**Implies:**
- Implies implementation decision: does the unlock flow implement Twilio quota-awareness and graceful fallback to email, or does it assume SMS will always succeed? Needs Tweedledum clarity before ship.
- Implies monitoring: Dormouse needs telemetry on SMS-send success rate and queue depth during high-unlock-volume periods.
