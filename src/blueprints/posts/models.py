from sqlalchemy.sql import func
from src import db
from src.lib.mixins import ResourceMixin


post_likes = db.Table(
    'post_likes',
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    ),
    db.Column(
        'post_id',
        db.Integer,
        db.ForeignKey('posts.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
)


post_tags = db.Table(
    'post_tags',
    db.Column(
        'tag_id',
        db.Integer,
        db.ForeignKey('tags.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    ),
    db.Column(
        'post_id',
        db.Integer,
        db.ForeignKey('posts.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
)


class Post(db.Model, ResourceMixin):
    __tablename__ = 'posts'

    # Identification
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='CASCADE', onupdate='CASCADE'))
    comment_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    # relationships
    comments = db.relationship(
        "Post", lazy='dynamic', backref=db.backref('parent', remote_side=[id]))
    likes = db.relationship(
        'User', secondary=post_likes, lazy='dynamic',
        backref=db.backref('likes', lazy='dynamic')
    )
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')

    def __repr__(self):
        return f'<Post {self.body}>'

    def is_liked_by(self, user):
        return self.likes.filter(
            post_likes.c.user_id == user.id).count() > 0

    @classmethod
    def get_reactions(cls):
        '''Gets all posts and their reactions.'''
        posts = cls.query.filter(cls.comment_id.is_(None)).subquery()
        ncomments = db.session.query(posts.c.id, func.count(cls.id).label(
            'num_comments')).outerjoin(
                cls, posts.c.id == cls.comment_id).group_by(
                    posts.c.id).subquery()
        nlikes = db.session.query(cls.id, func.count(
            post_likes.c.post_id).label('num_likes')).join(
                post_likes, cls.id == post_likes.c.post_id).group_by(
                    cls.id).subquery()
        return db.session.query(ncomments.c.id, (
            ncomments.c.num_comments + nlikes.c.num_likes).label(
                'reactions')).outerjoin(nlikes, ncomments.c.id == nlikes.c.id)

    @classmethod
    def get_by_reactions(cls):
        '''Gets all posts and ordered by their reactions.'''
        posts = cls.get_reactions().subquery()
        return db.session.query(Post.id, func.row_number().over(
            order_by=posts.c.reactions).label('sequence')).join(
                cls, posts.c.id == Post.id)

    def to_dict(self, auth):
        return {
            'id': self.id,
            'body': self.body,
            'likes': self.likes.count(),
            'comments': self.comments.count(),
            'isLiked': self.is_liked_by(auth),
            'created_on': self.created_on,
            'author': {
                'id': self.author.id,
                'username': self.author.profile.username,
                'name': self.author.profile.name,
                'avatar': self.author.profile.avatar,
                'isFollowing': auth.is_following(self.author)
                if auth.id != self.author.id else None,
            },
            'tags': [{
                'id': tag.id,
                'name': tag.name,
            } for tag in self.tags],
        }
