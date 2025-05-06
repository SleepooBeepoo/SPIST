from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.models import db
from app.services.config_service import ConfigService
from app.services.error_service import ErrorService
from app.services.logging_service import LoggingService
import os
import logging

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Application factory function to create and configure the Flask app"""
    # Create Flask app
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        print(f"Created instance directory: {instance_path}")
    
    # Load configuration from service
    app.config.update(ConfigService.get_config())
    
    # Set up logging
    LoggingService.setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Set login view
    login_manager.login_view = 'auth.login'
    
    # Register error handlers using service
    ErrorService.register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
    
    app.logger.info(f"Application initialized with {config_name} configuration")
    return app

def register_blueprints(app):
    """Register Flask blueprints"""
    from app.auth.routes import auth_bp
    from app.quiz.routes import quiz_bp
    from app.subject.routes import subject_bp
    from app.dashboard.routes import dashboard_bp
    from app.main.routes import main_bp
    from app.import_document import import_document_bp
    from app.import_document.batch_operations import batch_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    app.register_blueprint(subject_bp, url_prefix='/subject')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(main_bp)
    app.register_blueprint(import_document_bp, url_prefix='/import')
    app.register_blueprint(batch_bp, url_prefix='/batch')

# Error handlers are now managed by ErrorService

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        from app.models import User
        return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None