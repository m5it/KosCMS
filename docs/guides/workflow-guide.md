# WebCMS Workflow Guide

## Overview

WebCMS provides a flexible content approval workflow with states, reviewers, and scheduled publishing.

## States

- **draft**: Initial content state
- **review**: Content under review
- **approved**: Content approved for publishing
- **published**: Live content

## Using the Workflow

### Starting a Workflow

```bash
curl -X POST /api/v1/post/post-1/workflow \
  -H "Content-Type: application/json" \
  -d '{"user_id": "author1", "username": "Author"}'
```

### Assigning Reviewers

```bash
curl -X POST /api/v1/workflow-instances/{id}/reviewers \
  -H "Content-Type: application/json" \
  -d '{"reviewer_ids": ["reviewer1", "reviewer2"]}'
```

### Transitioning States

```bash
curl -X POST /api/v1/workflow-instances/{id}/transition \
  -H "Content-Type: application/json" \
  -d '{"to_state": "approved", "user_id": "reviewer1"}'
```

### Scheduling Publish

```bash
curl -X POST /api/v1/workflow-instances/{id}/schedule \
  -H "Content-Type: application/json" \
  -d '{"publish_time": "2026-08-01T09:00:00"}'
```

## Permissions

- Authors can submit to review
- Reviewers can approve or reject
- Editors can publish approved content
