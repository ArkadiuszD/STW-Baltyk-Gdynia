"""
Members API endpoints.

Uses:
- MemberService for business logic
- Decorators for authorization
- Response helpers for consistent API responses
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app.schemas import MemberSchema, MemberCreateSchema, MemberUpdateSchema
from app.services.member_service import member_service
from app.utils.decorators import admin_required, write_permission_required
from app.utils.responses import success, created, error, validation_error, conflict, paginated

members_bp = Blueprint('members', __name__)

# Schema instances
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
member_create_schema = MemberCreateSchema()
member_update_schema = MemberUpdateSchema()


@members_bp.route('', methods=['GET'])
@jwt_required()
def get_members():
    """Get all members with optional filtering and pagination."""
    # Query parameters
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Build filters
    filters = {}
    if status:
        filters['status'] = status

    # Get paginated results
    result = member_service.get_all(
        page=page,
        per_page=per_page,
        search=search,
        filters=filters
    )

    return paginated(
        items=result.items,
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        schema=members_schema
    )


@members_bp.route('/<int:member_id>', methods=['GET'])
@jwt_required()
def get_member(member_id):
    """Get single member by ID."""
    member = member_service.get_or_404(member_id)
    return success(member_schema.dump(member))


@members_bp.route('', methods=['POST'])
@jwt_required()
@write_permission_required
def create_member():
    """Create a new member."""
    try:
        data = member_create_schema.load(request.json)
    except ValidationError as err:
        return validation_error(err.messages)

    try:
        member = member_service.create(data)
    except ValueError as e:
        return conflict(str(e))

    return created(member_schema.dump(member))


@members_bp.route('/<int:member_id>', methods=['PUT'])
@jwt_required()
@write_permission_required
def update_member(member_id):
    """Update an existing member."""
    try:
        data = member_update_schema.load(request.json)
    except ValidationError as err:
        return validation_error(err.messages)

    try:
        member = member_service.update(member_id, data)
    except ValueError as e:
        return conflict(str(e))

    return success(member_schema.dump(member))


@members_bp.route('/<int:member_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_member(member_id):
    """Delete a member (soft delete - change status to 'former')."""
    member_service.deactivate(member_id)
    return success(message='Członek oznaczony jako były')


@members_bp.route('/<int:member_id>/fees', methods=['GET'])
@jwt_required()
def get_member_fees(member_id):
    """Get all fees for a specific member."""
    from app import db
    from app.schemas import FeeSchema
    fees_schema = FeeSchema(many=True)

    member = member_service.get_or_404(member_id)
    fees = member.fees.order_by(db.desc('due_date')).all()

    return success(fees_schema.dump(fees))


@members_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_member_stats():
    """Get member statistics."""
    stats = member_service.get_stats()
    return success(stats)
