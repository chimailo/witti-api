from marshmallow import Schema, fields


class MessageSchema(Schema):
    id = fields.Int(dump_only=True)
    body = fields.Str(required=True)
    created_on = fields.DateTime(dump_only=True)
    author_id = fields.Int(dump_only=True)


class NotificationSchema(Schema):
    id = fields.Int(dump_only=True)
    subject = fields.Str(dump_only=True)
    item_id = fields.Int(dump_only=True)
    timestamp = fields.DateTime(dump_only=True)
    user = fields.Nested('UserSchema', dump_only=True, only=(
        'id', 'profile',))
    post = fields.Nested('PostSchema', dump_only=True, only=('id', 'body',))
