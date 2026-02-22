from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import Enum

from app import db


class EventType(PyEnum):
    CRUISE = 'cruise'  # rejs
    KAYAK_TRIP = 'kayak_trip'  # spływ kajakowy
    TRAINING = 'training'  # szkolenie
    MEETING = 'meeting'  # spotkanie
    OTHER = 'other'


class EventStatus(PyEnum):
    PLANNED = 'planned'
    REGISTRATION_OPEN = 'registration_open'
    FULL = 'full'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class ParticipantStatus(PyEnum):
    REGISTERED = 'registered'
    WAITLIST = 'waitlist'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'


class Event(db.Model):
    """Events organized by the association (cruises, trips, trainings)."""
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(Enum(EventType), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)

    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False)
    registration_deadline = db.Column(db.Date, nullable=True)

    max_participants = db.Column(db.Integer, nullable=True)
    status = db.Column(Enum(EventStatus), default=EventStatus.PLANNED, nullable=False)

    # Optional cost per participant
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', backref='created_events')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    participants = db.relationship('EventParticipant', backref='event', lazy='dynamic',
                                   cascade='all, delete-orphan')

    @property
    def registered_count(self) -> int:
        """Count of registered (not waitlisted or cancelled) participants."""
        return self.participants.filter(
            EventParticipant.status.in_([ParticipantStatus.REGISTERED, ParticipantStatus.CONFIRMED])
        ).count()

    @property
    def waitlist_count(self) -> int:
        """Count of waitlisted participants."""
        return self.participants.filter_by(status=ParticipantStatus.WAITLIST).count()

    @property
    def spots_available(self) -> int:
        """Number of available spots."""
        if self.max_participants is None:
            return 999  # Unlimited
        return max(0, self.max_participants - self.registered_count)

    @property
    def is_full(self) -> bool:
        """Check if event has reached max participants."""
        if self.max_participants is None:
            return False
        return self.registered_count >= self.max_participants

    @property
    def is_registration_open(self) -> bool:
        """Check if registration is still open."""
        if self.status != EventStatus.REGISTRATION_OPEN:
            return False
        if self.registration_deadline and date.today() > self.registration_deadline:
            return False
        return True

    def __repr__(self):
        return f'<Event {self.name} ({self.start_date.date()})>'


class EventParticipant(db.Model):
    """Member participation in an event."""
    __tablename__ = 'event_participants'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)

    status = db.Column(Enum(ParticipantStatus), default=ParticipantStatus.REGISTERED, nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Unique constraint: member can register only once per event
    __table_args__ = (
        db.UniqueConstraint('event_id', 'member_id', name='uq_event_member'),
    )

    def __repr__(self):
        return f'<EventParticipant {self.member_id} -> {self.event_id} ({self.status.value})>'
