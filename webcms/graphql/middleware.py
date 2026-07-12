"""
GraphQL middleware for permissions and complexity limiting.
"""

import graphene


class PermissionMiddleware:
    """Field-level permission middleware."""

    def resolve(self, next, root, info, **args):
        field_name = info.field_name
        user = getattr(info.context, "user", None) if info.context else None

        # Admin-only fields
        admin_fields = {"users", "user", "workflows", "versions"}
        if field_name in admin_fields:
            if not user or not getattr(user, "is_admin", False):
                return None

        # Protected mutations
        if info.operation.operation == "mutation":
            if not user or not getattr(user, "can_edit", False):
                raise Exception("Permission denied: editor role required")

        return next(root, info, **args)


class ComplexityMiddleware:
    """Query complexity limiting middleware."""

    DEFAULT_MAX_COMPLEXITY = 1000

    def __init__(self, max_complexity=None):
        self.max_complexity = max_complexity or self.DEFAULT_MAX_COMPLEXITY

    def resolve(self, next, root, info, **args):
        complexity = self._calculate_complexity(info.operation)
        if complexity > self.max_complexity:
            raise Exception(f"Query complexity {complexity} exceeds maximum {self.max_complexity}")
        return next(root, info, **args)

    def _calculate_complexity(self, operation, depth=0):
        if not operation:
            return 0

        # Simple complexity estimation
        base_cost = 1
        multiplier = depth + 1

        selection_set = getattr(operation, "selection_set", None)
        if not selection_set:
            return base_cost * multiplier

        total = 0
        selections = getattr(selection_set, "selections", [])
        for selection in selections:
            total += base_cost * multiplier
            nested = self._calculate_complexity(selection, depth + 1)
            total += nested

        return total
