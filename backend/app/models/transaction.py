from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import Enum

from app import db


class TransactionType(PyEnum):
    INCOME = 'income'
    EXPENSE = 'expense'


class TransactionCategory(PyEnum):
    # Income categories
    FEES = 'fees'  # składki członkowskie
    DONATIONS = 'donations'  # darowizny
    GRANTS = 'grants'  # dotacje
    EVENTS_INCOME = 'events_income'  # przychody z wydarzeń
    EQUIPMENT_RENTAL = 'equipment_rental'  # wynajem sprzętu
    OTHER_INCOME = 'other_income'

    # Expense categories
    ADMINISTRATION = 'administration'  # opłaty bankowe, ubezpieczenia, biuro
    STATUTORY_ACTIVITIES = 'statutory_activities'  # działalność statutowa
    EQUIPMENT_PURCHASE = 'equipment_purchase'  # zakup sprzętu
    EQUIPMENT_MAINTENANCE = 'equipment_maintenance'  # konserwacja sprzętu
    EVENTS_EXPENSE = 'events_expense'  # organizacja wydarzeń
    TRAINING = 'training'  # szkolenia
    RENT = 'rent'  # czynsz i media
    OTHER_EXPENSE = 'other_expense'


class Transaction(db.Model):
    """Financial transaction (income or expense)."""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(Enum(TransactionType), nullable=False, index=True)
    category = db.Column(Enum(TransactionCategory), nullable=False)
    description = db.Column(db.Text, nullable=False)
    counterparty = db.Column(db.String(255), nullable=True)  # Payer/payee name
    bank_reference = db.Column(db.String(100), nullable=True, unique=True)  # Bank statement ID

    # Matching with member
    matched_member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=True, index=True)
    matched_member = db.relationship('Member', backref='transactions')
    match_confidence = db.Column(db.String(20), nullable=True)  # auto, manual, none

    # Import metadata
    imported_at = db.Column(db.DateTime, nullable=True)
    import_source = db.Column(db.String(50), nullable=True)  # mt940, csv, manual

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', backref='created_transactions')

    @property
    def is_income(self) -> bool:
        return self.type == TransactionType.INCOME

    @property
    def is_expense(self) -> bool:
        return self.type == TransactionType.EXPENSE

    def __repr__(self):
        sign = '+' if self.is_income else '-'
        return f'<Transaction {self.date}: {sign}{self.amount} PLN>'
