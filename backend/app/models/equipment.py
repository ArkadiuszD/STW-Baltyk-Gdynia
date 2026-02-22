from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import Enum

from app import db


class EquipmentType(PyEnum):
    KAYAK = 'kayak'
    SAILBOAT = 'sailboat'
    SUP = 'sup'
    MOTORBOAT = 'motorboat'
    OTHER = 'other'


class EquipmentStatus(PyEnum):
    AVAILABLE = 'available'
    RESERVED = 'reserved'
    MAINTENANCE = 'maintenance'
    RETIRED = 'retired'


class ReservationStatus(PyEnum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Equipment(db.Model):
    """Water sports equipment owned by the association."""
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(Enum(EquipmentType), nullable=False, index=True)
    status = db.Column(Enum(EquipmentStatus), default=EquipmentStatus.AVAILABLE, nullable=False)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    inventory_number = db.Column(db.String(50), unique=True, nullable=True)

    # Dates
    purchase_date = db.Column(db.Date, nullable=True)
    last_maintenance = db.Column(db.Date, nullable=True)
    next_maintenance = db.Column(db.Date, nullable=True)

    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reservations = db.relationship('Reservation', backref='equipment', lazy='dynamic',
                                   cascade='all, delete-orphan')

    @property
    def needs_maintenance(self) -> bool:
        """Check if equipment is due for maintenance."""
        if not self.next_maintenance:
            return False
        return self.next_maintenance <= date.today()

    @property
    def is_available(self) -> bool:
        """Check if equipment can be reserved."""
        return self.status == EquipmentStatus.AVAILABLE

    def __repr__(self):
        return f'<Equipment {self.name} ({self.type.value})>'


class Reservation(db.Model):
    """Equipment reservation by a member."""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)

    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)

    purpose = db.Column(db.String(255), nullable=True)  # e.g., "Weekend trip"
    notes = db.Column(db.Text, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', backref='created_reservations')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_active(self) -> bool:
        """Check if reservation is currently active."""
        now = datetime.utcnow()
        return (
            self.status == ReservationStatus.CONFIRMED and
            self.start_date <= now <= self.end_date
        )

    @property
    def duration_days(self) -> int:
        """Calculate reservation duration in days."""
        delta = self.end_date - self.start_date
        return delta.days + 1

    def __repr__(self):
        return f'<Reservation {self.id}: {self.equipment.name if self.equipment else "?"} ({self.start_date.date()} - {self.end_date.date()})>'
