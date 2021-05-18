import random
import jwt
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import and_
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased
from werkzeug.security import generate_password_hash, check_password_hash

from src import db
from src.lib.mixins import ResourceMixin, SearchableMixin
from src.blueprints.posts.models import Post, post_tags
from src.blueprints.messages.models import Message, Chat, \
    LastReadMessage, Notification


followers = db.Table(
    'followers',
    db.Column(
        'follower_id',
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    ),
    db.Column(
        'followed_id',
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True)
)


user_tags = db.Table(
    'user_tags',
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    ),
    db.Column(
        'tag_id',
        db.Integer,
        db.ForeignKey('tags.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
)

deleted_msgs = db.Table(
    'deleted_messages',
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    ),
    db.Column(
        'message_id',
        db.Integer,
        db.ForeignKey('messages.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
)


class User(db.Model, ResourceMixin, SearchableMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean(), default=True, nullable=False)
    is_admin = db.Column(db.Boolean(), default=False, nullable=False)

    # Relationships
    profile = db.relationship(
        'Profile', uselist=False, backref='user', lazy='joined',
        cascade='all, delete-orphan')
    followed = db.relationship(
        'User', secondary='followers', lazy='dynamic',
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic')
    )
    posts = db.relationship(
        'Post', backref='author', cascade='all, delete-orphan')
    tags = db.relationship(
        'Tag', secondary='user_tags', lazy='dynamic', backref='users')
    chat1 = db.relationship(
        'Chat', foreign_keys='Chat.user1_id',
        backref='user1', cascade='all, delete-orphan')
    chat2 = db.relationship(
        'Chat', foreign_keys='Chat.user2_id',
        backref='user2', cascade='all, delete-orphan')
    deleted_messages = db.relationship(
        'Message', secondary=deleted_msgs, lazy='dynamic')
    last_notif_read_time = db.Column(db.DateTime, default=datetime.utcnow)
    notifications = db.relationship(
        'Notification',
        backref='user',
        cascade='all, delete-orphan',
        foreign_keys='Notification.doer_id'
    )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password = User.hash_password(kwargs.get('password', ''))

    def __str__(self):
        return f'<User {self.id} {self.email}>'

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter((cls.email == email)).first()

    @classmethod
    def hash_password(cls, password):
        """
        Hash a plaintext string using PBKDF2.

        :param password: Password in plain text
        :type password: str
        :return: str
        """
        if password:
            return generate_password_hash(password)

        return None

    def check_password(self, password):
        """
        Check if the provided password matches that of the specified user.

        :param password: Password in plain text
        :return: boolean
        """
        return check_password_hash(self.password, password)

    def encode_auth_token(self):
        """Generates the auth token"""
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(
                    days=current_app.config.get('TOKEN_EXPIRATION_DAYS'),
                    seconds=current_app.config.get('TOKEN_EXPIRATION_SECONDS')
                ),
                'iat': datetime.utcnow(),
                'sub': {
                    'id': self.id,
                }
            }
            return jwt.encode(
                payload,
                current_app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(token):
        """
        Decodes the auth token

        :param string: token
        :return dict: The user's identity
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config.get('SECRET_KEY'),
                algorithms='HS256'
            )
            return payload.get('sub')
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_users_to_follow(self, count=3):
        likes = self.likes.subquery()
        liked_posts = db.session.query(User).join(
            likes, User.id == likes.c.user_id).distinct().except_(
                self.followed).order_by(User.updated_on).limit(count)

        if liked_posts.count() > 0:
            return liked_posts.all()

        return [User.find_by_id(random.randrange(
            User.query.count())) for _ in range(count)]

    def get_followed_posts(self):
        followed_users_posts = db.session.query(Post.id).join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).filter(
                    Post.comment_id.is_(None))
        own_posts = db.session.query(Post.id).filter_by(
            user_id=self.id).filter(Post.comment_id.is_(None))

        return db.session.query(Post.id).join(
            post_tags, Post.id == post_tags.c.post_id).join(
                user_tags, post_tags.c.tag_id == user_tags.c.tag_id).filter(
                    user_tags.c.user_id == self.id).union(
                        followed_users_posts.union(own_posts))

    def follow_tag(self, tag):
        if not self.is_following_tag(tag):
            self.tags.append(tag)

    def unfollow_tag(self, tag):
        if self.is_following_tag(tag):
            self.tags.remove(tag)

    def is_following_tag(self, tag):
        return self.tags.filter(user_tags.c.tag_id == tag.id).count() > 0

    def add_notification(self, subject, item_id, id, **kwargs):
        notif = Notification(
            subject=subject, item_id=item_id, user_id=id, doer_id=self.
            id, **kwargs)
        db.session.add(notif)
        return notif

    def get_notifications(self):
        return Notification.query.filter_by(user_id=self.id).order_by(
            Notification.timestamp.desc())

    def get_chat(self, user):
        '''Get chat between user?'''
        return Chat.query.filter(
            and_(Chat.user1_id == self.id, Chat.user2_id == user.id) |
            and_(Chat.user1_id == user.id, Chat.user2_id == self.id)).first()

    def get_chat_messages(self, user):
        '''Get all the messages in a conversation between two users'''
        return Message.query.join(Chat.messages).filter(
            and_(Chat.user1_id == self.id, Chat.user2_id == user.id) |
            and_(Chat.user1_id == user.id, Chat.user2_id == self.id)).except_(
                self.deleted_messages).order_by(Message.created_on.desc())

    def get_chat_last_messages(self):
        '''Get the last messages in all chats with self.'''
        user1 = aliased(User)
        user2 = aliased(User)
        # get the last message in all chats.
        last_msgs = db.session.query(Message.chat_id, func.max(
            Message.created_on).label('last_messages')).group_by(
                Message.chat_id).subquery()
        # return the users and messages involved in the conversation with self
        return last_msgs, db.session.query(
            Message, user1, user2, last_msgs.c.last_messages).join(
            last_msgs, Message.created_on == last_msgs.c.last_messages).join(
                Chat, Chat.id == Message.chat_id).join(
                    user1, user1.id == Chat.user1_id).join(
                        user2, user2.id == Chat.user2_id).filter((
                            Chat.user1_id == self.id) | (
                                Chat.user2_id == self.id)).order_by(
                                    last_msgs.c.last_messages.desc())

    def last_read_msg_ts(self, chat_id):
        return LastReadMessage.query.filter(and_(
            LastReadMessage.user_id == self.id,
            LastReadMessage.chat_id == chat_id)).first()

    def delete_message_for_me(self, message):
        self.deleted_messages.append(message)
        self.save()
