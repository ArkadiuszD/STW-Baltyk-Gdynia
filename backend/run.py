#!/usr/bin/env python3
"""Flask application entry point."""

import os
from app import create_app, db
from app.models import User, Member, Fee, FeeType, Transaction, Equipment, Reservation, Event, EventParticipant
from app.models.user import UserRole

# Get config from environment
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)


@app.shell_context_processor
def make_shell_context():
    """Make shell context for flask shell command."""
    return {
        'db': db,
        'User': User,
        'Member': Member,
        'Fee': Fee,
        'FeeType': FeeType,
        'Transaction': Transaction,
        'Equipment': Equipment,
        'Reservation': Reservation,
        'Event': Event,
        'EventParticipant': EventParticipant,
    }


@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')


@app.cli.command('create-admin')
def create_admin():
    """Create admin user."""
    email = input('Admin email: ')
    password = input('Admin password: ')
    first_name = input('First name: ')
    last_name = input('Last name: ')

    if User.query.filter_by(email=email).first():
        print('User with this email already exists.')
        return

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print(f'Admin user {email} created.')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed database with demo data."""
    from datetime import date, datetime, timedelta
    from decimal import Decimal
    from app.models.member import MemberStatus
    from app.models.fee import FeeFrequency, FeeStatus
    from app.models.equipment import EquipmentType, EquipmentStatus
    from app.models.event import EventType, EventStatus

    # Create admin user if not exists
    if not User.query.filter_by(email='admin@baltyk.pl').first():
        admin = User(
            email='admin@baltyk.pl',
            first_name='Admin',
            last_name='STW',
            role=UserRole.ADMIN
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print('Created admin user: admin@baltyk.pl / admin123')

    # Create fee types
    if not FeeType.query.first():
        fee_types = [
            FeeType(name='Składka roczna 2025', amount=Decimal('100.00'),
                    frequency=FeeFrequency.YEARLY, due_day=1, due_month=1, is_active=True),
            FeeType(name='Wpisowe', amount=Decimal('50.00'),
                    frequency=FeeFrequency.ONE_TIME, is_active=True),
        ]
        db.session.add_all(fee_types)
        print('Created fee types.')

    # Create sample members
    if not Member.query.first():
        members = [
            Member(member_number='001', first_name='Jan', last_name='Kowalski',
                   email='jan.kowalski@example.com', phone='600111222',
                   status=MemberStatus.ACTIVE, data_consent=True,
                   consent_date=datetime.utcnow(), join_date=date(2020, 1, 15)),
            Member(member_number='002', first_name='Anna', last_name='Nowak',
                   email='anna.nowak@example.com', phone='600333444',
                   status=MemberStatus.ACTIVE, data_consent=True,
                   consent_date=datetime.utcnow(), join_date=date(2021, 3, 10)),
            Member(member_number='003', first_name='Piotr', last_name='Wiśniewski',
                   email='piotr.wisniewski@example.com', phone='600555666',
                   status=MemberStatus.ACTIVE, data_consent=True,
                   consent_date=datetime.utcnow(), join_date=date(2022, 6, 1)),
            Member(member_number='004', first_name='Maria', last_name='Zielińska',
                   email='maria.zielinska@example.com',
                   status=MemberStatus.SUSPENDED, data_consent=True,
                   consent_date=datetime.utcnow(), join_date=date(2019, 9, 20)),
            Member(member_number='005', first_name='Tomasz', last_name='Lewandowski',
                   email='tomasz.lewandowski@example.com', phone='600777888',
                   status=MemberStatus.ACTIVE, data_consent=True,
                   consent_date=datetime.utcnow(), join_date=date(2023, 1, 5)),
        ]
        db.session.add_all(members)
        db.session.flush()
        print('Created sample members.')

        # Create fees for members
        fee_type = FeeType.query.filter_by(name='Składka roczna 2025').first()
        fees = []
        for member in members:
            if member.status == MemberStatus.ACTIVE:
                fee = Fee(
                    member_id=member.id,
                    fee_type_id=fee_type.id,
                    amount=fee_type.amount,
                    due_date=date(2025, 1, 1),
                    status=FeeStatus.PENDING
                )
                fees.append(fee)
        db.session.add_all(fees)
        print('Created sample fees.')

    # Create equipment
    if not Equipment.query.first():
        equipment = [
            Equipment(name='Kajak Baltic 1', type=EquipmentType.KAYAK,
                      status=EquipmentStatus.AVAILABLE, inventory_number='K-001',
                      purchase_date=date(2022, 5, 1)),
            Equipment(name='Kajak Baltic 2', type=EquipmentType.KAYAK,
                      status=EquipmentStatus.AVAILABLE, inventory_number='K-002',
                      purchase_date=date(2022, 5, 1)),
            Equipment(name='SUP Voyager', type=EquipmentType.SUP,
                      status=EquipmentStatus.AVAILABLE, inventory_number='S-001',
                      purchase_date=date(2023, 4, 15)),
            Equipment(name='Żaglówka Omega', type=EquipmentType.SAILBOAT,
                      status=EquipmentStatus.MAINTENANCE, inventory_number='Z-001',
                      purchase_date=date(2018, 6, 1),
                      next_maintenance=date.today() - timedelta(days=30)),
        ]
        db.session.add_all(equipment)
        print('Created sample equipment.')

    # Create events
    if not Event.query.first():
        events = [
            Event(name='Spływ kajakowy Brda', type=EventType.KAYAK_TRIP,
                  description='Weekendowy spływ Brdą dla początkujących i zaawansowanych.',
                  location='Bydgoszcz - Koronowo',
                  start_date=datetime.utcnow() + timedelta(days=30),
                  end_date=datetime.utcnow() + timedelta(days=32),
                  max_participants=15, status=EventStatus.REGISTRATION_OPEN,
                  cost=Decimal('150.00')),
            Event(name='Szkolenie żeglarskie', type=EventType.TRAINING,
                  description='Podstawy żeglarstwa dla nowych członków.',
                  location='Gdynia Marina',
                  start_date=datetime.utcnow() + timedelta(days=14),
                  end_date=datetime.utcnow() + timedelta(days=14, hours=4),
                  max_participants=10, status=EventStatus.REGISTRATION_OPEN),
            Event(name='Zebranie członków', type=EventType.MEETING,
                  description='Coroczne zebranie sprawozdawcze.',
                  location='Klub STW Bałtyk',
                  start_date=datetime.utcnow() + timedelta(days=60),
                  end_date=datetime.utcnow() + timedelta(days=60, hours=3),
                  status=EventStatus.PLANNED),
        ]
        db.session.add_all(events)
        print('Created sample events.')

    db.session.commit()
    print('Demo data seeded successfully.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
