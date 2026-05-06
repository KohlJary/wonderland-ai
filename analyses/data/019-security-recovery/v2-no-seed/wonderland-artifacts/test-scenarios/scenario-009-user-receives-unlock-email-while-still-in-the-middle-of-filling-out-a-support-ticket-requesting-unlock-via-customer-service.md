## Scenario 009: User receives unlock email while still in the middle of filling out a support ticket requesting unlock via customer service

**Severity:** degradation

**Setup:**

User got locked out 2 minutes ago. They immediately email support@company.com requesting manual unlock (what they think is the only path). At the same time, or slightly after, the automated unlock email arrives. User now has two unlock paths live: the human support path and the automated email path. They unlock via email immediately. They then also get a response from support 5 minutes later saying 'your request has been assigned to a specialist' or 'let us confirm your identity via security question.' The user is already unlocked but support is still processing. Two scenarios here: (a) user opens the support communication thinking they still need it, wastes 5 minutes on a security questionnaire for an account that is already unlocked, or (b) support system sees the account is no longer locked and sends a 'request cancelled' email that looks like a support denial, and the user panics thinking support said no.

**Trigger:**

User has two concurrent unlock paths (automated and human support) in flight simultaneously; one completes while the other is still processing.

**Expected:**

The system should mark a support-unlock-request as stale once the account is re-unlocked via any path. Support should see the account status change and either auto-close the request with 'account was unlocked via automated unlock email' messaging, or proactively reach out with 'your account is already unlocked' framing.

**Concern:**

This is a coordination failure between the automated unlock path and the support-request workflow. If they don't coordinate, the user experience is chaotic—they think they might still need support, or they think support denied them, when actually the issue resolved faster than expected. Support system visibility of account unlock status is non-trivial.

**Property:**

For all support-unlock-requests S initiated by user U, if account A (that S targets) is unlocked via any mechanism before S is fulfilled, S must be transitioned to a terminal state ('resolved: account unlocked via other path') and U must be notified of the resolution.

**Implies:**
- Implies data coordination: does the support-request system have real-time visibility into account unlock status? Needs architectural review — flag for Cat.
- Implies notification coordination: what does the user see if support and automated unlock race? Messaging matters here. Flag for Tweedledee.
