## Story 006: View my own account settings and profile

**Persona:** Morgan, 26, wants to keep their homepage tidy. They've been on the platform for a few weeks and want to update their email, change their password, and see what data the site holds about them.

**Situation:**

Morgan is in their account dashboard looking for settings. They want to know what options are available to them (email change, password change, etc.) and whether they can export or inspect their data.

**Need:**

As Morgan, I want a settings page where I can change my email and password, and see what data you have about me, so that I can stay in control of my account.

**Acceptance:**
- Settings page is accessible from the homepage (e.g., a menu or profile link)
- Can change email (with confirmation to the new email address)
- Can change password (requires old password or email confirmation)
- Can export personal data or see a summary of what's stored (GDPR right of access)
- Account deletion button is on this page (not easy to hit by accident, but visible)

**Tier:** core

**Confusion-flags:**
- GDPR right of access: does the export need to be in a specific machine-readable format, or is a summary enough for MVP? This is a compliance question, not a UX one, but it affects what we build.
- Session management: if Morgan changes their password, should existing sessions be invalidated immediately? This affects their sense of control.
