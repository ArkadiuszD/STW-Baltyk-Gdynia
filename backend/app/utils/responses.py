"""
Standardized API response helpers.

Usage:
    from app.utils.responses import success, error, paginated, created

    @app.route('/items')
    def get_items():
        items = Item.query.all()
        return success(items_schema.dump(items))

    @app.route('/items', methods=['POST'])
    def create_item():
        item = Item.create(**data)
        return created(item_schema.dump(item))
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import jsonify
from marshmallow import Schema


def success(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> Tuple[Any, int]:
    """
    Return successful response.

    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default 200)

    Returns:
        Tuple of (response, status_code)
    """
    if data is None and message:
        return jsonify({'message': message}), status_code
    return jsonify(data), status_code


def created(
    data: Any,
    message: Optional[str] = None
) -> Tuple[Any, int]:
    """
    Return 201 Created response.

    Args:
        data: Created resource data
        message: Optional success message
    """
    if message:
        response = {'data': data, 'message': message}
        return jsonify(response), 201
    return jsonify(data), 201


def error(
    message: str,
    code: Optional[str] = None,
    status_code: int = 400,
    errors: Optional[Dict[str, List[str]]] = None
) -> Tuple[Any, int]:
    """
    Return error response.

    Args:
        message: Error message
        code: Error code (for programmatic handling)
        status_code: HTTP status code (default 400)
        errors: Field-level validation errors

    Returns:
        Tuple of (response, status_code)
    """
    response = {'error': message}

    if code:
        response['code'] = code

    if errors:
        response['errors'] = errors

    return jsonify(response), status_code


def validation_error(errors: Dict[str, List[str]]) -> Tuple[Any, int]:
    """
    Return validation error response.

    Args:
        errors: Dictionary of field -> error messages
    """
    return error(
        message='Błąd walidacji danych',
        code='validation_error',
        status_code=400,
        errors=errors
    )


def not_found(message: str = 'Nie znaleziono zasobu') -> Tuple[Any, int]:
    """Return 404 Not Found response."""
    return error(message, code='not_found', status_code=404)


def forbidden(message: str = 'Brak uprawnień') -> Tuple[Any, int]:
    """Return 403 Forbidden response."""
    return error(message, code='forbidden', status_code=403)


def conflict(message: str) -> Tuple[Any, int]:
    """Return 409 Conflict response (e.g., duplicate entry)."""
    return error(message, code='conflict', status_code=409)


def paginated(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    schema: Optional[Schema] = None
) -> Tuple[Any, int]:
    """
    Return paginated response.

    Args:
        items: List of items (already serialized or to be serialized)
        total: Total count of all items
        page: Current page number
        per_page: Items per page
        schema: Optional schema to serialize items

    Returns:
        Tuple of (response, status_code)
    """
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    if schema:
        items = schema.dump(items, many=True) if hasattr(schema, 'dump') else items

    response = {
        'items': items,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page
    }

    return jsonify(response), 200


def no_content() -> Tuple[str, int]:
    """Return 204 No Content response."""
    return '', 204
