from flask import Flask
from flask_session import Session
import os
from datetime import timedelta
import logging

# Session configuration
session = Session()

def create_app():
    app = Flask(__name__, 
                static_folder='../static',
                template_folder='../templates')
    
    # Configure logging
    if os.environ.get('DEBUG', 'false').lower() == 'true':
        app.logger.setLevel(logging.INFO)
        
    # Set environment variables for OAuth scope relaxation
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    # Load configuration
    app.config.from_pyfile('config.py')
    
    # Configure server-side session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
    session.init_app(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.analytics.routes import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create session directory if it doesn't exist
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    return app
