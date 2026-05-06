## Story 003: New user joins and authenticates for the first time

**Persona:** Carlos, 28, a German software engineer who joined a Japanese language-exchange community online. He has never used this chat system before.

**Situation:**

Someone sends Carlos a link to the book club chat. He clicks it. He has no account yet. He wants to start chatting but does not want to fill out forms.

**Need:**

As Carlos, I want to sign up and start chatting with minimal friction, so that I can test whether this group is worth my time before I commit to remembering another login.

**Acceptance:**
- Carlos can create an account or authenticate in fewer than 3 steps
- Carlos can select or confirm his native language (German) during or immediately after signup
- Carlos can immediately send a message after signup — he does not need to wait for confirmation emails or additional setup
- If Carlos closes the chat and returns, he stays authenticated (reasonable session timeout)

**Tier:** core

**Confusion-flags:**
- Does 'basic auth' mean username/password or does it mean something lighter? If lighter, what?
- EU scope + GDPR means we probably need to ask about data storage. Does the MVP include a privacy notice, or is that deferred?
- Does Carlos need to confirm his email address before he can chat, or does email-confirmation happen async in the background?
