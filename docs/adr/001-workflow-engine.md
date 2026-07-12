# ADR 001: Workflow Engine Design

## Status

Accepted

## Context

WebCMS needed a content approval workflow to support editorial teams with multiple reviewers and scheduled publishing.

## Decision

We implemented a state-machine based workflow engine with explicit transitions, reviewer assignment, and notification hooks.

## Consequences

- Positive: Clear state transitions, audit history, role-based permissions
- Positive: Easy to extend with new states and transitions
- Negative: Requires careful validation of transition permissions
