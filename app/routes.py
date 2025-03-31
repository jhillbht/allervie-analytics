from flask import Blueprint, render_template, jsonify, session, redirect, url_for
from app.auth.google_oauth import GoogleOAuth

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@main_bp.route('/api/auth/status')
def auth_status():
    """API endpoint to check authentication status"""
    oauth = GoogleOAuth()
    credentials = oauth.get_credentials_from_session()
    
    if credentials:
        return jsonify({
            'authenticated': True
        })
    else:
        return jsonify({
            'authenticated': False,
            'auth_url': url_for('auth.login')
        })

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy'
    })