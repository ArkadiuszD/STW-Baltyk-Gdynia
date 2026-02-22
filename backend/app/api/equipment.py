from datetime import datetime, date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import and_, or_

from app import db
from app.models import Equipment, Reservation, Member
from app.models.equipment import EquipmentType, EquipmentStatus, ReservationStatus
from app.schemas import (
    EquipmentSchema, EquipmentCreateSchema,
    ReservationSchema, ReservationCreateSchema
)

equipment_bp = Blueprint('equipment', __name__)
equipment_schema = EquipmentSchema()
equipments_schema = EquipmentSchema(many=True)
equipment_create_schema = EquipmentCreateSchema()
reservation_schema = ReservationSchema()
reservations_schema = ReservationSchema(many=True)
reservation_create_schema = ReservationCreateSchema()


def check_write_permission():
    """Check if user has write permission."""
    claims = get_jwt()
    role = claims.get('role')
    return role in ['admin', 'treasurer']


# Equipment endpoints

@equipment_bp.route('', methods=['GET'])
@jwt_required()
def get_equipment():
    """Get all equipment with filtering."""
    equipment_type = request.args.get('type')
    status = request.args.get('status')
    available_only = request.args.get('available', 'false').lower() == 'true'

    query = Equipment.query

    if equipment_type:
        try:
            query = query.filter(Equipment.type == EquipmentType(equipment_type))
        except ValueError:
            pass

    if status:
        try:
            query = query.filter(Equipment.status == EquipmentStatus(status))
        except ValueError:
            pass

    if available_only:
        query = query.filter(Equipment.status == EquipmentStatus.AVAILABLE)

    equipment = query.order_by(Equipment.name).all()
    return jsonify(equipments_schema.dump(equipment)), 200


@equipment_bp.route('/<int:equipment_id>', methods=['GET'])
@jwt_required()
def get_equipment_item(equipment_id):
    """Get single equipment item."""
    equipment = Equipment.query.get_or_404(equipment_id)
    return jsonify(equipment_schema.dump(equipment)), 200


@equipment_bp.route('', methods=['POST'])
@jwt_required()
def create_equipment():
    """Create new equipment."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = equipment_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    equipment = Equipment(
        name=data['name'],
        type=EquipmentType(data['type']),
        status=EquipmentStatus(data.get('status', 'available')),
        description=data.get('description'),
        photo_url=data.get('photo_url'),
        inventory_number=data.get('inventory_number'),
        purchase_date=data.get('purchase_date'),
        last_maintenance=data.get('last_maintenance'),
        next_maintenance=data.get('next_maintenance'),
        notes=data.get('notes')
    )

    db.session.add(equipment)
    db.session.commit()

    return jsonify(equipment_schema.dump(equipment)), 201


@equipment_bp.route('/<int:equipment_id>', methods=['PUT'])
@jwt_required()
def update_equipment(equipment_id):
    """Update equipment."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    equipment = Equipment.query.get_or_404(equipment_id)

    try:
        data = equipment_create_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    for field in ['name', 'description', 'photo_url', 'inventory_number',
                  'purchase_date', 'last_maintenance', 'next_maintenance', 'notes']:
        if field in data:
            setattr(equipment, field, data[field])

    if 'type' in data:
        equipment.type = EquipmentType(data['type'])
    if 'status' in data:
        equipment.status = EquipmentStatus(data['status'])

    db.session.commit()
    return jsonify(equipment_schema.dump(equipment)), 200


@equipment_bp.route('/<int:equipment_id>', methods=['DELETE'])
@jwt_required()
def delete_equipment(equipment_id):
    """Delete equipment (set status to retired)."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Tylko administrator może usuwać sprzęt'}), 403

    equipment = Equipment.query.get_or_404(equipment_id)
    equipment.status = EquipmentStatus.RETIRED
    db.session.commit()

    return jsonify({'message': 'Sprzęt oznaczony jako wycofany'}), 200


@equipment_bp.route('/<int:equipment_id>/reservations', methods=['GET'])
@jwt_required()
def get_equipment_reservations(equipment_id):
    """Get reservations for specific equipment."""
    equipment = Equipment.query.get_or_404(equipment_id)

    # Default: show future and ongoing reservations
    start_from = request.args.get('start_from')
    if start_from:
        try:
            start_from = datetime.fromisoformat(start_from)
        except ValueError:
            start_from = datetime.utcnow()
    else:
        start_from = datetime.utcnow()

    reservations = equipment.reservations.filter(
        Reservation.end_date >= start_from,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    ).order_by(Reservation.start_date).all()

    return jsonify(reservations_schema.dump(reservations)), 200


# Reservations endpoints

@equipment_bp.route('/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    """Get all reservations with filtering."""
    equipment_id = request.args.get('equipment_id', type=int)
    member_id = request.args.get('member_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Reservation.query

    if equipment_id:
        query = query.filter(Reservation.equipment_id == equipment_id)
    if member_id:
        query = query.filter(Reservation.member_id == member_id)
    if status:
        try:
            query = query.filter(Reservation.status == ReservationStatus(status))
        except ValueError:
            pass

    # Date range filter
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Reservation.end_date >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Reservation.start_date <= end_dt)
        except ValueError:
            pass

    reservations = query.order_by(Reservation.start_date).all()
    return jsonify(reservations_schema.dump(reservations)), 200


@equipment_bp.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """Create a new reservation."""
    try:
        data = reservation_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Verify equipment exists and is available
    equipment = Equipment.query.get(data['equipment_id'])
    if not equipment:
        return jsonify({'error': 'Sprzęt nie znaleziony'}), 404

    if equipment.status not in [EquipmentStatus.AVAILABLE, EquipmentStatus.RESERVED]:
        return jsonify({'error': f'Sprzęt niedostępny (status: {equipment.status.value})'}), 400

    # Verify member exists
    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Członek nie znaleziony'}), 404

    # Check for conflicts
    start_date = data['start_date']
    end_date = data['end_date']

    if start_date >= end_date:
        return jsonify({'error': 'Data końcowa musi być późniejsza niż początkowa'}), 400

    conflicts = Reservation.query.filter(
        Reservation.equipment_id == equipment.id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
        or_(
            and_(Reservation.start_date <= start_date, Reservation.end_date > start_date),
            and_(Reservation.start_date < end_date, Reservation.end_date >= end_date),
            and_(Reservation.start_date >= start_date, Reservation.end_date <= end_date)
        )
    ).all()

    if conflicts:
        conflict_dates = [f"{r.start_date.strftime('%Y-%m-%d')} - {r.end_date.strftime('%Y-%m-%d')}"
                         for r in conflicts]
        return jsonify({
            'error': 'Konflikt rezerwacji',
            'conflicts': conflict_dates
        }), 409

    user_id = get_jwt_identity()

    reservation = Reservation(
        equipment_id=equipment.id,
        member_id=member.id,
        start_date=start_date,
        end_date=end_date,
        status=ReservationStatus(data.get('status', 'pending')),
        purpose=data.get('purpose'),
        notes=data.get('notes'),
        created_by_id=user_id
    )

    db.session.add(reservation)
    db.session.commit()

    return jsonify(reservation_schema.dump(reservation)), 201


@equipment_bp.route('/reservations/<int:reservation_id>', methods=['PUT'])
@jwt_required()
def update_reservation(reservation_id):
    """Update a reservation."""
    reservation = Reservation.query.get_or_404(reservation_id)

    try:
        data = reservation_create_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check for conflicts if dates are changing
    if 'start_date' in data or 'end_date' in data:
        start_date = data.get('start_date', reservation.start_date)
        end_date = data.get('end_date', reservation.end_date)

        if start_date >= end_date:
            return jsonify({'error': 'Data końcowa musi być późniejsza niż początkowa'}), 400

        conflicts = Reservation.query.filter(
            Reservation.equipment_id == reservation.equipment_id,
            Reservation.id != reservation.id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            or_(
                and_(Reservation.start_date <= start_date, Reservation.end_date > start_date),
                and_(Reservation.start_date < end_date, Reservation.end_date >= end_date),
                and_(Reservation.start_date >= start_date, Reservation.end_date <= end_date)
            )
        ).all()

        if conflicts:
            return jsonify({'error': 'Konflikt rezerwacji z innymi terminami'}), 409

    for field in ['start_date', 'end_date', 'purpose', 'notes']:
        if field in data:
            setattr(reservation, field, data[field])

    if 'status' in data:
        reservation.status = ReservationStatus(data['status'])

    db.session.commit()
    return jsonify(reservation_schema.dump(reservation)), 200


@equipment_bp.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_reservation(reservation_id):
    """Confirm a pending reservation."""
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.status != ReservationStatus.PENDING:
        return jsonify({'error': f'Nie można potwierdzić rezerwacji o statusie {reservation.status.value}'}), 400

    reservation.status = ReservationStatus.CONFIRMED
    db.session.commit()

    return jsonify(reservation_schema.dump(reservation)), 200


@equipment_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_reservation(reservation_id):
    """Cancel a reservation."""
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.status in [ReservationStatus.COMPLETED, ReservationStatus.CANCELLED]:
        return jsonify({'error': 'Rezerwacja jest już zakończona lub anulowana'}), 400

    reservation.status = ReservationStatus.CANCELLED
    db.session.commit()

    return jsonify(reservation_schema.dump(reservation)), 200


@equipment_bp.route('/reservations/<int:reservation_id>/complete', methods=['POST'])
@jwt_required()
def complete_reservation(reservation_id):
    """Mark reservation as completed."""
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.status != ReservationStatus.CONFIRMED:
        return jsonify({'error': 'Tylko potwierdzone rezerwacje można oznaczyć jako zakończone'}), 400

    reservation.status = ReservationStatus.COMPLETED
    db.session.commit()

    return jsonify(reservation_schema.dump(reservation)), 200


@equipment_bp.route('/maintenance-due', methods=['GET'])
@jwt_required()
def get_maintenance_due():
    """Get equipment that needs maintenance."""
    equipment = Equipment.query.filter(
        Equipment.next_maintenance <= date.today(),
        Equipment.status != EquipmentStatus.RETIRED
    ).all()

    return jsonify(equipments_schema.dump(equipment)), 200


@equipment_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_equipment_stats():
    """Get equipment statistics."""
    total = Equipment.query.filter(Equipment.status != EquipmentStatus.RETIRED).count()

    by_type = db.session.query(
        Equipment.type,
        db.func.count(Equipment.id)
    ).filter(
        Equipment.status != EquipmentStatus.RETIRED
    ).group_by(Equipment.type).all()

    by_status = db.session.query(
        Equipment.status,
        db.func.count(Equipment.id)
    ).group_by(Equipment.status).all()

    # Active reservations
    active_reservations = Reservation.query.filter(
        Reservation.status == ReservationStatus.CONFIRMED,
        Reservation.start_date <= datetime.utcnow(),
        Reservation.end_date >= datetime.utcnow()
    ).count()

    # Upcoming reservations (next 7 days)
    from datetime import timedelta
    upcoming = Reservation.query.filter(
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
        Reservation.start_date > datetime.utcnow(),
        Reservation.start_date <= datetime.utcnow() + timedelta(days=7)
    ).count()

    return jsonify({
        'total': total,
        'by_type': {t.value: c for t, c in by_type},
        'by_status': {s.value: c for s, c in by_status},
        'active_reservations': active_reservations,
        'upcoming_reservations': upcoming
    }), 200
