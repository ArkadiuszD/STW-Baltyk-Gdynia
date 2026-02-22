from datetime import date
from decimal import Decimal

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import ValidationError
from sqlalchemy import or_

from app import db
from app.models import Fee, FeeType, Member
from app.models.fee import FeeStatus, FeeFrequency
from app.models.member import MemberStatus
from app.schemas import FeeSchema, FeeCreateSchema, FeeTypeSchema, FeeTypeCreateSchema
from app.config.finance_config import (
    get_all_default_fees, STATUS_LABELS, ALERTS, format_currency
)

fees_bp = Blueprint('fees', __name__)
fee_schema = FeeSchema()
fees_schema = FeeSchema(many=True)
fee_create_schema = FeeCreateSchema()
fee_type_schema = FeeTypeSchema()
fee_types_schema = FeeTypeSchema(many=True)
fee_type_create_schema = FeeTypeCreateSchema()


def check_write_permission():
    """Check if user has write permission (admin or treasurer)."""
    claims = get_jwt()
    role = claims.get('role')
    return role in ['admin', 'treasurer']


# Fee Types endpoints

@fees_bp.route('/types', methods=['GET'])
@jwt_required()
def get_fee_types():
    """Get all fee types."""
    active_only = request.args.get('active', 'true').lower() == 'true'

    query = FeeType.query
    if active_only:
        query = query.filter_by(is_active=True)

    fee_types = query.order_by(FeeType.name).all()
    return jsonify(fee_types_schema.dump(fee_types)), 200


@fees_bp.route('/types', methods=['POST'])
@jwt_required()
def create_fee_type():
    """Create a new fee type."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = fee_type_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    fee_type = FeeType(
        name=data['name'],
        amount=Decimal(str(data['amount'])),
        frequency=FeeFrequency(data['frequency']),
        due_day=data.get('due_day'),
        due_month=data.get('due_month'),
        is_active=data.get('is_active', True),
        description=data.get('description')
    )

    db.session.add(fee_type)
    db.session.commit()

    return jsonify(fee_type_schema.dump(fee_type)), 201


@fees_bp.route('/types/<int:fee_type_id>', methods=['PUT'])
@jwt_required()
def update_fee_type(fee_type_id):
    """Update a fee type."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    fee_type = FeeType.query.get_or_404(fee_type_id)

    try:
        data = fee_type_create_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    for field in ['name', 'description', 'due_day', 'due_month', 'is_active']:
        if field in data:
            setattr(fee_type, field, data[field])

    if 'amount' in data:
        fee_type.amount = Decimal(str(data['amount']))
    if 'frequency' in data:
        fee_type.frequency = FeeFrequency(data['frequency'])

    db.session.commit()
    return jsonify(fee_type_schema.dump(fee_type)), 200


# Fees endpoints

@fees_bp.route('', methods=['GET'])
@jwt_required()
def get_fees():
    """Get all fees with filtering."""
    status = request.args.get('status')
    member_id = request.args.get('member_id', type=int)
    year = request.args.get('year', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Fee.query.join(Member)

    # Filter by status
    if status:
        try:
            query = query.filter(Fee.status == FeeStatus(status))
        except ValueError:
            pass

    # Filter by member
    if member_id:
        query = query.filter(Fee.member_id == member_id)

    # Filter by year
    if year:
        query = query.filter(db.extract('year', Fee.due_date) == year)

    # Order by due date descending
    query = query.order_by(db.desc(Fee.due_date))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': fees_schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@fees_bp.route('/overdue', methods=['GET'])
@jwt_required()
def get_overdue_fees():
    """Get all overdue fees."""
    query = Fee.query.join(Member).filter(
        Fee.status == FeeStatus.PENDING,
        Fee.due_date < date.today(),
        Member.status == MemberStatus.ACTIVE
    ).order_by(Fee.due_date)

    fees = query.all()

    # Update status to overdue if still pending
    for fee in fees:
        if fee.status == FeeStatus.PENDING:
            fee.status = FeeStatus.OVERDUE

    db.session.commit()

    return jsonify(fees_schema.dump(fees)), 200


@fees_bp.route('', methods=['POST'])
@jwt_required()
def create_fee():
    """Create a single fee for a member."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = fee_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verify member and fee type exist
    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Członek nie znaleziony'}), 404

    fee_type = FeeType.query.get(data['fee_type_id'])
    if not fee_type:
        return jsonify({'error': 'Typ składki nie znaleziony'}), 404

    fee = Fee(
        member_id=data['member_id'],
        fee_type_id=data['fee_type_id'],
        amount=Decimal(str(data['amount'])),
        due_date=data['due_date'],
        status=FeeStatus(data.get('status', 'pending')),
        notes=data.get('notes')
    )

    db.session.add(fee)
    db.session.commit()

    return jsonify(fee_schema.dump(fee)), 201


@fees_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_fees():
    """Generate fees for all active members based on fee type."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    data = request.json
    fee_type_id = data.get('fee_type_id')
    due_date = data.get('due_date')

    if not fee_type_id or not due_date:
        return jsonify({'error': 'Wymagane: fee_type_id i due_date'}), 400

    fee_type = FeeType.query.get(fee_type_id)
    if not fee_type:
        return jsonify({'error': 'Typ składki nie znaleziony'}), 404

    # Parse due date
    try:
        due_date = date.fromisoformat(due_date)
    except ValueError:
        return jsonify({'error': 'Nieprawidłowy format daty (YYYY-MM-DD)'}), 400

    # Get all active members
    active_members = Member.query.filter_by(status=MemberStatus.ACTIVE).all()

    created_count = 0
    skipped_count = 0

    for member in active_members:
        # Check if fee already exists for this member/type/date
        existing = Fee.query.filter_by(
            member_id=member.id,
            fee_type_id=fee_type_id,
            due_date=due_date
        ).first()

        if existing:
            skipped_count += 1
            continue

        fee = Fee(
            member_id=member.id,
            fee_type_id=fee_type_id,
            amount=fee_type.amount,
            due_date=due_date,
            status=FeeStatus.PENDING
        )
        db.session.add(fee)
        created_count += 1

    db.session.commit()

    return jsonify({
        'message': f'Wygenerowano {created_count} składek',
        'created': created_count,
        'skipped': skipped_count
    }), 201


@fees_bp.route('/<int:fee_id>', methods=['PUT'])
@jwt_required()
def update_fee(fee_id):
    """Update a fee."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    fee = Fee.query.get_or_404(fee_id)
    data = request.json

    if 'status' in data:
        try:
            fee.status = FeeStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Nieprawidłowy status'}), 400

    if 'paid_date' in data:
        fee.paid_date = date.fromisoformat(data['paid_date']) if data['paid_date'] else None

    if 'amount' in data:
        fee.amount = Decimal(str(data['amount']))

    if 'notes' in data:
        fee.notes = data['notes']

    db.session.commit()
    return jsonify(fee_schema.dump(fee)), 200


@fees_bp.route('/<int:fee_id>/mark-paid', methods=['POST'])
@jwt_required()
def mark_fee_paid(fee_id):
    """Mark a fee as paid."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    fee = Fee.query.get_or_404(fee_id)
    data = request.json or {}

    paid_date = data.get('paid_date')
    if paid_date:
        try:
            paid_date = date.fromisoformat(paid_date)
        except ValueError:
            return jsonify({'error': 'Nieprawidłowy format daty'}), 400
    else:
        paid_date = date.today()

    fee.mark_as_paid(
        paid_date=paid_date,
        transaction_id=data.get('transaction_id')
    )
    db.session.commit()

    return jsonify(fee_schema.dump(fee)), 200


@fees_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_fee_stats():
    """Get fee statistics."""
    year = request.args.get('year', date.today().year, type=int)

    # Fees for given year
    year_fees = Fee.query.filter(
        db.extract('year', Fee.due_date) == year
    )

    total_count = year_fees.count()
    paid_count = year_fees.filter(Fee.status == FeeStatus.PAID).count()
    pending_count = year_fees.filter(Fee.status == FeeStatus.PENDING).count()
    overdue_count = year_fees.filter(Fee.status == FeeStatus.OVERDUE).count()

    # Amounts
    total_amount = db.session.query(db.func.sum(Fee.amount)).filter(
        db.extract('year', Fee.due_date) == year
    ).scalar() or 0

    paid_amount = db.session.query(db.func.sum(Fee.amount)).filter(
        db.extract('year', Fee.due_date) == year,
        Fee.status == FeeStatus.PAID
    ).scalar() or 0

    overdue_amount = db.session.query(db.func.sum(Fee.amount)).filter(
        Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE]),
        Fee.due_date < date.today()
    ).scalar() or 0

    return jsonify({
        'year': year,
        'total_count': total_count,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'total_amount': float(total_amount),
        'paid_amount': float(paid_amount),
        'overdue_amount': float(overdue_amount),
        'collection_rate': round(paid_count / total_count * 100, 1) if total_count > 0 else 0
    }), 200


@fees_bp.route('/config/defaults', methods=['GET'])
@jwt_required()
def get_default_fees_config():
    """Get default fee configurations from finance config."""
    return jsonify({
        'fees': get_all_default_fees(),
        'status_labels': STATUS_LABELS.get('fee', {}),
        'alerts': {
            'reminder_days_before': ALERTS.get('fee_reminder_days_before', 7),
            'first_warning_days': ALERTS.get('fee_first_warning_days', 14),
            'second_warning_days': ALERTS.get('fee_second_warning_days', 30),
            'suspension_days': ALERTS.get('fee_suspension_days', 60),
        }
    }), 200
