## Story 003: See who I'm talking to and when

**Persona:** Maya, 26, moderator in a polyglot hobby community, needs to keep chat organized and readable even when messages are flowing in multiple languages.

**Situation:**

Maya runs a small community chat. Messages come in English, German, and Japanese mixed together. Right now the translation tool adds confusion because people don't know if they're reading an original or a translation. She needs the chat to stay legible.

**Need:**

As Maya, I want each message to show the sender's name, the original language, the timestamp, and the translation clearly distinguished, so that the chat stays readable and I know who said what when.

**Acceptance:**
- Each message shows sender name, timestamp, original text with language label, translated text with language label.
- The layout is clean enough that I can scan the conversation quickly.
- I can tell at a glance who is a native German speaker vs. who is translating from English.
- The translation is visibly secondary to the original — I can read the original language without it feeling cluttered.

**Tier:** core

**Confusion-flags:**
- UI layout — is this message-in-a-card with original above translation? Side-by-side? Toggle between? I don't want to over-spec, but the clarity piece feels fragile and I'm not sure what's obvious to the front-end team.
- Mobile readability — a lot of translation content in a small viewport. Does the MVP optimize for desktop or mobile? Or both?
