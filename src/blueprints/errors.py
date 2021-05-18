from flask import jsonify, Blueprint
from werkzeug.http import HTTP_STATUS_CODES

from src import db

errors = Blueprint('errors', __name__)


def error_response(status_code, message=None):
    payload = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    }
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message):
    return error_response(400, message)


def not_found(message):
    return error_response(404, message)


def server_error(message):
    return error_response(500, message)


@errors.app_errorhandler(404)
def not_found_error(error):
    return not_found('Not found.')


@errors.app_errorhandler(405)
def not_allowed_error(error):
    return error_response(405, 'Method not allowed')


@errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return error_response(500, 'Internal error')
