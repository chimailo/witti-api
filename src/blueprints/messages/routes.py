from datetime import datetime
from sqlalchemy.exc import IntegrityError, ProgrammingError
from flask import json, jsonify, request, url_for, Blueprint, current_app
from src.blueprints.messages.schema import NotificationSchema
from src.blueprints.messages.models import Notification

from src import db
from src.lib import urlsafe_base64
from src.lib.auth import authenticate
from src.blueprints.errors import error_response, bad_request, \
     server_error, not_found
from src.blueprints.users.models import User
from src.blueprints.profiles.models import Profile
from src.blueprints.messages.models import Message, Chat, LastReadMessage
from src.blueprints.messages.schema import MessageSchema
from src.blueprints.users.schema import UserSchema

messages = Blueprint('messages', __name__, url_prefix='/api')


@messages.route('/messages/ping', methods=['GET'])
def ping():
    return {'message': 'Messages Route!'}


@messages.route('/chats', methods=['GET'])
@authenticate
def get_messages(user):
    cursor = request.args.get('cursor')
    items_per_page = current_app.config['ITEMS_PER_PAGE']
    last_messages = None
    nextCursor = None
    messages = []

    try:
        stmt, query = user.get_chat_last_messages()
        if cursor == '0':
            last_messages = query.limit(items_per_page + 1).all()
        else:
            cursor = urlsafe_base64(cursor, from_base64=True)
            last_messages = query.filter(
                stmt.c.last_messages < cursor).limit(items_per_page + 1).all()
    except (IntegrityError, ValueError) as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')

    if len(last_messages) > items_per_page:
        nextCursor = urlsafe_base64(
            last_messages[items_per_page - 1].last_messages.isoformat())

    for msg, user1, user2, _ in last_messages[:items_per_page]:
        author = user2 if user.id == user1.id else user1
        last_read_msg = user.last_read_msg_ts(msg.chat_id)
        message = MessageSchema(exclude=('author_id',)).dump(msg)
        message['isRead'] = False if not last_read_msg else \
            last_read_msg.timestamp >= msg.created_on
        message['user'] = UserSchema(only=('id', 'profile',)).dump(author)
        messages.append(message)

    return {
        'data': messages,
        'nextCursor': nextCursor,
    }


@messages.route('/messages', methods=['GET'])
@authenticate
def get_chat_messages(user):
    username = request.args.get('username', '')
    cursor = request.args.get('cursor')
    items_per_page = current_app.config['ITEMS_PER_PAGE']
    a_user = Profile.find_by_username(username).user
    nextCursor = None
    msgs = None

    if not a_user:
        return not_found('User not found.')

    try:
        query = user.get_chat_messages(a_user)
        chat = user.get_chat(a_user)

        if cursor == '0':
            msgs = query.limit(items_per_page + 1).all()
        else:
            cursor = urlsafe_base64(cursor, from_base64=True)
            msgs = query.filter(
                Message.created_on < cursor).limit(items_per_page + 1).all()

        if len(msgs) > items_per_page:
            nextCursor = urlsafe_base64(
                msgs[items_per_page - 1].created_on.isoformat())

        # check if lrm exist
        if chat:
            lrm = LastReadMessage.find_by_pk(user.id, chat.id)

            if lrm:
                lrm.timestamp = datetime.utcnow()
            else:
                lrm = LastReadMessage()
                lrm.user_id = user.id
                lrm.chat_id = chat.id
                lrm.timestamp = datetime.utcnow()
            lrm.save()
    except Exception as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')
    else:
        return {
            'data': MessageSchema(many=True).dump(msgs[:items_per_page]),
            'nextCursor': nextCursor
        }


@messages.route('/messages', methods=['POST'])
@authenticate
def create_message(user):
    req_data = request.get_json()
    user_id = request.args.get('user', None, int)

    if not req_data:
        return bad_request("No request data provided")

    try:
        a_user = User.find_by_id(user_id)

        if not a_user:
            return not_found('User not found.')

        chat = user.get_chat(a_user)

        if not chat:
            chat = Chat(user1_id=user.id, user2_id=a_user.id)
            db.session.add(chat)
            db.session.commit()

        message = Message()
        message.body = json.dumps(req_data.get('body'))
        message.author_id = user.id
        message.created_on = datetime.utcnow()
        message.chat_id = chat.id
        db.session.add(message)

        lrm = LastReadMessage.find_by_pk(user.id, chat.id)

        if lrm:
            lrm.timestamp = datetime.utcnow()
        else:
            lrm = LastReadMessage()
            lrm.user_id = user.id
            lrm.chat_id = chat.id
            lrm.timestamp = message.created_on
            db.session.add(lrm)

        user.add_notification(
            subject='message', item_id=message.id, id=a_user.id)
        user.save()
    except (IntegrityError, ProgrammingError, AttributeError, ValueError) as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')
    else:
        response = jsonify(MessageSchema().dump(message))
        response.status_code = 201
        response.headers['Location'] = url_for(
            'messages.get_messages', user=user, user_id=a_user.id)
        return response


@messages.route('/messages/<int:msg_id>', methods=['DELETE'])
@authenticate
def delete_message(user, msg_id):
    del_for_user = request.args.get('userOnly')
    try:
        message = Message.find_by_id(msg_id)

        if not message:
            return not_found('Message not found.')

        if del_for_user:
            user.delete_message_for_me(message)
            return {'message': 'Successfully deleted for you.'}

        if user.id != message.author_id:
            return error_response(403, "Cannot delete another user's message.")

        db.session.delete(
            Notification.find_by_attr(subject='message', item_id=msg_id))
        message.delete()
        return {'message': 'Successfully deleted.'}
    except (IntegrityError, ValueError):
        db.session.rollback()
        return server_error('Something went wrong, please try again.')


@messages.route('/notifications/count', methods=['GET'])
@authenticate
def get_notifications_count(user):
    """Get the count of new notifications"""
    return {
        'count': user.get_notifications().filter(
            Notification.timestamp > user.last_notif_read_time).count()
    }


@messages.route('/notifications', methods=['GET'])
@authenticate
def get_notifications(user):
    cursor = request.args.get('cursor')
    items_per_page = current_app.config['ITEMS_PER_PAGE']
    nextCursor = None
    notifs = None

    try:
        if cursor == '0':
            notifs = user.get_notifications().limit(items_per_page + 1).all()
        else:
            cursor = urlsafe_base64(cursor, from_base64=True)
            notifs = user.get_notifications().filter(
                Notification.timestamp < cursor).limit(
                    items_per_page + 1).all()

        if len(notifs) > items_per_page:
            nextCursor = urlsafe_base64(
                notifs[items_per_page - 1].timestamp.isoformat())

        user.last_notif_read_time = datetime.utcnow()
        user.save()
    except (IntegrityError, ValueError) as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')
    else:
        return {
            'data': NotificationSchema(many=True).dump(
                notifs[:items_per_page]),
            'nextCursor': nextCursor
        }


@messages.route('/notifications/<int:notif_id>', methods=['DELETE'])
@authenticate
def delete_notification(user, notif_id):
    try:
        notif = Notification.find_by_id(notif_id)

        if not notif:
            return not_found('Notification not found.')

        if user.id != notif.owner_id:
            return error_response(403, "Not allowed!")

        notif.delete()
        return {'message': 'Successfully removed.'}
    except (IntegrityError, ValueError) as e:
        db.session.rollback()
        print(e)
        return server_error('Something went wrong, please try again.')
