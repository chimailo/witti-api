from datetime import datetime
from sqlalchemy import and_
from src import db


class Chat(db.Model):
    __tablename__ = 'chats'
    __table_args__ = (
        db.Index('_chat_users_idx', 'user2_id', 'user1_id', unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    messages = db.relationship(
        'Message', backref='chat', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Chat: user_{self.user1_id} <-> user_{self.user2_id}>"


class LastReadMessage(db.Model):
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id"), primary_key=True, nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey(
        "chats.id"), primary_key=True, nullable=False)

    def save(self):
        """
        Save a model instance.

        :return: Model instance
        """
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_pk(cls, user_id, chat_id):
        return cls.query.filter(
            and_(cls.user_id == user_id, cls.chat_id == chat_id)
        ).first()


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text())
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    chat_id = db.Column(
        db.Integer, db.ForeignKey("chats.id"), nullable=False)

    def __repr__(self):
        return "<Message {}>".format(self.id)

    @classmethod
    def find_by_id(cls, id):
        """
        Get a class instance given its id

        :param id: int
        :return: Class instance
        """
        return cls.query.get(int(id))

    def save(self):
        """
        Save a model instance.

        :return: Model instance
        """
        db.session.add(self)
        db.session.commit()

        return self

    def delete(self):
        """
        Delete a model instance.

        :return: db.session.commit()'s result
        """
        db.session.delete(self)
        return db.session.commit()


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128), index=True)
    item_id = db.Column(db.Integer(), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    doer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    post = db.relationship('Post', backref='notif', lazy='joined')

    def __repr__(self):
        return "<Notification {}>".format(self.subject)

    @classmethod
    def find_by_id(cls, id):
        """
        Get a class instance given its id

        :param id: int
        :return: Class instance
        """
        return cls.query.get(int(id))

    @classmethod
    def find_by_attr(cls, subject, item_id):
        """
        Get a class instance given its attributes

        :param subject: str
        :param item_id: id
        :return: Class instance
        """
        if subject == 'post':
            return cls.query.filter(
                and_(cls.subject == subject, cls.item_id == item_id)).all()

        return cls.query.filter(
            and_(cls.subject == subject, cls.item_id == item_id)).first()
