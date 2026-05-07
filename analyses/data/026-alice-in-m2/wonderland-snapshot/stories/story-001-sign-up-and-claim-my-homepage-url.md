## Story 001: Sign up and claim my homepage URL

**Persona:** Jordan, 28, a musician who wants an online presence but dislikes algorithmic feeds. Wants a simple, owned space for their work.

**Situation:**

Jordan has some recordings and photos they want to share with collaborators and fans, but doesn't want to depend on Instagram or SoundCloud. They are new to self-hosting but technically curious.

**Need:**

As Jordan, I want to sign up with just an email and password and immediately own a URL like /~jordan where my content lives, so that I have a permanent, owned space I control.

**Acceptance:**
- Email validation works (no typo confirmation needed for MVP, but sent validation email exists)
- Password meets basic strength requirements (12+ chars or equiv)
- After signup, user is logged in and can immediately navigate to /~[their-chosen-username]
- Username is globally unique and case-insensitive in lookup
- Signup completes in under 30 seconds for a user with password manager
- Error messages are clear (email already in use, username taken, etc.)

**Tier:** core

**Confusion-flags:**
- GDPR deletion: when Jordan deletes their account, must all hosted content vanish immediately, or is there a grace period? If immediate, does a 'purge' operation block new signups with that username?
- Username reclamation: if Jordan abandons their account (but doesn't delete), can someone else claim /~jordan after 6 months? Or is the username tied to the account forever?
