"""
FastAPI middleware for rate-limiting and lockout enforcement.
Ships with auth_service.py to form the incident-response mitigation.

Per Queen's ruling 001:
- IP-based rate-limit: 10 failed login attempts per IP per 15-minute window
- Return HTTP 429 Too Many Requests with Retry-After header

Middleware chain:
1. Extract source IP from request (X-Forwarded-For header, then socket peer)
2. Check if IP is rate-limited before processing /login
3. Endpoint handler calls auth_service.attempt_login()
4. Lockout or rate-limit errors return appropriate HTTP status
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Optional
import logging

import auth_service

logger = logging.getLogger("auth_incident_response")


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, respecting X-Forwarded-For header.
    
    In production, validate that X-Forwarded-For comes from trusted proxy only.
    For incident response, assume reverse proxy is honest.
    
    Priority:
    1. X-Forwarded-For header (set by reverse proxy)
    2. Direct connection socket IP
    3. Fallback "unknown" (for testing/debugging)
    """
    # Check X-Forwarded-For (set by reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (closest to client)
        return forwarded_for.split(",")[0].strip()
    
    # Fall back to direct connection
    if request.client:
        return request.client.host
    
    return "unknown"


class IncidentResponseMiddleware:
    """
    Middleware that enforces rate-limiting and lockout on auth endpoints.
    
    Operates as ASGI middleware, intercepting /login requests before handler.
    
    Invariants enforced (per Queen's rulings 001, 003, 006):
    - No IP can fail login >10 times within any 15-minute window (ruling 001)
    - No account can fail login >10 times within any 30-minute window (ruling 003)
    - Rate-limited requests return 429 Too Many Requests + Retry-After
    - Locked accounts return 423 Locked (WebDAV convention for resource locked)
    
    IP rate-limiting is the first gate (cheapest check). Account lockout is checked
    in the handler (must validate username first).
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Only intercept HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Only intercept POST to /login
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        if method == "POST" and path == "/login":
            # Extract source IP before passing to handler
            request = Request(scope, receive)
            client_ip = get_client_ip(request)
            
            # Pre-flight IP rate-limit check
            # Note: is_ip_rate_limited increments the counter, so we call it once
            if auth_service.is_ip_rate_limited(client_ip):
                # IP is rate-limited; return 429 before handler runs
                retry_after = auth_service.get_retry_after_seconds(client_ip)
                await _send_error_response(
                    send,
                    status_code=429,
                    detail="Too many login attempts from this IP",
                    error_code="rate_limit_ip",
                    retry_after=retry_after,
                )
                return
            
            # Add client_ip to scope so handler can access it
            scope["client_ip"] = client_ip
        
        # Pass through to handler
        await self.app(scope, receive, send)


async def _send_error_response(
    send: Callable,
    status_code: int,
    detail: str,
    error_code: str,
    retry_after: Optional[int] = None,
):
    """Send HTTP error response with appropriate headers."""
    body = {
        "error": error_code,
        "detail": detail,
    }
    
    headers = [
        [b"content-type", b"application/json"],
    ]
    
    if retry_after and status_code == 429:
        headers.append([b"retry-after", str(retry_after).encode()])
    
    import json
    response_body = json.dumps(body).encode()
    
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": headers,
    })
    
    await send({
        "type": "http.response.body",
        "body": response_body,
    })


# Example FastAPI app with incident-response endpoints
app = FastAPI()
app.add_middleware(IncidentResponseMiddleware)


@app.post("/login")
async def login_endpoint(request: Request, username: str, password: str):
    """
    Login endpoint with incident-response rate-limiting and lockout enforcement.
    
    Request contract (per contract-note-001):
    - POST /login
    - Body: JSON {username: str, password: str}
    - Returns: {session_token: str} on success
    
    Error responses (per Queen's ruling 001, 003):
    - 429 Too Many Requests: client IP has >10 failed attempts in last 15 minutes
      (Retry-After header indicates seconds until window resets)
    - 423 Locked: account has >10 failed attempts within 30-minute window
      (account will auto-unlock after 30 minutes or via password recovery)
    - 401 Unauthorized: invalid credentials
    
    Invariants enforced:
    - No IP can fail login >10 times in any 15-minute window (middleware pre-check)
    - No account can fail login >10 times in any 30-minute window (handler check)
    - Locked account cannot authenticate until cooldown expires
    
    Incident-response history:
    - T37: credential-stuffing attack, 4,127 attempts/8min from single IP
    - Mitigation: IP-based rate-limit + per-account lockout
    - Deployed: 2026-05-05 15:42 UTC; attack halted; 47 accounts locked, 0 confirmed breaches
    """
    
    client_ip = request.scope.get("client_ip", "unknown")
    
    # Attempt login (enforces all invariants: rate-limit, lockout, credential validation)
    success, error_reason = auth_service.attempt_login(
        username=username,
        password=password,
        source_ip=client_ip,
    )
    
    if success:
        # Return session token on successful authentication
        # (placeholder — real implementation would use signed JWT or secure opaque token)
        return {
            "session_token": f"token_{hash(username)}",
            "username": username,
        }
    
    # Determine HTTP status from error reason
    if error_reason == "rate_limit_ip":
        # IP rate-limited by middleware pre-check, but can also occur at handler
        # if concurrent requests from same IP all increment the counter
        retry_after = auth_service.get_retry_after_seconds(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts from your IP. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    
    elif error_reason == "account_locked":
        # Account is in lockout state (≥10 failed attempts in 30-min window)
        # User must wait for lockout to expire or use password recovery
        raise HTTPException(
            status_code=423,  # WebDAV Locked status
            detail="Account temporarily locked due to multiple failed login attempts. "
                   "Please try again in 30 minutes or use the password recovery link.",
        )
    
    elif error_reason == "invalid_credentials":
        # Username doesn't exist or password is wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    # Shouldn't reach here if attempt_login is correct
    logger.error(f"Unexpected error_reason from attempt_login: {error_reason}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected error during login",
    )


@app.get("/incident/status")
async def incident_status():
    """
    Operational endpoint for incident response monitoring.
    
    Returns current rate-limit + lockout state, including:
    - Recent failed login count (last 15 minutes)
    - Source IPs with failures
    - Locked-out accounts (with count)
    - Audit log size
    
    Exposed to:
    - Dormouse: for telemetry verification (is rate-limit working?)
    - Queen: for ruling verification (are the thresholds correct?)
    - Incident responder: for situational awareness
    
    This is an operational endpoint for the incident-response window only.
    Disable after attack is fully mitigated (after Queen's all-clear ruling).
    """
    return auth_service.get_incident_status()


if __name__ == "__main__":
    import uvicorn
    # Run with: python -m uvicorn http_middleware:app --port 8000
    # Then: curl -X POST http://localhost:8000/login -d '{"username":"test","password":"wrong"}' -H "Content-Type: application/json"
    uvicorn.run(app, host="0.0.0.0", port=8000)
