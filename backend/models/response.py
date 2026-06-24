"""
models/response.py
Standardised API response helpers.
Every endpoint should use these for consistent JSON shape.
"""

from flask import jsonify
from typing import Any


def success(data: Any = None, message: str = "Success", status_code: int = 200):
    """Return a successful JSON response."""
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def created(data: Any = None, message: str = "Created"):
    """Return a 201 Created response."""
    return success(data=data, message=message, status_code=201)


def error(message: str, status_code: int = 400, details: Any = None):
    """Return an error JSON response."""
    payload = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def not_found(resource: str = "Resource"):
    """Return a 404 Not Found response."""
    return error(f"{resource} not found", status_code=404)


def forbidden(message: str = "Insufficient permissions"):
    """Return a 403 Forbidden response."""
    return error(message, status_code=403)


def server_error(message: str = "Internal server error"):
    """Return a 500 Internal Server Error response."""
    return error(message, status_code=500)


def paginated(
    items: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
):
    """Return a paginated list response."""
    payload = {
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": -(-total // per_page),  # ceiling division
            "has_next": page * per_page < total,
            "has_prev": page > 1,
        },
    }
    return jsonify(payload), 200
