import re
from marshmallow import Schema, fields, validate, validates, ValidationError


class ProfileSchema(Schema):
    username = fields.Str(
        validate=validate.Length(min=3, max=32),
        required=True,
        error_messages={"required": "Username is required."}
    )
    name = fields.Str(
        validate=validate.Length(min=2, max=128),
        required=True,
        error_messages={"required": "Name is required."}
    )
    avatar = fields.Url(validate=validate.Length(max=255))
    dob = fields.Str(validate=validate.Length(min=16, max=32))
    bio = fields.Str()
    created_on = fields.DateTime(dump_only=True)
    updated_on = fields.DateTime(dump_only=True)


@validates('username')
def validate_username(self, username):
    if re.match('^[a-zA-Z0-9_]+$', username) is None:
        raise ValidationError(
            'Username can only contain valid characters.'
        )
