"""
Password hashing utilities using passlib + bcrypt.

Per Queen's ruling (contract-note-01KV9PGN): cost=12 minimum,
constant-time comparison, no password logging/echoing.
"""
from passlib.context import CryptContext

# CryptContext with bcrypt, cost 12 (Queen's requirement for security)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt cost 12.
    
    **Invariants enforced:**
    - Every call produces a unique hash (salt is random)
    - Hash collision resistance: infeasible to find two passwords that hash to the same value
    - Hash includes cost and salt embedded (format: $2b$12$...)
    
    **Failure mode:** if passlib is misconfigured, raises ValueError
    
    Args:
        plain_password: plaintext password to hash
        
    Returns:
        bcrypt hash string (includes cost and salt)
        
    Raises:
        ValueError: if hashing fails (shouldn't happen in normal operation)
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    
    **Invariants enforced:**
    - Returns True if and only if the plaintext matches the hash
    - Uses constant-time comparison (timing attack resistant)
    - Rejects wrong passwords with False, never raises
    
    **Failure mode:** wrong password returns False, never raises
    
    Args:
        plain_password: plaintext password to verify
        password_hash: bcrypt hash to verify against
        
    Returns:
        True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, password_hash)
