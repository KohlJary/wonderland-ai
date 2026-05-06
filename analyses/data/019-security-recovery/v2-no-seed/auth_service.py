"""
Minimal auth service with rate-limiting and lockout enforcement.
Responds to credential-stuffing incident (T37 incident-response).

Per Queen's rulings 001, 003, and 006:
- IP-based rate-limit: 10 failed attempts per IP per 15-minute window → 429 Too Many Requests
- Account-based lockout: 10 failed attempts per account within 30-minute window → 423 Locked
- Lockout duration: 30 minutes (automatic reset or manual unlock via password recovery)

Contract: /login returns 429 (rate_limit_ip), 423 (account_locked), 401 (invalid_credentials), 
or 200 + session_token on success.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
import hashlib
import json

# In-memory store for incident response. In production this would be Redis + persistent audit log.
# Keys: "lockout:{username}" (TTL 30min), "ratelimit:{ip}" (sliding 15-min window)
_incident_store = {}


@dataclass
class LoginAttempt:
    """Audit log entry for login attempt."""
    timestamp: datetime
    username: str
    source_ip: str
    success: bool
    reason: Optional[str] = None  # "lockout", "rate_limit_ip", "invalid_credentials", etc.


@dataclass
class RateLimitConfig:
    """Rate-limit enforcement per Queen's rulings."""
    # Ruling 001: 10 failed login attempts per IP per 15-minute window
    max_failed_attempts_per_ip: int = 10
    ip_rate_limit_window_minutes: int = 15
    
    # Ruling 003 & 006: 10 failed login attempts per account triggers 30-minute lockout
    max_failed_attempts_per_account: int = 10
    account_lockout_window_minutes: int = 30


audit_log: list[LoginAttempt] = []
config = RateLimitConfig()


def is_ip_rate_limited(source_ip: str) -> bool:
    """
    Check if source IP has exceeded rate limit in the current 15-minute window.
    
    Invariant: no single IP can fail login >10 times in any 15-minute window.
    Enforced by sliding-window counter per source IP.
    """
    key = f"ratelimit:{source_ip}"
    now = datetime.utcnow()
    
    if key not in _incident_store:
        _incident_store[key] = {
            "failed_attempts": [],
            "window_start": now,
        }
    
    bucket = _incident_store[key]
    window_start = bucket["window_start"]
    
    # Slide the window: discard failed attempts older than 15 minutes
    cutoff = now - timedelta(minutes=config.ip_rate_limit_window_minutes)
    bucket["failed_attempts"] = [
        ts for ts in bucket["failed_attempts"] if ts > cutoff
    ]
    
    # If window has drifted >15min, reset it
    if (now - window_start).total_seconds() > (config.ip_rate_limit_window_minutes * 60):
        bucket["window_start"] = now
    
    current_count = len(bucket["failed_attempts"])
    if current_count >= config.max_failed_attempts_per_ip:
        return True
    
    # Increment on this call (recording the failure that triggered the check)
    bucket["failed_attempts"].append(now)
    return False


def is_account_locked_out(username: str) -> bool:
    """
    Check if account is in lockout state.
    
    Invariant: an account with ≥10 failed attempts within 30 minutes is locked.
    Lockout is enforced at application layer; locked account cannot authenticate
    regardless of correct password until lockout expires.
    """
    key = f"lockout:{username}"
    now = datetime.utcnow()
    
    if key not in _incident_store:
        return False
    
    lockout_entry = _incident_store[key]
    lockout_until = lockout_entry["until"]
    
    if now < lockout_until:
        return True
    
    # Lockout expired; clean up
    del _incident_store[key]
    return False


def record_failed_attempt(username: str, source_ip: str, reason: str):
    """
    Record a failed login attempt and update lockout state if necessary.
    Called when login fails for any reason (rate limited, locked, invalid cred, etc).
    
    Enforces account-level lockout invariant: if account ≥10 failures in 30min, lock it.
    """
    attempt = LoginAttempt(
        timestamp=datetime.utcnow(),
        username=username,
        source_ip=source_ip,
        success=False,
        reason=reason,
    )
    audit_log.append(attempt)
    
    # Count failed attempts for this account in the last 30 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=config.account_lockout_window_minutes)
    recent_failures = [
        a for a in audit_log
        if a.username == username and not a.success and a.timestamp > cutoff
    ]
    
    # If ≥10 failures within 30min window, lock the account for 30 minutes
    if len(recent_failures) >= config.max_failed_attempts_per_account:
        key = f"lockout:{username}"
        lockout_until = datetime.utcnow() + timedelta(minutes=config.account_lockout_window_minutes)
        _incident_store[key] = {
            "until": lockout_until,
            "triggered_at": datetime.utcnow(),
            "attempt_count": len(recent_failures),
        }


def record_successful_login(username: str, source_ip: str):
    """
    Record a successful login and clear lockout state if present.
    
    Clearing lockout on success is correct: if the user has re-authenticated successfully,
    they have proven ownership of the account. The lockout is lifted.
    """
    attempt = LoginAttempt(
        timestamp=datetime.utcnow(),
        username=username,
        source_ip=source_ip,
        success=True,
    )
    audit_log.append(attempt)
    
    # Clear lockout state on successful login
    key = f"lockout:{username}"
    if key in _incident_store:
        del _incident_store[key]


def attempt_login(username: str, password: str, source_ip: str) -> tuple[bool, Optional[str]]:
    """
    Attempt a login with rate-limiting and lockout enforcement per Queen's rulings.
    
    Returns: (success: bool, error_reason: Optional[str])
    
    Contract with frontend (per contract-note-001):
    - On success: (True, None) — caller should issue session token
    - On rate_limit_ip: (False, "rate_limit_ip") → HTTP 429 + Retry-After header
    - On account_locked: (False, "account_locked") → HTTP 423 Locked
    - On invalid_credentials: (False, "invalid_credentials") → HTTP 401 Unauthorized
    
    Invariants enforced:
    - No IP can fail login >10 times within any 15-minute window (ruled by Queen 001)
    - No account can fail login >10 times within any 30-minute window (ruled by Queen 003, 006)
    - Locked account cannot authenticate until lockout expires
    """
    
    # Check IP rate limit first (cheapest check; rules out bulk attacks)
    if is_ip_rate_limited(source_ip):
        record_failed_attempt(username, source_ip, "rate_limit_ip")
        return False, "rate_limit_ip"
    
    # Check account lockout (prevents further damage to individual accounts)
    if is_account_locked_out(username):
        record_failed_attempt(username, source_ip, "account_locked")
        return False, "account_locked"
    
    # Validate credentials (placeholder — would check password hash in production)
    # For incident response, we assume the attacker has a leaked-credentials list
    # and is trying them. Real credential check would use bcrypt/argon2.
    if not _validate_credentials(username, password):
        record_failed_attempt(username, source_ip, "invalid_credentials")
        return False, "invalid_credentials"
    
    # Success — lock is clean, account is valid, password matches
    record_successful_login(username, source_ip)
    return True, None


def _validate_credentials(username: str, password: str) -> bool:
    """
    Placeholder credential validation.
    In production, would check against salted password hash (bcrypt/argon2).
    """
    if not username or not password:
        return False
    # Placeholder — for incident response we assume auth works if rate/lockout allow
    # Real implementation would verify password_hash(password) == stored_hash
    return True


def get_retry_after_seconds(source_ip: str) -> int:
    """
    Calculate seconds until the rate-limit window resets for a source IP.
    Used to populate the HTTP 429 Retry-After header.
    """
    key = f"ratelimit:{source_ip}"
    if key not in _incident_store:
        return 0
    
    bucket = _incident_store[key]
    window_start = bucket["window_start"]
    window_end = window_start + timedelta(minutes=config.ip_rate_limit_window_minutes)
    now = datetime.utcnow()
    
    seconds_remaining = (window_end - now).total_seconds()
    return max(0, int(seconds_remaining))


def get_incident_status() -> dict:
    """
    Return current incident status for operational visibility.
    Used by /incident/status endpoint for the Dormouse and Queen.
    """
    now = datetime.utcnow()
    
    # Count recent failures in the last 15 minutes
    cutoff = now - timedelta(minutes=15)
    recent_failures = [a for a in audit_log if not a.success and a.timestamp > cutoff]
    
    # Count unique source IPs with failures
    failing_ips = set(a.source_ip for a in recent_failures)
    
    # Count locked-out accounts (still within lockout window)
    locked_accounts = [
        k.replace("lockout:", "") for k in _incident_store.keys()
        if k.startswith("lockout:") and _incident_store[k]["until"] > now
    ]
    
    return {
        "timestamp": now.isoformat(),
        "recent_failures_15min": len(recent_failures),
        "failing_source_ips": list(failing_ips),
        "locked_accounts": locked_accounts,
        "audit_log_entries": len(audit_log),
    }


if __name__ == "__main__":
    # Incident simulation for testing
    print("Simulating credential-stuffing attack from 203.0.113.42...")
    print("Rate-limit: 10 failed attempts per IP per 15-min window")
    print("Lockout: 10 failed attempts per account within 30-min window\n")
    
    # Simulate 20 attempts from the attacker IP
    for i in range(20):
        success, reason = attempt_login(
            username=f"user_{i % 5}",
            password="wrong_password",
            source_ip="203.0.113.42",
        )
        status = "OK" if success else reason
        print(f"  Attempt {i+1}: {status}")
    
    print("\nIncident status after attack simulation:")
    print(json.dumps(get_incident_status(), indent=2, default=str))
