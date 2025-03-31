from flask import Blueprint, redirect, request, url_for, current_app, flash, session, render_template
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Start the OAuth flow by redirecting to Google's consent page"""
    # Create OAuth flow instance
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [current_app.config['REDIRECT_URI']]
            }
        },
        scopes=current_app.config['SCOPES']
    )
    
    flow.redirect_uri = current_app.config['REDIRECT_URI']
    
    # Allow HTTP for local development
    if current_app.config['DEBUG']:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store state for CSRF protection
    session['oauth_state'] = state
    
    return redirect(authorization_url)

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
    
    # Verify state for CSRF protection
    if state != session.get('oauth_state'):
        flash('Authentication failed: invalid state', 'error')
        return redirect(url_for('main.index'))
    
    # Exchange code for credentials
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                    "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [current_app.config['REDIRECT_URI']]
                }
            },
            scopes=current_app.config['SCOPES'],
            state=state
        )
        flow.redirect_uri = current_app.config['REDIRECT_URI']
        flow.fetch_token(code=code)
        
        # Store credentials in session
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
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