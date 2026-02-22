from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import Enum

from app import db


class MemberStatus(PyEnum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    FORMER = 'former'


class Member(db.Model):
    """Member of the association."""
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    member_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    join_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(Enum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # RODO consent
    data_consent = db.Column(db.Boolean, default=False, nullable=False)
    consent_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fees = db.relationship('Fee', backref='member', lazy='dynamic', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='member', lazy='dynamic')
    event_participations = db.relationship('EventParticipant', backref='member', lazy='dynamic')

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def pending_fees(self):
        """Get all unpaid fees."""
        from app.models.fee import FeeStatus
        return self.fees.filter(Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])).all()

    @property
    def total_debt(self):
        """Calculate total unpaid amount."""
        return sum(fee.amount for fee in self.pending_fees)

    def __repr__(self):
        return f'<Member {self.full_name}>'


# Import Fee here to avoid circular import in pending_fees property
from app.models.fee import Fee
