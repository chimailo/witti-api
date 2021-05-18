from sqlalchemy import exc
from marshmallow import ValidationError
from flask import jsonify, request, url_for

from src import db
from src.lib.auth import authenticate
from src.blueprints.errors import error_response, bad_request, \
    server_error
from src.blueprints.users.models import User
from src.blueprints.users.schema import UserSchema, AuthSchema
from src.blueprints.profiles.models import Profile

from src.blueprints.users.routes import users


@users.route('/ping')
def ping():
    return {"message": "Users Route!"}


@users.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    user = User.find_by_email(data.get('email'))
    return {'res': not isinstance(user, User)}


@users.route('/register', methods=['POST'])
def register_user():
    post_data = request.get_json()

    if not post_data:
        return bad_request("No input data provided")

    try:
        data = AuthSchema(partial=True).load(post_data)
    except ValidationError as err:
        return error_response(422, err.messages)

    name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # check for existing user
    user = User.query.filter(User.email == email).first()

    if user:
        return bad_request('That user already exists.')

    profile = Profile()
    profile.name = name
    profile.username = username
    profile.avatar = profile.set_avatar(email)

    user = User(password=password)
    user.email = email
    user.profile = profile

    try:
        user.save()
    except (exc.IntegrityError, ValueError):
        db.session.rollback()
        return server_error('Something went wrong, please try again.')

    response = jsonify({'token': user.encode_auth_token()})
    response.status_code = 201
    response.headers['Location'] = url_for('users.get_user', id=user.id)
    return response


@users.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()

    if data is None:
        return bad_request("No input data provided")

    try:
        # check for existing user
        user = User.find_by_email(data.get('email'))

        if user and user.check_password(data.get('password')):
            return jsonify({'token': user.encode_auth_token()})
        else:
            return error_response(401, 'Incorrect email or password.')
    except Exception:
        return server_error('Something went wrong, please try again.')


@users.route('/logout', methods=['GET'])
@authenticate
def logout_user(user):
    return jsonify({'message': 'Successfully logged out.'})


@users.route('/auth', methods=['GET'])
@authenticate
def get_user(user):
    return jsonify(UserSchema(only=('id', 'profile',)).dump(user))
