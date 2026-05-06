## Contract Note 008: Translated Text Nullability Semantics

**Operation:** propose
**State:** proposed
**Contract Version:** message-envelope v1.1 (clarification on translated_text type)

**Current Shape:**

Code returns `translated_text` as empty string `""` when translation is pending or failed. Pydantic schema defines it as `str` (not `Optional[str]`), which is correct. But the comment "empty string if null" creates ambiguity about what the actual contract is.

**Proposed Change:**

Clarify that in the API response, `translated_text` is **never null** — it is always a string. When translation has not yet occurred (translation_status = pending_translation or translation_failed), the API returns empty string `""`. When translation has succeeded, it returns the translated text. This is a deliberate choice to simplify frontend logic: the frontend never needs to check `translated_text !== null`, only `translated_text !== ""`.

**Source:** Tweedledee concern about schema ambiguity; contract-note-001 and contract-note-005 both mention "always present" but don't clarify null vs empty-string distinction.

**Backend Impact (Tweedledum):**

Message.to_dict() already implements this: `"translated_text": self.translated_text if self.translated_text else ""`. Pydantic schema should reflect the contract: `translated_text: str` (non-optional). The type annotation now matches the runtime behavior. At the DB layer, translated_text remains nullable (None until translation completes), but the API response always returns a string.

**Frontend Impact (Tweedledee):**

Rendering logic: check `if (message.translated_text && message.translated_text.length > 0)` or equivalently `if (message.translated_text)` — both work because empty string is falsy in JavaScript. No need to check for null. Simpler than Optional[str] semantics.

**Resolution:**

proposed — awaiting Tweedledee's confirmation that empty-string semantics match frontend expectations.
