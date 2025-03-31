from flask import Blueprint, jsonify, request, current_app, session
from app.auth.google_oauth import GoogleOAuth
from app.analytics.ga4 import GA4Analytics
from app.analytics.google_ads import GoogleAdsAnalytics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/active-users')
def active_users():
    """API endpoint to get active users data"""
    try:
        # Get OAuth credentials
        oauth = GoogleOAuth()
        credentials = oauth.get_credentials_from_session()
        
        # Check if user is authenticated
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Initialize GA4 client
        property_id = current_app.config['GA4_PROPERTY_ID']
        analytics = GA4Analytics(credentials, property_id)
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Get data from GA4
        data = analytics.get_active_users(days)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        # Handle errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/traffic-sources')
def traffic_sources():
    """API endpoint to get traffic sources data"""
    try:
        # Get OAuth credentials
        oauth = GoogleOAuth()
        credentials = oauth.get_credentials_from_session()
        
        # Check if user is authenticated
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Initialize GA4 client
        property_id = current_app.config['GA4_PROPERTY_ID']
        analytics = GA4Analytics(credentials, property_id)
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Get data from GA4
        data = analytics.get_traffic_sources(days)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        # Handle errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/ads/campaigns')
def ads_campaigns():
    """API endpoint to get Google Ads campaign data"""
    try:
        # Get OAuth credentials
        oauth = GoogleOAuth()
        credentials = oauth.get_credentials_from_session()
        
        # Check if user is authenticated
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Get Google Ads configuration
        customer_id = current_app.config['GOOGLE_ADS_CUSTOMER_ID']
        developer_token = current_app.config['GOOGLE_ADS_DEVELOPER_TOKEN']
        
        # Initialize Google Ads client
        ads = GoogleAdsAnalytics(credentials, customer_id, developer_token)
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Get data from Google Ads
        data = ads.get_campaign_performance(days)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        # Handle errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500