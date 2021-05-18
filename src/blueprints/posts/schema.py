from marshmallow import Schema, fields


class PostSchema(Schema):
    body = fields.Str(required=True)
    parent = fields.Nested(
        'PostSchema', only=('id', 'body', 'author',), dump_only=True)
    tags = fields.Nested(
        'TagSchema', only=('id', 'name',), many=True, dump_only=True)
    likes = fields.Function(lambda post: post.likes.count())
    comments = fields.Function(lambda post: post.comments.count())
    author = fields.Nested('UserSchema', only=(
        'id', 'profile',), dump_only=True)

    class Meta:
        additional = ("id", "created_on", 'updated_on')
