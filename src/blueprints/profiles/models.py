import random
from hashlib import md5

from src import db
from src.lib.mixins import ResourceMixin


class Profile(db.Model, ResourceMixin):
    __tablename__ = 'profiles'

    # Identification
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(32), index=True, nullable=False, unique=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    avatar = db.Column(db.String(128))
    dob = db.Column(db.DateTime)
    bio = db.Column(db.Text)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )

    def __repr__(self):
        return f'<Profile: {self.name}>'

    @staticmethod
    def set_avatar(email, size=128):
        digest = md5(email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?s={size}&d=mm&r=pg'

    @classmethod
    def find_by_username(cls, username):
        """
        Find a user by their username.

        :param: user username - username
        :return: User instance
        """
        return cls.query.filter(cls.username == username).first()

    def set_username(self):
        username = f'{self.firstname.lower()}{self.lastname.lower()}'
        check = Profile.query.filter(Profile.username == username).first()

        if check:
            digits = str(random() * 1e5).split('.')[0]
            username = f'{username}{digits}'

        return username
