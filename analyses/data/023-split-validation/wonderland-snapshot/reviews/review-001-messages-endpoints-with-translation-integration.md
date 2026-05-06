## Review 001: Messages endpoints with translation integration

**Files reviewed:** src/backend/api/messages.py, src/backend/models.py, src/backend/translation_service.py, src/backend/main.py, tests/test_messages.py
**Verdict:** request-changes

### Findings

#### change-required: N+1 query in list_messages: sender lookup per message
**Location:** src/backend/api/messages.py:229-230
**Quote:**

```
for msg in messages:
        # Fetch sender name
        sender = _get_user_or_404(msg.sender_id, db)
```

**Read:** For each message in the conversation, you are issuing a separate database query to fetch the sender by id. If a conversation has 50 messages, this becomes 1 query (fetch messages) + 50 queries (fetch each sender) = 51 total. This is the classic N+1 problem.
**Concern:** As conversation history grows, the performance of list_messages degrades linearly with the number of messages. This will be noticeable in production. The Message model already has a relationship to User via sender_id; SQLAlchemy can eager-load that relationship in a single query using joinedload.
**Request:** Change the query to use `joinedload(Message.sender)` when fetching messages. This reduces the query count from N+1 to 1 regardless of message count. Example: `db.query(Message).options(joinedload(Message.sender)).filter(...).all()`

#### suggestion: Stub translation service returns identifiable output
**Location:** src/backend/translation_service.py:138
**Quote:**

```
return f"[{target_lang}] {text}"
```

**Read:** The stub vendor prepends the language code in brackets to the input text. This is useful for development — you can see that translation 'happened' — but it's not realistic. A real vendor would return a translation that looks like natural language output in the target language.
**Concern:** Frontend developers testing with the stub may build assumptions about translation output that won't hold with a real vendor. For example, they might not notice that the translation broke their UI layout because the stub output is so short. When you swap to a real vendor, layout issues surface.
**Request:** Consider adding a TODO comment noting that the stub should eventually be replaced with real translations (you already have this), but optionally: add a config flag to control whether the stub prepends the language tag. This lets testers toggle between 'identifiable stub' mode and 'realistic stub' mode. Not blocking; a suggestion for future work.

#### note: Sender fetch could race with soft-delete
**Location:** src/backend/api/messages.py:229-230
**Quote:**

```
sender = _get_user_or_404(msg.sender_id, db)
```

**Read:** After fetching a message, you fetch its sender by id. The Message row in the database points to a specific User id. However, between the two queries, the User could be soft-deleted by another request (deleted_at set to non-null).
**Concern:** If a user is soft-deleted between the time you fetch the message and fetch the sender, _get_user_or_404 will raise 404 and the entire list_messages call fails. This is probably rare in practice (soft-delete is not the same as delete), but it's a edge case. More likely: a concurrent request soft-deletes a user, and one list_messages call in flight gets a 404 partway through the message loop.
**Request:** This is low priority given the soft-delete model (users are rarely deleted), but document the assumption: 'Assumes users are not soft-deleted while their messages are being read.' Alternatively, if this becomes a real issue, fetch all relevant senders in bulk before the loop to avoid the race window. Not blocking for now.

#### suggestion: MessageResponse.created_at could be None in a real scenario
**Location:** src/backend/api/messages.py:70
**Quote:**

```
created_at: str
```

**Read:** The created_at field is defined as `str`, never optional. The code produces an isoformat string, but the Message model's created_at column has `server_default=func.now()`, which means the database sets it on insert. In practice, it will never be None. However, the code defensively handles the None case when converting to isoformat.
**Concern:** The code says `created_at=message.created_at.isoformat() if message.created_at else ""` — this returns an empty string if created_at is somehow None. Returning an empty string as a timestamp is confusing; the caller cannot tell if the message was never given a timestamp or if something went wrong. If you are confident created_at will always be set by the database, the defensive check is unnecessary and suggests uncertainty about the invariant.
**Request:** Either: (1) Assert that created_at is not None (Python level) and remove the defensive check, making the invariant explicit. Or (2) Make created_at optional in the response schema (`created_at: str | None`) and return None if it's missing, making the response shape honest about the possibility. I recommend (1) — assert it, remove the defensive code, document the invariant in the Message model.

#### suggestion: Error message in translation_service imports TranslationServiceError but does not use it
**Location:** src/backend/api/messages.py:23
**Quote:**

```
from src.backend.translation_service import TranslationServiceError, get_translation_service
```

**Read:** The import statement brings in TranslationServiceError, but it is never used in messages.py. The translation_service.translate() method returns (bool, str) tuples for success/error, not exceptions. The exception class is defined but not raised in messages.py.
**Concern:** Unused imports are noise; they suggest the code is catching exceptions that it doesn't actually catch, making the reader's job harder. If the intent is to catch and handle TranslationServiceError, the code should do that. If not, the import should be removed.
**Request:** Remove the TranslationServiceError import from messages.py. The contract is already clear: translate() returns (success, result) tuples. If you later decide to switch to exception-based error handling, add the import back at that time.

#### change-required: Models use string type for text_language, should use enum
**Location:** src/backend/models.py:87
**Quote:**

```
text_language = Column(String(10), nullable=False)
```

**Read:** The Message model stores text_language as a bare string in a String(10) column. However, only specific language codes are valid (those in the conversation's language_pair). The code enforces this in the API layer (see messages.py line 149), but the database schema allows any string.
**Concern:** A future developer, or a script, could insert a message with text_language='xyzabc' into the database directly, and the invariant 'text_language matches one of the two languages in language_pair' would be violated. The database is permissive where it should be restrictive. More importantly, the code hardcodes language validation in two places (create_message and list_messages) — if you add a third endpoint that accepts messages, you have to remember the validation again.
**Request:** Add a CheckConstraint on the Message table that enforces text_language in a fixed set (or reference the conversation's language_pair via a join constraint, though that's complex in SQLAlchemy). At minimum, document the assumption in the Message docstring: 'text_language MUST be one of the two languages in the conversation's language_pair; this is NOT enforced by the database schema, only by the API layer.' If this assumption is violated, operations will fail. Better: add a database-level constraint or switch to an Enum column. For now, add the documentation.

#### suggestion: Conversation.get_languages() is called multiple times per request
**Location:** src/backend/api/messages.py:149, 222
**Quote:**

```
languages_in_pair = conversation.get_languages()
if payload.language not in languages_in_pair:
    ...
# Later, in list_messages:
languages_in_pair = conversation.get_languages()
if read_language not in languages_in_pair:
```

**Read:** The method get_languages() parses the LanguagePair enum value (e.g., 'en_de') and splits it on underscore to return ['en', 'de']. This is a cheap operation (string split), but it's called in both create_message and list_messages, and could be called again in the future.
**Concern:** No real performance issue, but the code repeats the same pattern (get_languages, validate language against the list) twice without DRY principle. If the validation logic changes, you have to update two places. If you add a third endpoint, you have to remember the pattern again.
**Request:** Consider adding a helper method on Conversation like `is_language_in_pair(lang: str) -> bool` that encapsulates the validation. Then call `if not conversation.is_language_in_pair(payload.language)` — clearer intent, DRY, and centralized logic. Not blocking, but improves maintainability.

#### note: Test fixtures use hardcoded user ids; tests assume id=1 is available
**Location:** tests/test_messages.py:163, 168
**Quote:**

```
def _get_current_user(db: Session) -> User:
    """Get the current authenticated user. For MVP, stub: returns user with id=1.
    ...
    user = db.query(User).filter(
        User.id == 1,
        User.deleted_at.is_(None)
    ).first()
```

**Read:** The stub _get_current_user always returns user with id=1. The tests create fixture users but don't guarantee id=1. In most test setups (fresh SQLite DB per test), the first user created will have id=1, so the tests pass. But this is fragile: if someone changes the fixture order or adds a factory that creates users before the test fixtures, ids will shift and tests will fail mysteriously.
**Concern:** The coupling between the stub auth logic ('always return id=1') and the test setup ('first fixture created has id=1') is implicit. It works by accident. If a new team member adds a test that creates users differently, or if the test database is pre-populated, the assumption breaks.
**Request:** Either: (1) Refactor _get_current_user to accept a dependency (e.g., a test config that specifies which user to return) so tests can control it explicitly. Or (2) Add a comment in the test file documenting the assumption: 'Assumes first User fixture created has id=1. Tests will fail if user ids are not sequential from 1.' Or (3) Change _get_current_user to look up a user by some other identifier (e.g., by username 'system' or by a flag), making it more explicit. For now, add the comment in the test file.

### Approvals

- The overall structure is clear: schema redesign separates concerns (User, Conversation, Message) with explicit relationships and soft-delete support.
- Contract documentation is excellent. Each endpoint and service has a docstring that names the contract and references relevant contract-notes. This makes it easy to trace decisions back to the agreement.
- Error handling in list_messages is thoughtful: translation failures return the original text + a generic error message, never fail the entire request. This aligns with the 'never fail' contract.
- Pydantic schemas (MessageCreateRequest, MessageResponse) are well-shaped with clear field types and documentation.
- The test suite is comprehensive: happy path, invalid inputs, soft-delete filter, translation flows, roundtrips. Good coverage of the contract space.
- Soft-delete filtering is consistently applied (WHERE deleted_at IS NULL in Conversation and Message queries).
- Translation service abstraction is well-named and has a clear contract: synchronous, <300ms timeout, returns tuples. The stub implementation is honest about being a stub and includes a TODO for real vendor integration.

### Cross-domain references

- The sender lookup race condition (note finding) is low priority for now but worth tracking in the Dormouse's observation log — if soft-delete becomes more common, this edge case may need revisiting.
- The language validation logic (text_language must be in language_pair) is currently API-only. If the Cat or a future ADR proposes data validation at the boundary, this constraint should be reflected in the database schema as well.
