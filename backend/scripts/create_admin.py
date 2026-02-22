#!/usr/bin/env python3
"""Script to create admin user."""

import os
import sys

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from app import create_app, db
from app.models import User


def create_admin(email, password, first_name, last_name):
    """Create admin user."""
    config_name = os.getenv('FLASK_ENV', 'production')
    app = create_app(config_name)

    with app.app_context():
        # Check if user exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"User {email} already exists.")
            return False

        # Create user
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role='admin',
            is_active=True
        )

        db.session.add(user)
        db.session.commit()

        print(f"✓ Admin user created: {email}")
        return True


if __name__ == '__main__':
    # Default admin credentials
    create_admin(
        email='admin@stwbaltyk.pl',
        password='Admin2026!',
        first_name='Administrator',
        last_name='STW'
    )
