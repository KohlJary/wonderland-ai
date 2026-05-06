## Review 003: Rate-limiting and account-lockout implementation

**Files reviewed:** src/auth/rate_limit.py, src/auth/service.py, src/auth/endpoints.py, tests/test_auth.py
**Verdict:** block

### Findings

#### block: Missing AccountLockout class breaks imports in service.py
**Location:** src/auth/service.py:14
**Quote:**

```
from src.auth.rate_limit import AccountLockout, RateLimitViolation, RateLimiter
```

**Read:** service.py imports AccountLockout and RateLimitViolation from rate_limit.py, but neither class is defined in rate_limit.py. Only RateLimiter is defined.
**Concern:** The code will not run. When service.py calls self.account_lockout = AccountLockout(...) on line 52, the module will fail with ImportError. This blocks merge entirely.
**Request:** Define AccountLockout class in rate_limit.py with a compatible interface: __init__(failure_threshold, lockout_duration?), check(email), record_failure(email), record_success(email). Or redesign to fold account lockout logic into RateLimiter directly rather than as a separate class.

#### block: RateLimiter instantiation signature mismatch
**Location:** src/auth/service.py:52-53
**Quote:**

```
self.rate_limiter = rate_limiter or RateLimiter(requests_per_minute=10)
self.account_lockout = account_lockout or AccountLockout(failure_threshold=5)
```

**Read:** service.py instantiates RateLimiter with requests_per_minute=10 and AccountLockout with failure_threshold=5, but RateLimiter.__init__ (line 67 of rate_limit.py) takes db_session_factory, not requests_per_minute.
**Concern:** The code will fail with TypeError at runtime. The AuthService is the one with access to the DB session factory, but RateLimiter's constructor signature expects it directly. The interface is inverted — RateLimiter needs the factory, but service.py is treating it as a config object with request limits.
**Request:** Redesign the interface: either (a) have AuthService.__init__ pass db_session_factory to RateLimiter (and AccountLockout if it exists), or (b) move the request/failure thresholds into class constants (as you have done: IP_MAX_FAILURES, EMAIL_MAX_FAILURES) and have RateLimiter's __init__ take only the factory. Then in service.py, instantiate: self.rate_limiter = RateLimiter(db_session_factory) if not rate_limiter else rate_limiter.

#### block: RateLimitViolation exception not defined
**Location:** src/auth/service.py:71-78
**Quote:**

```
try:
    self.rate_limiter.check(source_ip)
except RateLimitViolation as e:
    ...
    retry_after_seconds=e.retry_after_seconds,
```

**Read:** service.py catches RateLimitViolation and accesses e.retry_after_seconds, but this exception class is not defined in rate_limit.py. RateLimiter.check() returns a RateLimitResult object, not raising an exception.
**Concern:** The code will not run. The exception class doesn't exist, and the flow is inverted from what RateLimiter actually does. The rate_limit.py module returns RateLimitResult; service.py must check the result status, not catch an exception.
**Request:** Remove the try/except blocks catching RateLimitViolation. Instead, redesign the flow: call self.rate_limiter.check(source_ip), store the result, and check result.status. If status is not ALLOWED, populate LoginResult with reason and retry_after_seconds. Do the same for account lockout checks.

#### block: Session.is_valid() method does not exist
**Location:** src/auth/service.py:141
**Quote:**

```
.filter(Session.is_valid())
```

**Read:** service.py calls Session.is_valid() as a filter predicate, but the Session model only defines is_expired() as an instance method, not a class/filter method.
**Concern:** The code will not run. SQLAlchemy will raise AttributeError when trying to apply is_valid() to a query. The logic here is also confusing — is_expired() checks if the session has expired, but you're using is_valid() in a filter. These need to be aligned.
**Request:** Replace .filter(Session.is_valid()) with .filter(Session.expires_at > datetime.now(timezone.utc)). If you prefer a method, add a class method or filter expression to Session that encapsulates this logic, e.g., Session.is_valid_filter() returning the timestamp comparison.

#### change-required: No observability instrumentation for rate-limit or lockout events
**Location:** src/auth/rate_limit.py (entire module)
**Quote:**

```
The RateLimiter class has no logging, metrics, or event-emission code. When rate_limited or account_locked status is returned, no observable event is created.
```

**Read:** The rate_limit.py module is a pure control layer: it checks state and returns decisions, but has no hooks for observability. When a rate-limit decision fires, nothing logs it, emits a metric, or creates an event. When an account is locked, same silence.
**Concern:** Queen ruling #3 (severity=high) explicitly requires 'production telemetry required before v1 ship'. The Queen also ruled on breach-notification obligations, which depends on knowing which credentials succeeded during the attack window. The current code logs failed attempts to FailedAttempt but has no instrumentation for rate-limit triggers or lockout triggers. A sysadmin cannot answer: 'Which IPs are currently rate-limited?', 'How many accounts are locked?', 'Is the attack still active?'. This violates the ruling and leaves the system unobservable during an incident.
**Request:** Add event emission to RateLimiter and AccountLockout (once it's defined). For each decision (IP_THROTTLED, ACCOUNT_LOCKED), emit a structured log or metric: log(event_type='rate_limit_ip_throttled', source_ip=..., current_count=..., threshold=...) and similarly for account lockout. These events should be queryable for incident response (e.g., 'show me all rate-limit events from the last hour' or 'how many accounts are locked right now'). Dormouse's contract note should specify the exact shape of these events before implementation resumes.

#### change-required: Password-reset endpoint not exempt from rate-limiting (Queen ruling #2 unaddressed)
**Location:** src/auth/endpoints.py, src/auth/service.py
**Quote:**

```
The login endpoint now has rate-limiting and lockout checks, but no /password-reset endpoint exists in endpoints.py, and no escape hatch is defined to exempt password-reset from the rate limiter if it does exist.
```

**Read:** Queen ruling #2 states: 'Password-reset endpoint rate-limiting — must not lockout legitimate password-recovery flow'. This implies that users who were locked out by the attack should be able to reset their password without being further rate-limited. The current implementation provides no escape hatch for this scenario.
**Concern:** A legitimate user whose account was compromised during the attack will be locked (per the per-email lockout) and will not be able to attempt password reset, because if password-reset shares the rate-limit logic, they will hit the per-email lockout again. If password-reset is read-only (no mutation), it should be exempt from rate-limiting entirely. The Queen's ruling treats this as v1-blocking; the implementation does not address it.
**Request:** Before shipping, confirm the scope of /password-reset: does it exist? If yes, what is its contract? If it's a read-only endpoint (email lookup for reset), it should bypass rate-limiting entirely. Add a parameter to the rate-limit checks (e.g., skip_rate_limit=True for reset flows) or create a separate code path that doesn't check limits. Document this in the endpoints and service layers so the next reviewer knows the escape hatch exists.

#### change-required: Successful login during attack window not observable
**Location:** src/auth/service.py:101-107
**Quote:**

```
session = Session.make(...)
db.add(session)
db.commit()
...
self.account_lockout.record_success(normalized_email)
return LoginResult(ok=True, session=session)
```

**Read:** When a login succeeds, the code creates a session, commits it, and records success to reset the lockout counter. But no event is emitted to mark this successful login as part of the attack-response instrumentation.
**Concern:** Dormouse and Alice both flagged this: the Queen's breach-notification ruling requires knowing which credentials succeeded during the attack window, so the team can notify users whose passwords were compromised. The system has no way to distinguish 'successful login during the attack window' from 'successful login at any other time'. This is foundational for the breach-notification work the Queen ruled on.
**Request:** Add event emission or logging when a successful login occurs: log(event_type='login_success', email=..., session_id=..., source_ip=..., occurred_at=...). This should be a structured log or metric that can be queried during incident response to extract the set of accounts that logged in successfully during the attack period. This is a v1 blocker for breach notification work.

#### change-required: Tests reference undefined classes (AccountLockout, RateLimitViolation)
**Location:** tests/test_auth.py:10, 38-40, 58
**Quote:**

```
from src.auth.rate_limit import AccountLockout, RateLimiter

auth = AuthService(...,
    rate_limiter=RateLimiter(requests_per_minute=100),
    account_lockout=AccountLockout(failure_threshold=3, lockout_duration=timedelta(seconds=10)),
)
```

**Read:** The test fixtures try to instantiate AccountLockout and RateLimiter with parameters that don't match the actual class signatures. AccountLockout doesn't exist; RateLimiter's signature is incompatible.
**Concern:** The tests cannot run. They will fail at import time (AccountLockout doesn't exist) and at instantiation time (signature mismatches). The test coverage for rate-limiting and lockout is well-intentioned and thorough, but the implementation underneath is not yet wired correctly.
**Request:** Once AccountLockout is defined and the interface issues are resolved, update the test fixtures to match the real signatures. The tests themselves (test_rate_limit_blocks_excessive_requests_from_single_ip, test_account_lockout_fires_after_threshold, etc.) are well-written and should pass with the corrected implementation.

#### suggestion: RateLimiter._db context manager usage unclear
**Location:** src/auth/rate_limit.py:98-107
**Quote:**

```
with self._db() as db:
    failure_count = (
        db.query(FailedAttempt)
        .filter(...)
        .count()
    )
```

**Read:** The code assumes self._db() is callable and returns a context manager (a sessionmaker). This is SQLAlchemy standard, but it's not validated in __init__. If a caller passes something that doesn't work as a context manager, the error will be cryptic.
**Concern:** Minor: this is a quality-of-life issue, not a blocker. But given that RateLimiter is initialized with db_session_factory in the current design, it might be clearer to add a docstring or type hint specifying what kind of object this should be, or to add a validation check in __init__.
**Request:** Add a docstring to RateLimiter.__init__ specifying that db_session_factory should be a SQLAlchemy sessionmaker (callable that returns a context manager). Or add a runtime check: try to create a session and catch exceptions with a clear message if the factory doesn't work.

### Approvals

- The conceptual structure of rate_limit.py is sound: separate IP-based and email-based checks, window-based thresholds, database-backed state. This architecture will survive a restart, and all decisions are queryable.
- The test cases for rate-limiting and account-lockout (once the classes are defined correctly) are thorough and well-named. They cover per-IP independence, per-email independence, interaction between the two, and counter-reset on success. This is good coverage.
- The HTTP status codes in endpoints.py are correct: 429 for rate-limit, 423 for account locked, 401 for credential failure. The Retry-After headers are included, which is proper HTTP protocol.
- The endpoint docstring updates are clear about what changed and why. The comments tracing back to the incident thread are helpful for future readers.

### Cross-domain references

- The AccountLockout class doesn't exist; this is an immediate architectural decision: should lockout logic live in a separate class (cleaner separation) or fold into RateLimiter? The Cat may have a view on this, but it's not blocking the blocker list — once the class exists with the right interface, the architecture works.
- Observability (logging/metrics for rate-limit and lockout events) is a Dormouse concern and a Queen ruling gate. This must be instrumented before v1 ships. Hatter's test scenarios (particularly the 'observable event' scenarios) should become acceptance criteria for this work.
- The /password-reset scope and exemption is a Queen ruling (#2) that must be confirmed with the team before this implementation can be final. If /password-reset doesn't exist yet, that's a deferral decision; if it does, the escape hatch must be explicit.
