from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import ValidationError
from sqlalchemy import or_

from app import db
from app.models import Member
from app.models.member import MemberStatus
from app.schemas import MemberSchema, MemberCreateSchema, MemberUpdateSchema

members_bp = Blueprint('members', __name__)
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
member_create_schema = MemberCreateSchema()
member_update_schema = MemberUpdateSchema()


def check_write_permission():
    """Check if user has write permission (admin or treasurer)."""
    claims = get_jwt()
    role = claims.get('role')
    return role in ['admin', 'treasurer']


@members_bp.route('', methods=['GET'])
@jwt_required()
def get_members():
    """Get all members with optional filtering."""
    # Query parameters
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Member.query

    # Filter by status
    if status:
        try:
            query = query.filter(Member.status == MemberStatus(status))
        except ValueError:
            pass

    # Search by name or email
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Member.first_name.ilike(search_term),
                Member.last_name.ilike(search_term),
                Member.email.ilike(search_term),
                Member.member_number.ilike(search_term)
            )
        )

    # Order by last name
    query = query.order_by(Member.last_name, Member.first_name)

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': members_schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    }), 200


@members_bp.route('/<int:member_id>', methods=['GET'])
@jwt_required()
def get_member(member_id):
    """Get single member by ID."""
    member = Member.query.get_or_404(member_id)
    return jsonify(member_schema.dump(member)), 200


@members_bp.route('', methods=['POST'])
@jwt_required()
def create_member():
    """Create a new member."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień do dodawania członków'}), 403

    try:
        data = member_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check for duplicate email
    if Member.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email już istnieje w systemie'}), 409

    # Check for duplicate member number
    if data.get('member_number'):
        if Member.query.filter_by(member_number=data['member_number']).first():
            return jsonify({'error': 'Numer członkowski już istnieje'}), 409

    member = Member(
        member_number=data.get('member_number'),
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data.get('phone'),
        address=data.get('address'),
        join_date=data.get('join_date'),
        status=MemberStatus(data.get('status', 'active')),
        notes=data.get('notes'),
        data_consent=data.get('data_consent', False)
    )

    if member.data_consent:
        member.consent_date = datetime.utcnow()

    db.session.add(member)
    db.session.commit()

    return jsonify(member_schema.dump(member)), 201


@members_bp.route('/<int:member_id>', methods=['PUT'])
@jwt_required()
def update_member(member_id):
    """Update an existing member."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień do edycji członków'}), 403

    member = Member.query.get_or_404(member_id)

    try:
        data = member_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check for duplicate email (if changed)
    if 'email' in data and data['email'] != member.email:
        if Member.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email już istnieje w systemie'}), 409

    # Check for duplicate member number (if changed)
    if 'member_number' in data and data['member_number'] != member.member_number:
        if Member.query.filter_by(member_number=data['member_number']).first():
            return jsonify({'error': 'Numer członkowski już istnieje'}), 409

    # Update fields
    for field in ['member_number', 'first_name', 'last_name', 'email', 'phone',
                  'address', 'notes']:
        if field in data:
            setattr(member, field, data[field])

    if 'status' in data:
        member.status = MemberStatus(data['status'])

    # Handle RODO consent
    if 'data_consent' in data:
        if data['data_consent'] and not member.data_consent:
            member.consent_date = datetime.utcnow()
        member.data_consent = data['data_consent']

    db.session.commit()

    return jsonify(member_schema.dump(member)), 200


@members_bp.route('/<int:member_id>', methods=['DELETE'])
@jwt_required()
def delete_member(member_id):
    """Delete a member (soft delete - change status to 'former')."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Tylko administrator może usuwać członków'}), 403

    member = Member.query.get_or_404(member_id)
    member.status = MemberStatus.FORMER
    db.session.commit()

    return jsonify({'message': 'Członek oznaczony jako były'}), 200


@members_bp.route('/<int:member_id>/fees', methods=['GET'])
@jwt_required()
def get_member_fees(member_id):
    """Get all fees for a specific member."""
    from app.schemas import FeeSchema
    fees_schema = FeeSchema(many=True)

    member = Member.query.get_or_404(member_id)
    fees = member.fees.order_by(db.desc('due_date')).all()

    return jsonify(fees_schema.dump(fees)), 200


@members_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_member_stats():
    """Get member statistics."""
    total = Member.query.count()
    active = Member.query.filter_by(status=MemberStatus.ACTIVE).count()
    suspended = Member.query.filter_by(status=MemberStatus.SUSPENDED).count()
    former = Member.query.filter_by(status=MemberStatus.FORMER).count()

    # Members with debt
    from app.models.fee import FeeStatus
    from app.models import Fee
    members_with_debt = db.session.query(Fee.member_id).filter(
        Fee.status.in_([FeeStatus.PENDING, FeeStatus.OVERDUE])
    ).distinct().count()

    return jsonify({
        'total': total,
        'active': active,
        'suspended': suspended,
        'former': former,
        'with_debt': members_with_debt
    }), 200
