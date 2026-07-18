"""
Request Validators for Admin API

Provides comprehensive input validation for all API endpoints
"""

import re
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ValidationError(Exception):
    """Validation error with details."""
    
    def __init__(self, field: str, message: str, code: str = 'invalid'):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class Validator:
    """Base validator class."""
    
    def __init__(self, required: bool = True, allow_none: bool = False):
        self.required = required
        self.allow_none = allow_none
    
    def validate(self, value: Any, field_name: str = 'field') -> Any:
        """Validate and return cleaned value."""
        if value is None:
            if self.allow_none:
                return None
            if self.required:
                raise ValidationError(field_name, 'This field is required', 'required')
            return None
        
        return self._validate_value(value, field_name)
    
    def _validate_value(self, value: Any, field_name: str) -> Any:
        """Override in subclasses."""
        return value


class StringValidator(Validator):
    """String field validator."""
    
    def __init__(self, required: bool = True, allow_none: bool = False,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None,
                 pattern: Optional[str] = None,
                 trim: bool = True):
        super().__init__(required, allow_none)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.trim = trim
    
    def _validate_value(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(field_name, 'Must be a string', 'type_error')
        
        if self.trim:
            value = value.strip()
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                field_name,
                f'Must be at least {self.min_length} characters',
                'min_length'
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                field_name,
                f'Must be at most {self.max_length} characters',
                'max_length'
            )
        
        if self.pattern and not self.pattern.match(value):
            raise ValidationError(
                field_name,
                'Invalid format',
                'pattern'
            )
        
        return value


class EmailValidator(StringValidator):
    """Email field validator."""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    def __init__(self, required: bool = True, allow_none: bool = False):
        super().__init__(
            required=required,
            allow_none=allow_none,
            pattern=self.EMAIL_PATTERN,
            min_length=5,
            max_length=254
        )


class IntegerValidator(Validator):
    """Integer field validator."""
    
    def __init__(self, required: bool = True, allow_none: bool = False,
                 min_value: Optional[int] = None,
                 max_value: Optional[int] = None):
        super().__init__(required, allow_none)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_value(self, value: Any, field_name: str) -> int:
        try:
            if isinstance(value, str):
                value = int(value.strip())
            else:
                value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, 'Must be a valid integer', 'type_error')
        
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                field_name,
                f'Must be at least {self.min_value}',
                'min_value'
            )
        
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                field_name,
                f'Must be at most {self.max_value}',
                'max_value'
            )
        
        return value


class BooleanValidator(Validator):
    """Boolean field validator."""
    
    TRUE_VALUES = {'true', '1', 'yes', 'on', 'True', 'TRUE'}
    FALSE_VALUES = {'false', '0', 'no', 'off', 'False', 'FALSE'}
    
    def _validate_value(self, value: Any, field_name: str) -> bool:
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value in self.TRUE_VALUES:
                return True
            if value in self.FALSE_VALUES:
                return False
        
        raise ValidationError(field_name, 'Must be a boolean value', 'type_error')


class ListValidator(Validator):
    """List field validator."""
    
    def __init__(self, required: bool = True, allow_none: bool = False,
                 item_validator: Optional[Validator] = None,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None):
        super().__init__(required, allow_none)
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
    
    def _validate_value(self, value: Any, field_name: str) -> List:
        if not isinstance(value, list):
            raise ValidationError(field_name, 'Must be a list', 'type_error')
        
        if self.min_length is not None and len(value) < self.min_length:
            raise ValidationError(
                field_name,
                f'Must have at least {self.min_length} items',
                'min_length'
            )
        
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                field_name,
                f'Must have at most {self.max_length} items',
                'max_length'
            )
        
        if self.item_validator:
            validated = []
            for i, item in enumerate(value):
                try:
                    validated.append(self.item_validator.validate(item, f'{field_name}[{i}]'))
                except ValidationError as e:
                    raise ValidationError(
                        field_name,
                        f'Invalid item at index {i}: {e.message}',
                        e.code
                    )
            return validated
        
        return value


class DictValidator(Validator):
    """Dictionary/object validator."""
    
    def __init__(self, required: bool = True, allow_none: bool = False,
                 schema: Optional[Dict[str, Validator]] = None):
        super().__init__(required, allow_none)
        self.schema = schema or {}
    
    def _validate_value(self, value: Any, field_name: str) -> Dict:
        if not isinstance(value, dict):
            raise ValidationError(field_name, 'Must be an object', 'type_error')
        
        if not self.schema:
            return value
        
        validated = {}
        errors = []
        
        # Validate provided fields
        for key, val in value.items():
            if key in self.schema:
                try:
                    validated[key] = self.schema[key].validate(val, key)
                except ValidationError as e:
                    errors.append({'field': e.field, 'message': e.message, 'code': e.code})
            else:
                # Extra fields are allowed but not validated
                validated[key] = val
        
        # Check required fields
        for key, validator in self.schema.items():
            if validator.required and key not in value:
                errors.append({'field': key, 'message': 'This field is required', 'code': 'required'})
        
        if errors:
            raise MultipleValidationError(errors)
        
        return validated


class MultipleValidationError(Exception):
    """Multiple validation errors."""
    
    def __init__(self, errors: List[Dict]):
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} errors")


# Predefined validators
class Validators:
    """Common validators."""
    
    @staticmethod
    def slug(min_length: int = 1, max_length: int = 100) -> StringValidator:
        """Slug validator (URL-friendly string)."""
        return StringValidator(
            pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
            min_length=min_length,
            max_length=max_length
        )
    
    @staticmethod
    def password(min_length: int = 8) -> StringValidator:
        """Password validator."""
        return StringValidator(
            min_length=min_length,
            max_length=128
        )
    
    @staticmethod
    def username(min_length: int = 3, max_length: int = 30) -> StringValidator:
        """Username validator."""
        return StringValidator(
            pattern=r'^[a-zA-Z0-9_-]+$',
            min_length=min_length,
            max_length=max_length
        )
    
    @staticmethod
    def uuid() -> StringValidator:
        """UUID validator."""
        return StringValidator(
            pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            min_length=36,
            max_length=36
        )


def validate_request(schema: Dict[str, Validator], data: Dict) -> Dict:
    """
    Validate request data against schema.
    
    Args:
        schema: Dictionary of field names to validators
        data: Request data to validate
    
    Returns:
        Validated and cleaned data
    
    Raises:
        MultipleValidationError: If validation fails
    """
    validator = DictValidator(required=True, schema=schema)
    return validator.validate(data)


def validate_or_error(schema: Dict[str, Validator], data: Dict) -> tuple:
    """
    Validate request data and return result or errors.
    
    Returns:
        Tuple of (success: bool, result: Any or errors: list)
    """
    try:
        result = validate_request(schema, data)
        return True, result
    except MultipleValidationError as e:
        return False, e.errors
    except ValidationError as e:
        return False, [{'field': e.field, 'message': e.message, 'code': e.code}]


# Export
__all__ = [
    'ValidationError',
    'MultipleValidationError',
    'Validator',
    'StringValidator',
    'EmailValidator',
    'IntegerValidator',
    'BooleanValidator',
    'ListValidator',
    'DictValidator',
    'Validators',
    'validate_request',
    'validate_or_error'
]
