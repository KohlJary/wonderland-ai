## Ruling 006: Message translation must not leak original content in logs or error states

**Severity:** high
**Domain:** data-handling
**Source:** Cat's hub-model ADR + Queen's implicit data-handling assumption

**Citation:**

GDPR Article 32 (security of processing) requires appropriate technical measures to protect personal data. CWE-532 'Insertion of Sensitive Information into Log File' — user messages are personal data; if they appear in debug logs, error traces, or third-party translation service logs, they have leaked beyond the intended recipient.

**Finding:**

The hub-model ADR specifies that translation happens server-side via a third-party service (or self-hosted). Either way, the original message must be sent to the translation engine. If that message is logged by the translation service (common for debugging and model improvement), or if your system logs the request/response for debugging, the message has leaked. This is especially acute if the translation service is a third party — you do not control their logging. The team has not yet specified: (1) does the translation service store messages? (2) if yes, for how long? (3) what does your contract with them say about data deletion? (4) does your system log translation requests before sending them externally?

**Required Remediation:**

(1) If using a third-party translation service: the data processor agreement (DPA) must explicitly forbid the service from storing, logging, or using messages for any purpose other than real-time translation. Demand confirmation in writing; do not assume 'standard' terms are acceptable. (2) If using a self-hosted model: configure logging to exclude message content from request/response logs; use structured logging (log 'translation_request_size: 42 bytes' not 'translation_request_content: [actual text]'). (3) Your system must not log the original message before sending it to translation; log only the operation ('message_translated', 'translation_time_ms') not the content. (4) Error messages must not echo message content; log only the error type and the message ID. (5) The Tweedles must implement a message-scrubbing pre-flight on all log outputs to ensure no message text escapes.

**Acceptance Criteria:**
- Third-party translation service contract includes explicit data-handling terms (no storage beyond real-time processing, no logging, no reuse)
- Self-hosted setup: logging configuration does not include message content in request/response logs
- System logs translation operations by type and size, not by content
- Error handlers do not echo message content in error output
- Caterpillar review confirms message content does not appear in any logs or error paths
- Dormouse post-launch observation confirms actual logs match the configuration (compliance is verified in production, not just in code review)

**Residual Risk:**

Third-party translation services (e.g., Google Translate API, DeepL) have publicly documented privacy policies, but those policies often permit logging and model training on data passed to them, unless you have a Business Associate Agreement (BAA) or equivalent. The residual risk is that you cannot unilaterally prevent the service from logging; you can only contractually forbid it and accept that the service may violate the contract. If you choose a third party, use one with a published commitment to not logging personal data (e.g., DeepL's 'data privacy' tier); do not use generic endpoints. If you use a self-hosted model, the risk transfers to your infrastructure: logging misconfiguration or third-party libraries logging message content. Both residual risks are acceptable if documented and monitored (Dormouse observation).

**Compliance Implications:**

GDPR Article 28 (processor agreements with third parties): if using a third-party service, you must have a written contract that specifies how the processor handles personal data. GDPR Article 32 (security of processing): your system must have technical measures to prevent unauthorized access to messages. Logging unencrypted message content is an unauthorized-access risk.

**Audit Reference:**

Message Data-Handling Strategy (MDS-001): recording the translation-service choice, the DPA terms, the logging configuration, and the message-scrubbing enforcement.
