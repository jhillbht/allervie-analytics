from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from flask import session, url_for, current_app
import json
import os
import logging

class GoogleOAuth:
    """Handles Google OAuth authentication flow"""
    
    def __init__(self):
        """Initialize OAuth handler with app configuration"""
        self.client_id = current_app.config['GOOGLE_CLIENT_ID']
        self.client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
        self.redirect_uri = current_app.config['REDIRECT_URI']
        self.scopes = current_app.config['SCOPES']
        
        # Set OAUTHLIB to allow HTTP for development
        if current_app.config['DEBUG']:
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            # Allow additional scopes to be appended by Google
            os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    def get_auth_url(self):
        """Generate the authorization URL for the OAuth flow"""
        flow = self._create_flow()
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',      # Get a refresh token
            include_granted_scopes='true',  # Include previously granted scopes
            prompt='consent'            # Force consent screen for refresh token
        )
        
        # Save the state in the session for later verification
        session['oauth_state'] = state
        return authorization_url
    
    def get_credentials_from_code(self, code, state):
        """Exchange authorization code for credentials"""
        # Verify the state matches to prevent CSRF
        session_state = session.get('oauth_state')
        if state != session_state:
            raise ValueError("State mismatch. Possible CSRF attack.")
        
        # Create flow with the saved state
        flow = self._create_flow()
        flow.fetch_token(code=code)
        
        # Log actual scopes returned vs requested
        if current_app.config['DEBUG']:
            requested_scopes = set(self.scopes)
            received_scopes = set(flow.credentials.scopes)
            current_app.logger.info(f"Requested scopes: {requested_scopes}")
            current_app.logger.info(f"Received scopes: {received_scopes}")
        
        # Store credentials in session
        credentials = flow.credentials
        session['credentials'] = self._credentials_to_dict(credentials)
        
        return credentials
    
    def get_credentials_from_session(self):
        """Retrieve credentials from session"""
        if 'credentials' not in session:
            return None
        
        return Credentials(**session['credentials'])
    
    def _create_flow(self):
        """Create an OAuth flow instance"""
        # Create the flow using client config
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
    
    def _credentials_to_dict(self, credentials):
        """Convert credentials to dictionary for session storage"""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
