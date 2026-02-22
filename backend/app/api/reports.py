from datetime import date, datetime
from decimal import Decimal
import csv
import io

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt

from app import db
from app.models import Member, Fee, Transaction, Event, EventParticipant
from app.models.member import MemberStatus
from app.models.fee import FeeStatus
from app.models.transaction import TransactionType, TransactionCategory
from app.models.event import EventStatus, ParticipantStatus
from app.models.equipment import EquipmentStatus

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/fees', methods=['GET'])
@jwt_required()
def fees_report():
    """Generate fees report."""
    year = request.args.get('year', date.today().year, type=int)
    format_type = request.args.get('format', 'json')

    # Get all fees for the year with member info
    fees = db.session.query(
        Fee, Member
    ).join(Member).filter(
        db.extract('year', Fee.due_date) == year
    ).order_by(Member.last_name, Fee.due_date).all()

    report_data = []
    for fee, member in fees:
        report_data.append({
            'member_number': member.member_number or '',
            'member_name': member.full_name,
            'member_email': member.email,
            'fee_type': fee.fee_type.name if fee.fee_type else '',
            'amount': float(fee.amount),
            'due_date': fee.due_date.isoformat(),
            'status': fee.status.value,
            'paid_date': fee.paid_date.isoformat() if fee.paid_date else '',
            'days_overdue': fee.days_overdue if fee.is_overdue else 0
        })

    if format_type == 'csv':
        return _generate_csv(report_data, f'skladki_{year}.csv')

    # Summary
    total_amount = sum(f['amount'] for f in report_data)
    paid_amount = sum(f['amount'] for f in report_data if f['status'] == 'paid')
    overdue_amount = sum(f['amount'] for f in report_data if f['status'] in ['pending', 'overdue'] and f['days_overdue'] > 0)

    return jsonify({
        'year': year,
        'items': report_data,
        'summary': {
            'total_count': len(report_data),
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'overdue_amount': overdue_amount,
            'collection_rate': round(paid_amount / total_amount * 100, 1) if total_amount > 0 else 0
        }
    }), 200


@reports_bp.route('/overdue', methods=['GET'])
@jwt_required()
def overdue_report():
    """Generate overdue fees report."""
    format_type = request.args.get('format', 'json')

    # Get all overdue fees
    overdue_fees = db.session.query(
        Fee, Member
    ).join(Member).filter(
        Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE]),
        Fee.due_date < date.today(),
        Member.status == MemberStatus.ACTIVE
    ).order_by(Fee.due_date).all()

    report_data = []
    for fee, member in overdue_fees:
        report_data.append({
            'member_number': member.member_number or '',
            'member_name': member.full_name,
            'email': member.email,
            'phone': member.phone or '',
            'fee_type': fee.fee_type.name if fee.fee_type else '',
            'amount': float(fee.amount),
            'due_date': fee.due_date.isoformat(),
            'days_overdue': (date.today() - fee.due_date).days
        })

    if format_type == 'csv':
        return _generate_csv(report_data, 'zaleglosci.csv')

    return jsonify({
        'generated_at': datetime.utcnow().isoformat(),
        'items': report_data,
        'total_members': len(set(r['member_name'] for r in report_data)),
        'total_amount': sum(r['amount'] for r in report_data)
    }), 200


@reports_bp.route('/members', methods=['GET'])
@jwt_required()
def members_report():
    """Generate members list report."""
    status = request.args.get('status', 'active')
    format_type = request.args.get('format', 'json')

    query = Member.query

    if status != 'all':
        try:
            query = query.filter(Member.status == MemberStatus(status))
        except ValueError:
            pass

    members = query.order_by(Member.last_name, Member.first_name).all()

    report_data = []
    for member in members:
        report_data.append({
            'member_number': member.member_number or '',
            'first_name': member.first_name,
            'last_name': member.last_name,
            'email': member.email,
            'phone': member.phone or '',
            'join_date': member.join_date.isoformat() if member.join_date else '',
            'status': member.status.value,
            'total_debt': float(member.total_debt)
        })

    if format_type == 'csv':
        return _generate_csv(report_data, f'czlonkowie_{status}.csv')

    return jsonify({
        'status': status,
        'items': report_data,
        'total': len(report_data)
    }), 200


@reports_bp.route('/finance', methods=['GET'])
@jwt_required()
def finance_report():
    """Generate finance report (simplified bookkeeping)."""
    year = request.args.get('year', date.today().year, type=int)
    format_type = request.args.get('format', 'json')

    # All transactions for the year
    transactions = Transaction.query.filter(
        db.extract('year', Transaction.date) == year
    ).order_by(Transaction.date).all()

    report_data = []
    for tx in transactions:
        report_data.append({
            'date': tx.date.isoformat(),
            'type': 'Przychód' if tx.type == TransactionType.INCOME else 'Koszt',
            'category': _translate_category(tx.category),
            'description': tx.description,
            'counterparty': tx.counterparty or '',
            'amount': float(tx.amount) if tx.type == TransactionType.INCOME else -float(tx.amount),
            'bank_reference': tx.bank_reference or ''
        })

    if format_type == 'csv':
        return _generate_csv(report_data, f'ewidencja_{year}.csv')

    # Summary by category
    income_by_cat = {}
    expense_by_cat = {}

    for tx in transactions:
        cat_name = _translate_category(tx.category)
        if tx.type == TransactionType.INCOME:
            income_by_cat[cat_name] = income_by_cat.get(cat_name, 0) + float(tx.amount)
        else:
            expense_by_cat[cat_name] = expense_by_cat.get(cat_name, 0) + float(tx.amount)

    total_income = sum(income_by_cat.values())
    total_expense = sum(expense_by_cat.values())

    return jsonify({
        'year': year,
        'items': report_data,
        'summary': {
            'income_by_category': income_by_cat,
            'expense_by_category': expense_by_cat,
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': total_income - total_expense
        }
    }), 200


@reports_bp.route('/events', methods=['GET'])
@jwt_required()
def events_report():
    """Generate events report."""
    year = request.args.get('year', date.today().year, type=int)
    format_type = request.args.get('format', 'json')

    events = Event.query.filter(
        db.extract('year', Event.start_date) == year
    ).order_by(Event.start_date).all()

    report_data = []
    for event in events:
        participants = EventParticipant.query.filter_by(
            event_id=event.id
        ).filter(
            EventParticipant.status.in_([ParticipantStatus.REGISTERED, ParticipantStatus.CONFIRMED])
        ).count()

        report_data.append({
            'name': event.name,
            'type': _translate_event_type(event.type),
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'location': event.location or '',
            'status': _translate_event_status(event.status),
            'max_participants': event.max_participants or 'bez limitu',
            'registered': participants,
            'cost': float(event.cost) if event.cost else 0
        })

    if format_type == 'csv':
        return _generate_csv(report_data, f'wydarzenia_{year}.csv')

    return jsonify({
        'year': year,
        'items': report_data,
        'total_events': len(report_data),
        'completed': sum(1 for e in events if e.status == EventStatus.COMPLETED)
    }), 200


@reports_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_data():
    """Get dashboard summary data."""
    today = date.today()
    current_year = today.year

    # Members stats
    active_members = Member.query.filter_by(status=MemberStatus.ACTIVE).count()

    # Fees stats
    overdue_fees_count = Fee.query.filter(
        Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE]),
        Fee.due_date < today
    ).count()

    overdue_amount = db.session.query(db.func.sum(Fee.amount)).filter(
        Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE]),
        Fee.due_date < today
    ).scalar() or 0

    # Finance - current year
    year_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.INCOME,
        db.extract('year', Transaction.date) == current_year
    ).scalar() or 0

    year_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.EXPENSE,
        db.extract('year', Transaction.date) == current_year
    ).scalar() or 0

    # Upcoming events (next 30 days)
    from datetime import timedelta
    upcoming_events = Event.query.filter(
        Event.start_date >= datetime.utcnow(),
        Event.start_date <= datetime.utcnow() + timedelta(days=30),
        Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
    ).order_by(Event.start_date).limit(5).all()

    # Equipment needing maintenance
    from app.models import Equipment
    maintenance_due = Equipment.query.filter(
        Equipment.next_maintenance <= today,
        Equipment.status != EquipmentStatus.RETIRED
    ).count()

    return jsonify({
        'members': {
            'active': active_members
        },
        'fees': {
            'overdue_count': overdue_fees_count,
            'overdue_amount': float(overdue_amount)
        },
        'finance': {
            'year': current_year,
            'income': float(year_income),
            'expense': float(year_expense),
            'balance': float(year_income - year_expense)
        },
        'upcoming_events': [{
            'id': e.id,
            'name': e.name,
            'date': e.start_date.isoformat(),
            'registered': e.registered_count
        } for e in upcoming_events],
        'maintenance_due': maintenance_due
    }), 200


def _generate_csv(data: list, filename: str):
    """Generate CSV file response."""
    if not data:
        return jsonify({'error': 'Brak danych do eksportu'}), 404

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def _translate_category(category):
    """Translate category enum to Polish."""
    translations = {
        TransactionCategory.FEES: 'Składki',
        TransactionCategory.DONATIONS: 'Darowizny',
        TransactionCategory.GRANTS: 'Dotacje',
        TransactionCategory.OTHER_INCOME: 'Inne przychody',
        TransactionCategory.ADMINISTRATION: 'Administracja',
        TransactionCategory.STATUTORY_ACTIVITIES: 'Działalność statutowa',
        TransactionCategory.EQUIPMENT: 'Sprzęt',
        TransactionCategory.EVENTS: 'Imprezy/rejsy',
        TransactionCategory.OTHER_EXPENSE: 'Inne koszty'
    }
    return translations.get(category, str(category))


def _translate_event_type(event_type):
    """Translate event type to Polish."""
    from app.models.event import EventType
    translations = {
        EventType.CRUISE: 'Rejs',
        EventType.KAYAK_TRIP: 'Spływ kajakowy',
        EventType.TRAINING: 'Szkolenie',
        EventType.MEETING: 'Spotkanie',
        EventType.OTHER: 'Inne'
    }
    return translations.get(event_type, str(event_type))


def _translate_event_status(status):
    """Translate event status to Polish."""
    translations = {
        EventStatus.PLANNED: 'Planowane',
        EventStatus.REGISTRATION_OPEN: 'Zapisy otwarte',
        EventStatus.FULL: 'Komplet',
        EventStatus.ONGOING: 'W trakcie',
        EventStatus.COMPLETED: 'Zakończone',
        EventStatus.CANCELLED: 'Anulowane'
    }
    return translations.get(status, str(status))
