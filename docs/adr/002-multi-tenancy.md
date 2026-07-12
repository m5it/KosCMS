# ADR 002: Multi-Tenancy Architecture

## Status

Accepted

## Context

WebCMS needs to serve multiple isolated tenants from a single deployment.

## Decision

We use schema-based isolation with context variables for request-scoped tenant routing. Each tenant has its own theme, plugins, and quotas.

## Consequences

- Positive: Strong data isolation between tenants
- Positive: Flexible per-tenant customization
- Negative: Requires tenant context management on every request
