from marshmallow import Schema, fields, validate


class FeeTypeSchema(Schema):
    """Schema for fee type output."""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    amount = fields.Decimal(as_string=True)
    frequency = fields.Str()
    due_day = fields.Int()
    due_month = fields.Int()
    is_active = fields.Bool()
    description = fields.Str()
    created_at = fields.DateTime(dump_only=True)


class FeeTypeCreateSchema(Schema):
    """Schema for creating a fee type."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    amount = fields.Decimal(required=True, as_string=True)
    frequency = fields.Str(required=True,
                           validate=validate.OneOf(['yearly', 'monthly', 'one_time']))
    due_day = fields.Int(validate=validate.Range(min=1, max=31))
    due_month = fields.Int(validate=validate.Range(min=1, max=12))
    is_active = fields.Bool(load_default=True)
    description = fields.Str()


class FeeSchema(Schema):
    """Schema for fee output."""
    id = fields.Int(dump_only=True)
    member_id = fields.Int()
    member = fields.Nested('MemberSchema', only=['id', 'full_name', 'email'], dump_only=True)
    fee_type_id = fields.Int()
    fee_type = fields.Nested(FeeTypeSchema, only=['id', 'name'], dump_only=True)
    amount = fields.Decimal(as_string=True)
    due_date = fields.Date()
    status = fields.Str()
    paid_date = fields.Date()
    transaction_id = fields.Int()
    notes = fields.Str()
    is_overdue = fields.Bool(dump_only=True)
    days_overdue = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class FeeCreateSchema(Schema):
    """Schema for creating a fee."""
    member_id = fields.Int(required=True)
    fee_type_id = fields.Int(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    due_date = fields.Date(required=True)
    status = fields.Str(validate=validate.OneOf(['pending', 'paid', 'overdue', 'cancelled']),
                        load_default='pending')
    notes = fields.Str()
