from functools import wraps

from flask import request

from src.blueprints.errors import error_response
from src.blueprints.users.models import User


def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return error_response(403, message='No authorization.')

        token = auth_header.split(" ")[1]
        payload = User.decode_auth_token(token)

        if not isinstance(payload, dict):
            return error_response(401, message=payload)

        user = User.find_by_id(payload.get('id'))

        if user is None:
            return error_response(401, message='Invalid token.')

        return func(user, *args, **kwargs)
    return wrapper
