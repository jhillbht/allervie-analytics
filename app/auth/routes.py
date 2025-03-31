from flask import Blueprint, redirect, request, url_for, current_app, flash, session, render_template
import os
import time
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging

auth_bp = Blueprint('auth', __name__)

# Configure logger
logger = logging.getLogger('allervie-analytics.auth')

@auth_bp.route('/login')
def login():
    """Start the OAuth flow by redirecting to Google's consent page"""
    # Clear any existing credentials to ensure a fresh login
    if 'credentials' in session:
        del session['credentials']
        logger.info("Cleared existing credentials for fresh login")
    
    # Set environment variable to relax scope checking
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
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
    
    # Generate authorization URL with explicit prompt for consent
    # This ensures we always get the refresh token which is required for OAuth to work
    authorization_url, state = flow.authorization_url(
        access_type='offline',       # Request a refresh token
        include_granted_scopes='true', # Include previously granted scopes
        prompt='consent'            # Always show consent screen to get refresh token
    )
    
    # Store state for CSRF protection
    session['oauth_state'] = state
    
    return redirect(authorization_url)

@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Google"""
    # Set environment variable to relax scope checking
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    # Get authorization code from URL
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Validate the request has both code and state
    if not code or not state:
        flash('Authentication failed: missing parameters', 'error')
        logger.error("OAuth callback missing code or state parameters")
        return redirect(url_for('main.index'))
    
    # Verify state for CSRF protection
    if state != session.get('oauth_state'):
        flash('Authentication failed: invalid state', 'error')
        logger.error(f"OAuth state mismatch. Received: {state}, Expected: {session.get('oauth_state')}")
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
        
        # Fetch token
        token_response = flow.fetch_token(code=code)
        logger.info("Successfully fetched OAuth tokens")
        
        # Log detailed token info for debugging
        credentials = flow.credentials
        
        # Check for required scopes
        received_scopes = set(credentials.scopes)
        required_scopes = {'https://www.googleapis.com/auth/adwords'}
        missing_scopes = required_scopes - received_scopes
        
        if missing_scopes:
            logger.error(f"Missing required scopes: {missing_scopes}")
            flash(f"Authentication failed: Missing required Google Ads permissions. Please try again.", 'error')
            return redirect(url_for('auth.login'))
            
        # Store credentials in session
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Force token refresh to ensure we have a fresh token
        creds = Credentials(**session['credentials'])
        if creds.expired:
            logger.info("Refreshing expired token")
            creds.refresh(Request())
            
            # Update session with refreshed credentials
            session['credentials'] = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            logger.info("Token successfully refreshed")
        
        flash('Authentication successful!', 'success')
        logger.info("OAuth authentication completed successfully")
        
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
        logger.error(f"Authentication error: {str(e)}")
    
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    """Log out user by clearing session"""
    # Clear credentials from session
    if 'credentials' in session:
        del session['credentials']
        logger.info("User logged out, credentials cleared from session")
    
    # Clear any other session data
    session.clear()
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))  # Redirect directly to login instead of index