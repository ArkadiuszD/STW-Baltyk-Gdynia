from marshmallow import Schema, fields, validate

from app.utils.enums import enum_values, EquipmentType, EquipmentStatus, ReservationStatus


class EquipmentSchema(Schema):
    """Schema for equipment output."""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    type = fields.Str()
    status = fields.Str()
    description = fields.Str()
    photo_url = fields.Str()
    inventory_number = fields.Str()
    purchase_date = fields.Date()
    last_maintenance = fields.Date()
    next_maintenance = fields.Date()
    needs_maintenance = fields.Bool(dump_only=True)
    is_available = fields.Bool(dump_only=True)
    notes = fields.Str()
    created_at = fields.DateTime(dump_only=True)


class EquipmentCreateSchema(Schema):
    """Schema for creating equipment."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    type = fields.Str(required=True, validate=validate.OneOf(enum_values(EquipmentType)))
    status = fields.Str(validate=validate.OneOf(enum_values(EquipmentStatus)),
                        load_default=EquipmentStatus.AVAILABLE.value)
    description = fields.Str()
    photo_url = fields.Str(validate=validate.Length(max=500))
    inventory_number = fields.Str(validate=validate.Length(max=50))
    purchase_date = fields.Date()
    last_maintenance = fields.Date()
    next_maintenance = fields.Date()
    notes = fields.Str()


class ReservationSchema(Schema):
    """Schema for reservation output."""
    id = fields.Int(dump_only=True)
    equipment_id = fields.Int()
    equipment = fields.Nested(EquipmentSchema, only=['id', 'name', 'type'], dump_only=True)
    member_id = fields.Int()
    member = fields.Nested('MemberSchema', only=['id', 'full_name', 'phone'], dump_only=True)
    start_date = fields.DateTime()
    end_date = fields.DateTime()
    status = fields.Str()
    purpose = fields.Str()
    notes = fields.Str()
    is_active = fields.Bool(dump_only=True)
    duration_days = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class ReservationCreateSchema(Schema):
    """Schema for creating a reservation."""
    equipment_id = fields.Int(required=True)
    member_id = fields.Int(required=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    status = fields.Str(validate=validate.OneOf(enum_values(ReservationStatus)),
                        load_default=ReservationStatus.PENDING.value)
    purpose = fields.Str(validate=validate.Length(max=255))
    notes = fields.Str()
