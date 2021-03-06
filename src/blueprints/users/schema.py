import re
from marshmallow import Schema, fields, validate, validates, ValidationError


class UserSchema(Schema):
    id = fields.Str(dump_only=True, validate=validate.Length(max=32))
    email = fields.Email(
        required=True, error_messages={"required": "Email is required."})
    is_active = fields.Boolean()
    is_admin = fields.Boolean()

    followers = fields.Function(lambda user: user.followers.count())
    following = fields.Function(lambda user: user.followed.count())
    # relationships
    activity = fields.Nested('ActivitySchema', dump_only=True)
    profile = fields.Nested('ProfileSchema', dump_only=True,)
    messages = fields.Nested('MessageSchema', many=True)
    posts = fields.Nested('PostSchema', many=True)
    tags = fields.Nested('TagSchema', many=True, dump_only=True)
    permissions = fields.Nested('PermissionSchema', many=True)


class AuthSchema(Schema):
    id = fields.Str(
        validate=validate.Length(max=32),
        required=True,
        error_messages={"required": "Required."}
    )
    name = fields.Str(
        validate=validate.Length(min=2, max=128),
        load_only=True,
        required=True,
        error_messages={"required": "Name is required."}
    )
    username = fields.Str(
        validate=validate.Length(min=3, max=32),
        required=True,
        error_messages={"required": "Username is required."}
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required."}
    )


@validates('username')
def validate_username(self, username):
    if re.match('^[a-zA-Z0-9_]+$', username) is None:
        raise ValidationError(
            'Username can only contain valid characters.'
        )
