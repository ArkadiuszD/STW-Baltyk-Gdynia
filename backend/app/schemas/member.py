from marshmallow import Schema, fields, validate, post_load
from datetime import date


class MemberSchema(Schema):
    """Schema for member output."""
    id = fields.Int(dump_only=True)
    member_number = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()
    full_name = fields.Str(dump_only=True)
    email = fields.Email()
    phone = fields.Str()
    address = fields.Str()
    join_date = fields.Date()
    status = fields.Str()
    notes = fields.Str()
    data_consent = fields.Bool()
    consent_date = fields.DateTime()
    total_debt = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class MemberCreateSchema(Schema):
    """Schema for creating a member."""
    member_number = fields.Str(validate=validate.Length(max=20))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    phone = fields.Str(validate=validate.Length(max=20))
    address = fields.Str()
    join_date = fields.Date(load_default=date.today)
    status = fields.Str(validate=validate.OneOf(['active', 'suspended', 'former']),
                        load_default='active')
    notes = fields.Str()
    data_consent = fields.Bool(load_default=False)


class MemberUpdateSchema(Schema):
    """Schema for updating a member."""
    member_number = fields.Str(validate=validate.Length(max=20))
    first_name = fields.Str(validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    phone = fields.Str(validate=validate.Length(max=20))
    address = fields.Str()
    status = fields.Str(validate=validate.OneOf(['active', 'suspended', 'former']))
    notes = fields.Str()
    data_consent = fields.Bool()
