from flask import Blueprint, render_template, jsonify, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@main_bp.route('/api/auth/status')
def auth_status():
    """API endpoint to check authentication status"""
    if 'credentials' in session:
        return jsonify({
            'authenticated': True
        })
    else:
        return jsonify({
            'authenticated': False,
            'auth_url': url_for('auth.login')
        })

@main_bp.route('/health')
def health():
    """Health check endpoint for DigitalOcean"""
    return jsonify({
        'status': 'healthy'
    })