from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Schema for user output."""
    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    full_name = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    last_login = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class UserCreateSchema(Schema):
    """Schema for creating a user."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(validate=validate.OneOf(['admin', 'treasurer', 'board']))
    member_id = fields.Int(allow_none=True)


class LoginSchema(Schema):
    """Schema for login request."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
