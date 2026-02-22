#!/usr/bin/env python3
"""Flask application entry point."""

import os


def create_app():
    """Application factory for gunicorn."""
    from app import create_app as _create_app
    config_name = os.getenv('FLASK_ENV', 'development')
    return _create_app(config_name)


# For direct execution
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
