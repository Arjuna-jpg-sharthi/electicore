"""Authentication and role authorization helpers."""

from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Student, db
from .errors import error


def current_user():
    return db.session.get(Student, int(get_jwt_identity()))


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @jwt_required()
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or user.role not in roles:
                return error("You do not have permission for this action", 403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
