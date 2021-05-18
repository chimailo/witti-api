import re
from marshmallow import Schema, fields, validate, validates, ValidationError


class TagSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=16), required=True)

    class Meta:
        additional = ("id", "created_on", 'updated_on')


@validates('name')
def validate_tag_name(self, name):
    print('tag name:', name)
    if re.match('^[a-zA-Z0-9]+$', name) is None:
        print('tag name:', name)
        raise ValidationError('Tag name can only contain valid characters.')
