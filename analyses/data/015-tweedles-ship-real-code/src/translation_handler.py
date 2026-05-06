"""
Translation request handler.

Implements the contract from third-party-translation-service-with-synchronous-on-read-model ADR:
- Synchronous on-read model with 2-second SLA
- Translation Status Signal Shape v1: {pending, translated, failed, timeout}
- Translation SLA Fallback Behavior v1: failure_reason enum {timeout, service_error, network_error}
- WebSocket Statefulness v1: stateless requests, each includes message_id, source_lang, target_lang
"""

import asyncio
from typing import TypedDict, Literal
from enum import Enum


class TranslationStatus(str, Enum):
    """Translation Status Signal Shape v1."""
    PENDING = "pending"
    TRANSLATED = "translated"
    FAILED = "failed"
    TIMEOUT = "timeout"


class FailureReason(str, Enum):
    """Translation SLA Fallback Behavior v1: failure reasons."""
    TIMEOUT = "timeout"
    SERVICE_ERROR = "service_error"
    NETWORK_ERROR = "network_error"


class TranslationResponse(TypedDict, total=False):
    """Response envelope matching Translation Status Signal Shape v1."""
    message_id: str
    status: TranslationStatus
    translated_text: str | None
    failure_reason: FailureReason | None


class TranslationRequestError(Exception):
    """Base exception for translation request failures."""
    pass


class TranslationTimeoutError(TranslationRequestError):
    """Raised when translation request exceeds 2-second SLA."""
    pass


class TranslationServiceError(TranslationRequestError):
    """Raised when translator service returns error."""
    pass


class TranslationNetworkError(TranslationRequestError):
    """Raised when network communication with translator fails."""
    pass


async def _stub_translator(
    message_id: str, 
    source_lang: str, 
    target_lang: str
) -> str:
    """
    Stub translator call. Returns translated text after notional 50ms delay.
    
    This is a placeholder for the actual third-party translator integration.
    In production, this would call the real translation service.
    
    Invariant: every call either returns translated_text or raises an exception.
    """
    # Notional 50ms delay to simulate network call
    await asyncio.sleep(0.05)
    
    # Stub response: echo source language and target language info
    return f"[{target_lang} translation of message {message_id}]"


async def handle_translation_request(
    message_id: str,
    source_lang: str,
    target_lang: str,
    sla_seconds: float = 2.0,
) -> TranslationResponse:
    """
    Handle a translation request for a single message.
    
    Implements:
    - Translation Status Signal Shape v1 (status enum, translated_text field)
    - Translation SLA Fallback Behavior v1 (2-second timeout, failure_reason enum)
    - WebSocket Statefulness v1 (stateless: all context in request parameters)
    
    Args:
        message_id: Unique identifier for the message being translated.
                   Persisted server-side; used for cache coherence at the seam.
        source_lang: ISO 639-1 code (e.g., "en"). Drives translator selection.
        target_lang: ISO 639-1 code (e.g., "de"). Drives translator selection.
        sla_seconds: SLA timeout in seconds. Default 2.0 per the ADR.
    
    Returns:
        TranslationResponse dict with status + translated_text (on success)
        or status + failure_reason (on failure).
    
    Invariants enforced:
    - Every call returns a response dict with message_id and status.
    - status is one of {pending, translated, failed, timeout}.
    - If status == "translated", translated_text is non-null string.
    - If status == "failed" or "timeout", failure_reason is set.
    - translated_text and failure_reason are mutually exclusive.
    
    Failure modes handled:
    - Timeout: translator takes >2s → returns status=timeout, failure_reason=timeout.
    - Service error: translator service error → returns status=failed, failure_reason=service_error.
    - Network error: translator network failure → returns status=failed, failure_reason=network_error.
    """
    
    try:
        # Wrap the stub translator call in a timeout.
        # This enforces the 2-second SLA from Translation SLA Fallback Behavior v1.
        translated_text = await asyncio.wait_for(
            _stub_translator(message_id, source_lang, target_lang),
            timeout=sla_seconds,
        )
        
        # Success path: return status=translated with the translated text.
        response: TranslationResponse = {
            "message_id": message_id,
            "status": TranslationStatus.TRANSLATED,
            "translated_text": translated_text,
        }
        return response
    
    except asyncio.TimeoutError:
        # SLA timeout: translator took >2 seconds.
        # Return status=timeout per Translation SLA Fallback Behavior v1.
        response: TranslationResponse = {
            "message_id": message_id,
            "status": TranslationStatus.TIMEOUT,
            "translated_text": None,
            "failure_reason": FailureReason.TIMEOUT,
        }
        return response
    
    except TranslationServiceError:
        # Translator service returned an error (non-network).
        # Return status=failed with failure_reason=service_error.
        response: TranslationResponse = {
            "message_id": message_id,
            "status": TranslationStatus.FAILED,
            "translated_text": None,
            "failure_reason": FailureReason.SERVICE_ERROR,
        }
        return response
    
    except TranslationNetworkError:
        # Network communication with translator failed.
        # Return status=failed with failure_reason=network_error.
        response: TranslationResponse = {
            "message_id": message_id,
            "status": TranslationStatus.FAILED,
            "translated_text": None,
            "failure_reason": FailureReason.NETWORK_ERROR,
        }
        return response
    
    except Exception as e:
        # Unexpected error: log and return service_error as safe default.
        # (In production, this would be instrumented with observability.)
        response: TranslationResponse = {
            "message_id": message_id,
            "status": TranslationStatus.FAILED,
            "translated_text": None,
            "failure_reason": FailureReason.SERVICE_ERROR,
        }
        return response
