"""
Authentication Tests
"""

import pytest
from webcms.auth.password import PasswordHasher
from webcms.auth.jwt_handler import JWTHandler
from webcms.auth.rbac import RBACManager, Permission


def test_password_hashing():
    """Test password hashing."""
    hasher = PasswordHasher()
    
    # Hash password
    hashed = hasher.hash_password("SecurePass123!")
    assert hashed != "SecurePass123!"
    assert hashed.startswith("$2")
    
    # Verify correct password
    assert hasher.verify_password("SecurePass123!", hashed) is True
    
    # Verify wrong password
    assert hasher.verify_password("WrongPass", hashed) is False


def test_password_validation():
    """Test password strength validation."""
    hasher = PasswordHasher()
    
    # Too short
    with pytest.raises(ValueError):
        hasher.hash_password("short")
    
    # No uppercase
    with pytest.raises(ValueError):
        hasher.hash_password("lowercase123!")
    
    # No special char
    with pytest.raises(ValueError):
        hasher.hash_password("NoSpecial123")


def test_jwt_tokens():
    """Test JWT creation and verification."""
    handler = JWTHandler("test-secret")
    
    # Create tokens
    access, refresh = handler.create_tokens("user123", {"role": "admin"})
    assert access
    assert refresh
    
    # Verify access token
    payload = handler.verify_token(access, "access")
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"
    
    # Verify wrong type
    assert handler.verify_token(access, "refresh") is None
    
    # Refresh token
    new_access = handler.refresh_access_token(refresh)
    assert new_access


def test_rbac():
    """Test role-based access control."""
    rbac = RBACManager()
    
    # Check default roles exist
    assert rbac.get_role("admin") is not None
    assert rbac.get_role("editor") is not None
    assert rbac.get_role("author") is not None
    
    # Admin has all permissions
    admin = rbac.get_role("admin")
    assert admin.has_permission(Permission.MANAGE_USERS)
    assert admin.has_permission(Permission.CREATE_POST)
    
    # Editor permissions
    editor = rbac.get_role("editor")
    assert editor.has_permission(Permission.EDIT_POST)
    assert not editor.has_permission(Permission.MANAGE_USERS)
    
    # Check user permissions
    user_roles = ["editor", "author"]
    assert rbac.check_permission(user_roles, Permission.EDIT_POST)
    assert not rbac.check_permission(user_roles, Permission.MANAGE_USERS)