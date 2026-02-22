from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
    set_refresh_cookies,
    unset_jwt_cookies
)
from marshmallow import ValidationError

from app import db
from app.models import User
from app.models.user import UserRole
from app.schemas import UserSchema, UserCreateSchema, LoginSchema

auth_bp = Blueprint('auth', __name__)
user_schema = UserSchema()
user_create_schema = UserCreateSchema()
login_schema = LoginSchema()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens."""
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Nieprawidłowy email lub hasło'}), 401

    if not user.is_active:
        return jsonify({'error': 'Konto jest nieaktywne'}), 403

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Create tokens - identity must be a string
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role.value}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    response = jsonify({
        'access_token': access_token,
        'user': user_schema.dump(user)
    })
    set_refresh_cookies(response, refresh_token)
    return response, 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_active:
        return jsonify({'error': 'Użytkownik nieaktywny'}), 403

    access_token = create_access_token(
        identity=user_id,
        additional_claims={'role': user.role.value}
    )
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear JWT cookies."""
    response = jsonify({'message': 'Wylogowano pomyślnie'})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Użytkownik nie znaleziony'}), 404
    return jsonify(user_schema.dump(user)), 200


@auth_bp.route('/register', methods=['POST'])
@jwt_required()
def register_user():
    """Register new user (admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': 'Brak uprawnień'}), 403

    try:
        data = user_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email już istnieje w systemie'}), 409

    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=UserRole(data.get('role', 'board')),
        member_id=data.get('member_id')
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify(user_schema.dump(user)), 201


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user's password."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Wymagane aktualne i nowe hasło'}), 400

    if not user.check_password(current_password):
        return jsonify({'error': 'Nieprawidłowe aktualne hasło'}), 401

    if len(new_password) < 8:
        return jsonify({'error': 'Nowe hasło musi mieć minimum 8 znaków'}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Hasło zmienione pomyślnie'}), 200
