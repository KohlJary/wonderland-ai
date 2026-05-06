## Story 005: User joins from EU and sees privacy/consent flow

**Persona:** Sofia, 22, student in Barcelona, first time using a translation app. She downloads it, creates an account with her email, and wants to start chatting.

**Situation:**

Before Sofia can send her first message, the app needs to be honest about what data it's collecting, storing, and using for translation — especially since GDPR applies and translation services may involve sending text to external services.

**Need:**

As Sofia, I want to understand clearly what happens to my messages (are they stored? sent to a third party for translation? kept for model training?) before I send anything, so that I can make an informed choice about whether to trust this app.

**Acceptance:**
- Sofia sees a clear, honest privacy notice before or during signup
- The notice explains: where messages are stored, how translation happens (local vs. cloud), data retention policy, whether messages are used for training, and her rights under GDPR
- She must affirmatively consent before sending her first message
- The notice is not a wall of legal text — it's in plain language a 22-year-old would read

**Tier:** core

**Confusion-flags:**
- The team hasn't specified whether translation happens on-device or via an external API. This determines what Sofia's consent actually covers. That's a Cat decision, not mine, but I'm flagging that users will want to know.
- If translation is external (most likely for quality), which service? Google Translate, AWS Translate, Anthropic, something else? Users in EU have preferences/concerns about US-based services. That's a real tension.
