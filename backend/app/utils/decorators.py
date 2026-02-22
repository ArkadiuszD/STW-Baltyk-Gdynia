"""
Custom decorators for Flask routes.

Usage:
    from app.utils.decorators import admin_required, write_permission_required

    @app.route('/admin-only')
    @jwt_required()
    @admin_required
    def admin_endpoint():
        pass

    @app.route('/create-something')
    @jwt_required()
    @write_permission_required
    def create_endpoint():
        pass
"""
from functools import wraps
from typing import Callable, List, Optional

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*allowed_roles: str):
    """
    Decorator that checks if user has one of the allowed roles.

    Args:
        *allowed_roles: Role names that are allowed access

    Usage:
        @role_required('admin', 'treasurer')
        def my_view():
            pass
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Brak uprawnień do wykonania tej operacji',
                    'code': 'forbidden'
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn: Callable) -> Callable:
    """
    Decorator that requires admin role.

    Usage:
        @admin_required
        def admin_only_view():
            pass
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({
                'error': 'Wymagane uprawnienia administratora',
                'code': 'admin_required'
            }), 403

        return fn(*args, **kwargs)
    return wrapper


def write_permission_required(fn: Callable) -> Callable:
    """
    Decorator that requires write permissions (admin or treasurer).

    Usage:
        @write_permission_required
        def create_or_update_view():
            pass
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        role = claims.get('role')

        if role not in ['admin', 'treasurer']:
            return jsonify({
                'error': 'Brak uprawnień do modyfikacji danych',
                'code': 'write_permission_required'
            }), 403

        return fn(*args, **kwargs)
    return wrapper


def get_current_user_role() -> Optional[str]:
    """Get current user's role from JWT claims."""
    try:
        claims = get_jwt()
        return claims.get('role')
    except Exception:
        return None


def get_current_user_id() -> Optional[int]:
    """Get current user's ID from JWT identity."""
    try:
        from flask_jwt_extended import get_jwt_identity
        identity = get_jwt_identity()
        return int(identity) if identity else None
    except Exception:
        return None


def has_role(*roles: str) -> bool:
    """Check if current user has any of the specified roles."""
    current_role = get_current_user_role()
    return current_role in roles


def is_admin() -> bool:
    """Check if current user is admin."""
    return has_role('admin')


def can_write() -> bool:
    """Check if current user has write permissions."""
    return has_role('admin', 'treasurer')
