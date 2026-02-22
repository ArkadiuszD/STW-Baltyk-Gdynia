from marshmallow import Schema, fields, validate


class TransactionSchema(Schema):
    """Schema for transaction output."""
    id = fields.Int(dump_only=True)
    date = fields.Date()
    amount = fields.Decimal(as_string=True)
    type = fields.Str()
    category = fields.Str()
    description = fields.Str()
    counterparty = fields.Str()
    bank_reference = fields.Str()
    matched_member_id = fields.Int()
    matched_member = fields.Nested('MemberSchema', only=['id', 'full_name'], dump_only=True)
    match_confidence = fields.Str()
    imported_at = fields.DateTime()
    import_source = fields.Str()
    created_at = fields.DateTime(dump_only=True)


class TransactionCreateSchema(Schema):
    """Schema for creating a transaction manually."""
    date = fields.Date(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    type = fields.Str(required=True, validate=validate.OneOf(['income', 'expense']))
    category = fields.Str(required=True, validate=validate.OneOf([
        'fees', 'donations', 'grants', 'other_income',
        'administration', 'statutory_activities', 'equipment', 'events', 'other_expense'
    ]))
    description = fields.Str(required=True)
    counterparty = fields.Str()
    bank_reference = fields.Str()
    matched_member_id = fields.Int()


class TransactionMatchSchema(Schema):
    """Schema for matching transaction to member/fee."""
    member_id = fields.Int(required=True)
    fee_id = fields.Int()  # Optional: specific fee to mark as paid


class TransactionImportSchema(Schema):
    """Schema for imported transaction (from bank statement)."""
    date = fields.Date(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    description = fields.Str(required=True)
    counterparty = fields.Str()
    bank_reference = fields.Str()
    # Matching suggestions
    suggested_member_id = fields.Int()
    suggested_fee_id = fields.Int()
    match_confidence = fields.Str()
