from sqlalchemy import exc
from marshmallow import ValidationError
from flask import Blueprint, current_app, jsonify, request

from src import db
from src.lib import urlsafe_base64
from src.lib.auth import authenticate
from src.blueprints.errors import server_error, error_response, \
    bad_request, not_found
from src.blueprints.posts.models import Post
from src.blueprints.tags.models import Tag
from src.blueprints.tags.schema import TagSchema


tags = Blueprint('tags', __name__, url_prefix='/api/tags')


@tags.route('/ping', methods=['GET'])
def ping():
    return {'message': 'Users Route!'}


@tags.route('/check', methods=['POST'])
def check_tag():
    data = request.get_json()
    tag = Tag.query.filter_by(name=data.get('tag')).first()
    return {'res': not isinstance(tag, Tag)}


@tags.route('/all-tags', methods=['GET'])
@authenticate
def get_tags(user):
    try:
        tags = Tag.query.all()
    except Exception as e:
        print(e)
        return server_error('An unexpected error occured.')
    return jsonify(TagSchema(many=True, only=('id', 'name',)).dump(tags))


@tags.route('', methods=['POST'])
@authenticate
def add_tag(user):
    req_data = request.get_json()

    if not req_data:
        return bad_request('No request data provided')

    try:
        data = TagSchema().load(req_data)
    except ValidationError as err:
        print(err)
        return error_response(422, err.messages)

    name = data.get('name')
    # check for existing tag
    tag = Tag.query.filter(Tag.name == name).first()

    if tag:
        return bad_request(f'Tag with name "{name}" already exists.')

    tag = Tag(name=name)

    try:
        tag.save()
    except (exc.IntegrityError, ValueError):
        db.session.rollback()
        return server_error('Something went wrong, please try again.')
    return jsonify(TagSchema().dump(tag))


@tags.route('/to-follow', methods=['GET'])
@authenticate
def get_top_tags(user):
    """Get list of top tags not followed by user"""
    cursor = request.args.get('cursor')
    items_per_page = current_app.config['ITEMS_PER_PAGE']
    nextCursor = None
    tags = None

    try:
        ord_tags = Tag.get_top_tags(user).subquery()
        query = db.session.query(Tag, ord_tags.c.nPosts).join(
            ord_tags, Tag.id == ord_tags.c.tags_id).order_by(
                ord_tags.c.nPosts.desc())

        if cursor == '0':
            tags = query.limit(items_per_page + 1).all()
        else:
            cursor = urlsafe_base64(cursor, from_base64=True)
            tags = query.filter(
                ord_tags.c.nPosts < cursor).limit(items_per_page + 1).all()
    except (exc.IntegrityError, ValueError) as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')

    if len(tags) > items_per_page:
        nextCursor = urlsafe_base64(str(tags[items_per_page - 1][1]))

    return {
        'data': [tag[0].to_dict(user) for tag in tags[:items_per_page]],
        'nextCursor': nextCursor
    }


@tags.route('/<int:tag_id>/follow', methods=['POST'])
@authenticate
def follow_tag(user, tag_id):
    tag = Tag.query.filter_by(id=tag_id).first()

    if not tag:
        return bad_request(f'No tag with id "{tag_id}" exists')

    try:
        user.unfollow_tag(tag) \
            if user.is_following_tag(tag) else user.follow_tag(tag)
        user.save()
    except (exc.IntegrityError, ValueError):
        db.session.rollback()
        return server_error('Something went wrong, please try again.')
    return TagSchema().dump(tag)


@tags.route('', methods=['GET'])
@authenticate
def get_tag(user):
    tag_name = request.args.get('name')

    try:
        tag = Tag.query.filter_by(name=tag_name).first()
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('An unexpected error occured.')

    if tag:
        return tag.to_dict(user)
    return not_found(f'Tag with name "{tag_name}" does not exist.')


@tags.route('/<tag_name>', methods=['GET'])
@authenticate
def get_tag_posts(user, tag_name):
    top = request.args.get('top', default=False)
    latest = request.args.get('latest', default=False)
    cursor = request.args.get('cursor')
    items_per_page = current_app.config['ITEMS_PER_PAGE']
    nextCursor = None
    query = ''

    try:
        tag = Tag.query.filter_by(name=tag_name).first()
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('An unexpected error occured.')

    try:
        sorted_posts = Post.get_by_reactions().subquery()
        tag_posts = Post.query.with_parent(tag).subquery()
        sort_top_posts = db.session.query(
            tag_posts, sorted_posts.c.sequence).join(
                sorted_posts, sorted_posts.c.id == tag_posts.c.id).subquery()
        top_posts = db.session.query(Post, sort_top_posts.c.sequence).join(
            sort_top_posts, Post.id == sort_top_posts.c.id).order_by(
                sort_top_posts.c.sequence.desc())
        latest_posts = Post.query.with_parent(tag).order_by(
            Post.created_on.desc())
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('An unexpected error occured, please try again.')

    if cursor == '0' and latest:
        query = latest_posts.limit(items_per_page + 1).all()
    elif cursor == '0' and top:
        query = top_posts.limit(items_per_page + 1).all()
    else:
        if latest:
            cursor = urlsafe_base64(cursor, from_base64=True)
            query = latest_posts.filter(
                Post.created_on < cursor).limit(items_per_page + 1).all()
        else:
            cursor = urlsafe_base64(cursor, from_base64=True)
            query = top_posts.filter(sort_top_posts.c.sequence < cursor).limit(
                items_per_page + 1).all()

    if len(query) > items_per_page:
        nextCursor = urlsafe_base64(
            query[items_per_page - 1].created_on.isoformat()) \
                if latest else urlsafe_base64(
            str(query[items_per_page - 1][1]))

    posts = [post.to_dict(user) for post in query[:items_per_page]] \
        if latest else \
            [post[0].to_dict(user) for post in query[:items_per_page]]

    return {
        'data': posts,
        'nextCursor': nextCursor
    }
