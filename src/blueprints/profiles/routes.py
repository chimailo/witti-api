from sqlalchemy import exc
from flask import jsonify, request, Blueprint
from marshmallow import ValidationError

from src import db
from src.lib.auth import authenticate
from src.blueprints.errors import error_response, \
    bad_request, server_error, not_found
from src.blueprints.users.schema import UserSchema
from src.blueprints.profiles.models import Profile
from src.blueprints.profiles.schema import ProfileSchema


profile = Blueprint('profile', __name__, url_prefix='/api/profile')


@profile.route('/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    user = Profile.find_by_username(data.get('username'))

    if user is not None:
        if user.id != id:
            return {'res': False}

    return {'res': True}


@profile.route('/<username>', methods=['GET'])
@authenticate
def get_profile(user, username):
    a_user = Profile.find_by_username(username).user

    if a_user:
        profile = UserSchema(
            only=('id', 'profile', 'followers', 'following',)).dump(a_user)
        if user.profile.username != username:
            profile['isFollowing'] = user.is_following(a_user)
        return jsonify(profile)

    return not_found('User not found.')


@profile.route('', methods=['PUT'])
@authenticate
def update_profile(user):
    request_data = request.get_json()
    print(request_data)

    if not request_data:
        return bad_request("No input data provided")

    try:
        data = ProfileSchema().load(request_data)
    except ValidationError as error:
        return error_response(422, error.messages)

    profile = user.profile
    profile.username = data.get('username')
    profile.name = data.get('name')
    profile.dob = data.get('dob')
    profile.bio = data.get('bio')

    try:
        profile.save()
    except (exc.IntegrityError, ValueError):
        db.session.rollback()
        return server_error('Something went wrong, please try again.')
    else:
        return jsonify(ProfileSchema().dump(profile))


@profile.route('', methods=['DELETE'])
@authenticate
def delete_profile(user):
    try:
        user.delete()
    except Exception:
        return server_error('Something went wrong, please try again.')
    else:
        return {'message': 'Successfully deleted profile.'}
