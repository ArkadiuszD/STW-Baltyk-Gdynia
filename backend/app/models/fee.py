from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Enum

from app import db


class FeeFrequency(PyEnum):
    YEARLY = 'yearly'
    MONTHLY = 'monthly'
    ONE_TIME = 'one_time'


class FeeStatus(PyEnum):
    PENDING = 'pending'
    PAID = 'paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'


class FeeType(db.Model):
    """Type/template for fees (e.g., Annual membership 2025)."""
    __tablename__ = 'fee_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    frequency = db.Column(Enum(FeeFrequency), nullable=False)
    due_day = db.Column(db.Integer, nullable=True)  # Day of month/year
    due_month = db.Column(db.Integer, nullable=True)  # Month for yearly fees
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    fees = db.relationship('Fee', backref='fee_type', lazy='dynamic')

    def __repr__(self):
        return f'<FeeType {self.name}: {self.amount} PLN>'


class Fee(db.Model):
    """Individual fee assigned to a member."""
    __tablename__ = 'fees'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False, index=True)
    fee_type_id = db.Column(db.Integer, db.ForeignKey('fee_types.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(Enum(FeeStatus), default=FeeStatus.PENDING, nullable=False, index=True)
    paid_date = db.Column(db.Date, nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    transaction = db.relationship('Transaction', backref='matched_fee', uselist=False)

    @property
    def is_overdue(self) -> bool:
        """Check if fee is past due date and unpaid."""
        return self.status == FeeStatus.PENDING and self.due_date < date.today()

    @property
    def days_overdue(self) -> int:
        """Calculate days past due date."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    def mark_as_paid(self, paid_date: date = None, transaction_id: int = None):
        """Mark fee as paid."""
        self.status = FeeStatus.PAID
        self.paid_date = paid_date or date.today()
        if transaction_id:
            self.transaction_id = transaction_id

    def __repr__(self):
        return f'<Fee {self.id}: {self.amount} PLN ({self.status.value})>'
