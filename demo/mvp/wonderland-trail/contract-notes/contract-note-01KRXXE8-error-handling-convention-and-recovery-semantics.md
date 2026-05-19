## Contract Note 017: Error handling convention and recovery semantics

**GUID:** 01KRXXE8K4TTDGGPWXW6FE9VV1
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

n/a, fresh feature thread

**Proposed Change:**

POST/PATCH error responses use HTTP convention: 4xx (validation/client error), 5xx (server error). Response shape: {error: string, detail: string, field?: string}. Client treats both 4xx and 5xx as retryable (preserve localStorage, show error, allow manual retry). Clear localStorage only on 200 response.

**Source:** Your question 3 + ticket-001KRXRVT (Save failure and recovery).

**Frontend Impact (Tweedledee):**

Preserve localStorage on all errors. Show error text to user. Button remains clickable for retry. Network timeout treated as 5xx.

**Backend Impact (Tweedledum):**

Return errors in above shape. Both 4xx and 5xx are recoverable from the client's standpoint.
