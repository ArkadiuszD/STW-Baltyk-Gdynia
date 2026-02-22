from marshmallow import Schema, fields, validate


class EventParticipantSchema(Schema):
    """Schema for event participant output."""
    id = fields.Int(dump_only=True)
    event_id = fields.Int()
    member_id = fields.Int()
    member = fields.Nested('MemberSchema', only=['id', 'full_name', 'email', 'phone'],
                           dump_only=True)
    status = fields.Str()
    registered_at = fields.DateTime(dump_only=True)
    notes = fields.Str()


class EventParticipantCreateSchema(Schema):
    """Schema for registering a participant."""
    member_id = fields.Int(required=True)
    notes = fields.Str()


class EventSchema(Schema):
    """Schema for event output."""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    type = fields.Str()
    description = fields.Str()
    location = fields.Str()
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    registration_deadline = fields.Date()
    max_participants = fields.Int()
    status = fields.Str()
    cost = fields.Decimal(as_string=True)
    notes = fields.Str()
    registered_count = fields.Int(dump_only=True)
    waitlist_count = fields.Int(dump_only=True)
    spots_available = fields.Int(dump_only=True)
    is_full = fields.Bool(dump_only=True)
    is_registration_open = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    participants = fields.Nested(EventParticipantSchema, many=True, dump_only=True)


class EventCreateSchema(Schema):
    """Schema for creating an event."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    type = fields.Str(required=True, validate=validate.OneOf([
        'cruise', 'kayak_trip', 'training', 'meeting', 'other'
    ]))
    description = fields.Str()
    location = fields.Str(validate=validate.Length(max=255))
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    registration_deadline = fields.Date()
    max_participants = fields.Int(validate=validate.Range(min=1))
    status = fields.Str(validate=validate.OneOf([
        'planned', 'registration_open', 'full', 'ongoing', 'completed', 'cancelled'
    ]), load_default='planned')
    cost = fields.Decimal(as_string=True)
    notes = fields.Str()
