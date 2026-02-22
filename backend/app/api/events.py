from datetime import datetime, date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.models import Event, EventParticipant, Member
from app.models.event import EventType, EventStatus, ParticipantStatus
from app.models.member import MemberStatus
from app.schemas import (
    EventSchema, EventCreateSchema,
    EventParticipantSchema, EventParticipantCreateSchema
)

events_bp = Blueprint('events', __name__)
event_schema = EventSchema()
events_schema = EventSchema(many=True, exclude=['participants'])
event_detail_schema = EventSchema()
event_create_schema = EventCreateSchema()
participant_schema = EventParticipantSchema()
participants_schema = EventParticipantSchema(many=True)
participant_create_schema = EventParticipantCreateSchema()


def check_write_permission():
    """Check if user has write permission."""
    claims = get_jwt()
    role = claims.get('role')
    return role in ['admin', 'treasurer']


@events_bp.route('', methods=['GET'])
@jwt_required()
def get_events():
    """Get all events with filtering."""
    event_type = request.args.get('type')
    status = request.args.get('status')
    upcoming_only = request.args.get('upcoming', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Event.query

    if event_type:
        try:
            query = query.filter(Event.type == EventType(event_type))
        except ValueError:
            pass

    if status:
        try:
            query = query.filter(Event.status == EventStatus(status))
        except ValueError:
            pass

    if upcoming_only:
        query = query.filter(
            Event.start_date >= datetime.utcnow(),
            Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
        )

    query = query.order_by(Event.start_date)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': events_schema.dump(pagination.items),
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@events_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    """Get single event with participants."""
    event = Event.query.get_or_404(event_id)
    return jsonify(event_detail_schema.dump(event)), 200


@events_bp.route('', methods=['POST'])
@jwt_required()
def create_event():
    """Create a new event."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = event_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    user_id = get_jwt_identity()

    event = Event(
        name=data['name'],
        type=EventType(data['type']),
        description=data.get('description'),
        location=data.get('location'),
        start_date=data['start_date'],
        end_date=data['end_date'],
        registration_deadline=data.get('registration_deadline'),
        max_participants=data.get('max_participants'),
        status=EventStatus(data.get('status', 'planned')),
        cost=data.get('cost'),
        notes=data.get('notes'),
        created_by_id=user_id
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event_schema.dump(event)), 201


@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """Update an event."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    event = Event.query.get_or_404(event_id)

    try:
        data = event_create_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    for field in ['name', 'description', 'location', 'start_date', 'end_date',
                  'registration_deadline', 'max_participants', 'cost', 'notes']:
        if field in data:
            setattr(event, field, data[field])

    if 'type' in data:
        event.type = EventType(data['type'])
    if 'status' in data:
        event.status = EventStatus(data['status'])

    # Update status to 'full' if max reached
    if event.max_participants and event.registered_count >= event.max_participants:
        if event.status == EventStatus.REGISTRATION_OPEN:
            event.status = EventStatus.FULL

    db.session.commit()
    return jsonify(event_schema.dump(event)), 200


@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """Cancel an event."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Tylko administrator może anulować wydarzenia'}), 403

    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.CANCELLED
    db.session.commit()

    return jsonify({'message': 'Wydarzenie anulowane'}), 200


# Participants endpoints

@events_bp.route('/<int:event_id>/participants', methods=['GET'])
@jwt_required()
def get_participants(event_id):
    """Get all participants for an event."""
    event = Event.query.get_or_404(event_id)

    status = request.args.get('status')
    query = event.participants

    if status:
        try:
            query = query.filter(EventParticipant.status == ParticipantStatus(status))
        except ValueError:
            pass

    participants = query.order_by(EventParticipant.registered_at).all()
    return jsonify(participants_schema.dump(participants)), 200


@events_bp.route('/<int:event_id>/participants', methods=['POST'])
@jwt_required()
def register_participant(event_id):
    """Register a member for an event."""
    event = Event.query.get_or_404(event_id)

    try:
        data = participant_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check if event allows registration
    if not event.is_registration_open and event.status != EventStatus.PLANNED:
        return jsonify({'error': 'Rejestracja na to wydarzenie jest zamknięta'}), 400

    # Verify member exists and is active
    member = Member.query.get(data['member_id'])
    if not member:
        return jsonify({'error': 'Członek nie znaleziony'}), 404
    if member.status != MemberStatus.ACTIVE:
        return jsonify({'error': 'Tylko aktywni członkowie mogą się rejestrować'}), 400

    # Check if already registered
    existing = EventParticipant.query.filter_by(
        event_id=event_id,
        member_id=member.id
    ).first()

    if existing:
        if existing.status == ParticipantStatus.CANCELLED:
            # Re-register cancelled participant
            existing.status = ParticipantStatus.REGISTERED if not event.is_full else ParticipantStatus.WAITLIST
            existing.registered_at = datetime.utcnow()
            existing.notes = data.get('notes')
            db.session.commit()
            return jsonify(participant_schema.dump(existing)), 200
        else:
            return jsonify({'error': 'Członek jest już zapisany na to wydarzenie'}), 409

    # Determine status based on availability
    if event.is_full:
        status = ParticipantStatus.WAITLIST
    else:
        status = ParticipantStatus.REGISTERED

    participant = EventParticipant(
        event_id=event_id,
        member_id=member.id,
        status=status,
        notes=data.get('notes')
    )

    db.session.add(participant)

    # Update event status if now full
    if event.max_participants and event.registered_count + 1 >= event.max_participants:
        if event.status == EventStatus.REGISTRATION_OPEN:
            event.status = EventStatus.FULL

    db.session.commit()

    return jsonify(participant_schema.dump(participant)), 201


@events_bp.route('/<int:event_id>/participants/<int:participant_id>', methods=['PUT'])
@jwt_required()
def update_participant(event_id, participant_id):
    """Update participant status."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    participant = EventParticipant.query.filter_by(
        id=participant_id,
        event_id=event_id
    ).first_or_404()

    data = request.json

    if 'status' in data:
        try:
            participant.status = ParticipantStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Nieprawidłowy status'}), 400

    if 'notes' in data:
        participant.notes = data['notes']

    db.session.commit()
    return jsonify(participant_schema.dump(participant)), 200


@events_bp.route('/<int:event_id>/participants/<int:participant_id>', methods=['DELETE'])
@jwt_required()
def cancel_participation(event_id, participant_id):
    """Cancel participation (member or admin)."""
    participant = EventParticipant.query.filter_by(
        id=participant_id,
        event_id=event_id
    ).first_or_404()

    # Check permission - admin or the member themselves via their user account
    claims = get_jwt()
    user_id = get_jwt_identity()

    from app.models import User
    user = User.query.get(user_id)

    is_admin = claims.get('role') == 'admin'
    is_own = user and user.member_id == participant.member_id

    if not is_admin and not is_own:
        return jsonify({'error': 'Brak uprawnień do anulowania tej rejestracji'}), 403

    participant.status = ParticipantStatus.CANCELLED

    # If someone from waitlist, move them to registered
    event = Event.query.get(event_id)
    if event.max_participants:
        waitlist = EventParticipant.query.filter_by(
            event_id=event_id,
            status=ParticipantStatus.WAITLIST
        ).order_by(EventParticipant.registered_at).first()

        if waitlist:
            waitlist.status = ParticipantStatus.REGISTERED

    # Update event status
    if event.status == EventStatus.FULL and event.spots_available > 0:
        event.status = EventStatus.REGISTRATION_OPEN

    db.session.commit()

    return jsonify({'message': 'Rejestracja anulowana'}), 200


@events_bp.route('/<int:event_id>/open-registration', methods=['POST'])
@jwt_required()
def open_registration(event_id):
    """Open registration for an event."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    event = Event.query.get_or_404(event_id)

    if event.status not in [EventStatus.PLANNED, EventStatus.FULL]:
        return jsonify({'error': f'Nie można otworzyć rejestracji dla statusu {event.status.value}'}), 400

    event.status = EventStatus.FULL if event.is_full else EventStatus.REGISTRATION_OPEN
    db.session.commit()

    return jsonify(event_schema.dump(event)), 200


@events_bp.route('/<int:event_id>/close-registration', methods=['POST'])
@jwt_required()
def close_registration(event_id):
    """Close registration for an event."""
    if not check_write_permission():
        return jsonify({'error': 'Brak uprawnień'}), 403

    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.PLANNED
    db.session.commit()

    return jsonify(event_schema.dump(event)), 200


@events_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_event_stats():
    """Get event statistics."""
    year = request.args.get('year', date.today().year, type=int)

    # Events count by type
    by_type = db.session.query(
        Event.type,
        db.func.count(Event.id)
    ).filter(
        db.extract('year', Event.start_date) == year
    ).group_by(Event.type).all()

    # Events count by status
    by_status = db.session.query(
        Event.status,
        db.func.count(Event.id)
    ).filter(
        db.extract('year', Event.start_date) == year
    ).group_by(Event.status).all()

    # Total participants this year
    total_participants = db.session.query(db.func.count(EventParticipant.id)).join(Event).filter(
        db.extract('year', Event.start_date) == year,
        EventParticipant.status.in_([ParticipantStatus.REGISTERED, ParticipantStatus.CONFIRMED])
    ).scalar() or 0

    # Upcoming events
    upcoming = Event.query.filter(
        Event.start_date >= datetime.utcnow(),
        Event.status.notin_([EventStatus.COMPLETED, EventStatus.CANCELLED])
    ).count()

    return jsonify({
        'year': year,
        'by_type': {t.value: c for t, c in by_type},
        'by_status': {s.value: c for s, c in by_status},
        'total_participants': total_participants,
        'upcoming': upcoming
    }), 200
