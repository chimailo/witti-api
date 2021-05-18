from flask import Blueprint, request

from src import db
from src.lib.auth import authenticate
from src.lib.search import TagsIndex, UsersIndex
from src.blueprints.errors import server_error
from src.blueprints.users.models import User
from src.blueprints.tags.models import Tag
from src.blueprints.users.schema import UserSchema


search = Blueprint('search', __name__, url_prefix='/api/search')


@search.route('/ping', methods=['GET'])
def ping():
    return {'message': 'Search Route!'}


@search.route('', methods=['GET'])
@authenticate
def mainSearch(user):
    q = request.args.get('q', str, None)

    try:
        if q is None:
            return {[]}

        tags = Tag.search(TagsIndex, q)
        users = User.search(UsersIndex, q)
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('An unexpected error occured, please try again.')
    return {
        'results': {
            'tags': [tag.to_dict(user) for tag in tags],
            'users': UserSchema(
                many=True,
                only=(
                    'id', 'profile.username', 'profile.name', 'profile.avatar')
            ).dump(users),
        }
    }


@search.route('/users', methods=['GET'])
@authenticate
def msg_Search(user):
    q = request.args.get('q', str, None)

    try:
        if q is None:
            return {[]}

        users = User.search(UsersIndex, q)
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('An unexpected error occured, please try again.')
    return {
        'users': UserSchema(
            many=True,
            only=('id', 'auth.username', 'profile.name', 'profile.avatar')
        ).dump(users),
    }
