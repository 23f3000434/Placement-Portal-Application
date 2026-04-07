from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_required(*roles):
    """
    Decorator that checks if the logged-in user has one of the allowed roles.
    Usage: @role_required("admin") or @role_required("admin", "company")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "Access denied. Insufficient permissions."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
