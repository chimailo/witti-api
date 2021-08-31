import base64
import json
import requests
from functools import wraps
from authlib.jose import jwt, errors
from flask import request

from src.blueprints.errors import error_response
from src.blueprints.users.models import User


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth_header = request.headers.get('Authorization', None)

    if not auth_header:
        return error_response(403, message='Authorization header is expected.')

    parts = auth_header.split()

    if parts[0].lower() != "bearer":
        return error_response(
            401, "Authorization header must start with 'Bearer'")
    elif len(parts) == 1:
        return error_response(401, "Token not found")
    elif len(parts) > 2:
        return error_response(
            401, "Authorization header must be 'Bearer token'")

    return parts[1]


def authenticate(func):
    """Determines if the Access Token is valid
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = get_token_auth_header()

        try:
            res = requests.get(
                'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com'
            ).json();
        except requests.exceptions.ConnectionError:
            return error_response(401, 'Network error')

        header64 = token.split('.')[0].encode('ascii')
        header = json.loads(bytes.decode(base64.b64decode(header64 + b'=='), 'ascii'))

        try:
            payload = jwt.decode(token, res[header['kid']])
        except errors.ExpiredTokenError:
            return error_response(401, 'Signature expired. Please log in again.')
        except Exception:
            return error_response(401, 'Invalid token. Please log in again.')

        if payload['iss'] != 'https://securetoken.google.com/witting' or \
            payload['aud'] != 'witting' or \
            payload['sub'] != payload['user_id']:
            return error_response(401, message='Invalid token.')

        user = User.find_by_id(payload.get('sub'))

        if user is None:
            return error_response(401, message='Invalid token.')

        return func(user, *args, **kwargs)
    return wrapper

        # payload = User.decode_auth_token(token)

        # if not isinstance(payload, dict):
        #     return error_response(401, message=payload)

        # user = User.find_by_id(payload.get('sub'))

        # if user is None:
        #     return error_response(401, message='Invalid token.')
