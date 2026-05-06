# ADR-001: Translation state ownership: frontend-cached or backend-owned

## Context

The WebSocket event carrying translation state changes needs to carry enough information for Tweedledee to update her UI state machine correctly. The contract shape depends on a deeper architectural decision: is the frontend's in-memory cache the system's oracle for translation state, or is the backend's persisted state the oracle and the frontend is eventual-consistent? These two models are incompatible—they have different failure modes, different consistency guarantees, and different operational costs.

## Decision

Before Tweedledum and Tweedledee negotiate the Contract Note, they must decide: **does Architecture A (frontend-owned cache, backend stateless) or Architecture B (backend-owned state, frontend eventual-consistent) own this thread?** The decision depends on the user-facing consistency requirement: if real-time accurate translations are non-negotiable even under failure, pick A. If eventual consistency is acceptable (user sees a stale translation briefly, or sees a retry UI), pick B.

## Tradeoffs

- Architecture A: Lower latency, fewer round-trips, faster retry. Cost: frontend cache is the oracle; silent corruption if frontend and backend diverge. WebSocket event shape is locked in; coupling permanent.
- Architecture B: Single source of truth; backend persistence guarantees consistency. Cost: higher latency (re-requests required), more server load, server-side retry logic complexity. Eventual consistency acceptable; user may see stale state briefly.
- Cannot have both low latency and strong consistency. Decide on the consistency model you need, then the contract seams resolve.

## Status

Proposed
