import random
from sqlalchemy.sql import func
from src import db
from src.lib.mixins import ResourceMixin, SearchableMixin
from src.blueprints.posts.models import post_tags
from src.blueprints.users.schema import UserSchema


class Tag(db.Model, ResourceMixin, SearchableMixin):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, index=True, unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

    @classmethod
    def get_top_tags(cls, user):
        tags = cls.query.except_(user.tags).subquery()
        return db.session.query(tags.c.tags_id, func.count(
            post_tags.c.tag_id).label('nPosts')).join(
                post_tags, tags.c.tags_id == post_tags.c.tag_id).group_by(
                    tags.c.tags_id)

    def to_dict(self, user):
        followers = []
        count = 0

        if len(self.users) == 1 or len(self.users) == 2:
            followers = UserSchema(
                many=True, only=('id', 'profile',)).dump(user)

        if len(self.users) > 2:
            followers = UserSchema(many=True, only=('id', 'profile',)).dump(
                random.sample(self.users, k=2))
            count = len(self.users) - 2

        return {
            'id': self.id,
            'name': self.name,
            'isFollowing': user.is_following_tag(self),
            'followedBy': {'users': followers, 'count': count}
        }
