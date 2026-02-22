from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_marshmallow import Marshmallow

import sys
import os

# Ensure we import config.py from parent directory, not app/config/
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _backend_dir)

# Import config dict from config.py
import importlib.util
_spec = importlib.util.spec_from_file_location("config_module", os.path.join(_backend_dir, "config.py"))
_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config_module)
config = _config_module.config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # CORS
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.members import members_bp
    from app.api.fees import fees_bp
    from app.api.finance import finance_bp
    from app.api.equipment import equipment_bp
    from app.api.events import events_bp
    from app.api.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(members_bp, url_prefix='/api/members')
    app.register_blueprint(fees_bp, url_prefix='/api/fees')
    app.register_blueprint(finance_bp, url_prefix='/api/finance')
    app.register_blueprint(equipment_bp, url_prefix='/api/equipment')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token wygasł', 'code': 'token_expired'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Nieprawidłowy token', 'code': 'invalid_token'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Brak tokenu autoryzacji', 'code': 'missing_token'}, 401

    # Health check endpoint
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'app': 'STW Bałtyk Gdynia'}

    return app
