## Story 002: English-only speaker joins a multilingual group chat

**Persona:** James, 42, software engineer in London. He was added to a chat group that includes German and Japanese speakers. He has no German or Japanese. He wants to see what everyone is saying.

**Situation:**

James receives a message from the group. He sees German and Japanese in the thread. He can infer that something is being discussed, but he's locked out of the actual content. He feels like a bystander in his own chat.

**Need:**

As James, I want all messages in the chat translated to English automatically, so that I can understand and contribute to any conversation regardless of which language someone chose to write in.

**Acceptance:**
- When a German speaker sends a message, James sees it in English within 2-3 seconds
- When a Japanese speaker sends a message, James sees it in English within 2-3 seconds
- James can see that a translation happened (indicator or original-language tag visible)
- Translation happens without James having to configure language pairs or press a button

**Tier:** core

**Confusion-flags:**
- I'm assuming 2-3 second latency again. For a synchronous chat where people are waiting for replies, this might feel slow. But instant translation might be over-engineered for v1. I don't know where the boundary is.
- I don't know if James would want to see the original Japanese/German or only the English. For a learner, seeing original might be valuable. For someone who just wants to participate, it's clutter. This needs user research.
- The phrase 'automatically' is doing a lot of work. Does James have to join a German-English pair explicitly, or does the system infer that he needs it? If there are 5 language pairs in the group, does he see all 5 translated?
