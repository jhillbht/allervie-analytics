from flask import Blueprint, redirect, request, url_for, current_app, flash, session, render_template
from app.auth.google_oauth import GoogleOAuth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Start the OAuth flow by redirecting to Google's consent page"""
    oauth = GoogleOAuth()
    auth_url = oauth.get_auth_url()
    return redirect(auth_url)

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Google"""
    # Get authorization code from URL
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Validate the request has both code and state
    if not code or not state:
        flash('Authentication failed: missing parameters', 'error')
        return redirect(url_for('main.index'))
    
    # Exchange code for credentials
    oauth = GoogleOAuth()
    try:
        credentials = oauth.get_credentials_from_code(code, state)
        flash('Authentication successful!', 'success')
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    """Log out user by clearing session"""
    # Clear credentials from session
    if 'credentials' in session:
        del session['credentials']
    
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))