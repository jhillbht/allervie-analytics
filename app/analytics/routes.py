from flask import Blueprint, jsonify, request, current_app, session
from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import os
import logging
import traceback
import sys
import json
from google.auth.transport.requests import Request

analytics_bp = Blueprint('analytics', __name__)

# Configure logger for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('allervie-analytics')

@analytics_bp.route('/active-users')
def active_users():
    """API endpoint to get active users data"""
    try:
        # Check if user is authenticated
        if 'credentials' not in session:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Create credentials object
        credentials = Credentials(**session['credentials'])
        
        # Initialize GA4 client
        client = BetaAnalyticsDataClient(credentials=credentials)
        property_id = current_app.config['GA4_PROPERTY_ID']
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Calculate date range
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Define API request
        ga_request = RunReportRequest(
            property=f'properties/{property_id}',
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="newUsers")
            ],
            date_ranges=[
                DateRange(
                    start_date=start_date,
                    end_date=end_date
                )
            ]
        )
        
        # Execute request
        response = client.run_report(ga_request)
        
        # Format response data
        data = []
        for row in response.rows:
            data_point = {
                'date': row.dimension_values[0].value,
                'activeUsers': float(row.metric_values[0].value),
                'newUsers': float(row.metric_values[1].value)
            }
            data.append(data_point)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        # Handle errors
        logger.error(f"Active users error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/traffic-sources')
def traffic_sources():
    """API endpoint to get traffic sources data"""
    try:
        # Check if user is authenticated
        if 'credentials' not in session:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Create credentials object
        credentials = Credentials(**session['credentials'])
        
        # Initialize GA4 client
        client = BetaAnalyticsDataClient(credentials=credentials)
        property_id = current_app.config['GA4_PROPERTY_ID']
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Calculate date range
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Define API request
        ga_request = RunReportRequest(
            property=f'properties/{property_id}',
            dimensions=[Dimension(name="sessionSource")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers")
            ],
            date_ranges=[
                DateRange(
                    start_date=start_date,
                    end_date=end_date
                )
            ]
        )
        
        # Execute request
        response = client.run_report(ga_request)
        
        # Format response data
        data = []
        for row in response.rows:
            data_point = {
                'sessionSource': row.dimension_values[0].value,
                'sessions': float(row.metric_values[0].value),
                'activeUsers': float(row.metric_values[1].value)
            }
            data.append(data_point)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        # Handle errors
        logger.error(f"Traffic sources error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@analytics_bp.route('/ads/campaigns')
def ads_campaigns():
    """API endpoint to get Google Ads campaign data"""
    try:
        # Check if user is authenticated
        if 'credentials' not in session:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Enable more detailed logging
        logger.setLevel(logging.DEBUG)
        
        # Log the start of processing
        logger.info("Processing Google Ads campaign data request")
        
        # Create credentials object from session
        credentials_dict = session.get('credentials', {})
        
        # Log the credential info (without sensitive parts)
        if credentials_dict:
            logger.info(f"Credentials scopes: {credentials_dict.get('scopes', [])}")
            logger.info(f"Credentials have refresh_token: {'Yes' if credentials_dict.get('refresh_token') else 'No'}")
        
        # Validate required credential fields
        required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes']
        missing_fields = [field for field in required_fields if field not in credentials_dict]
        
        if missing_fields:
            logger.error(f"Missing credential fields: {missing_fields}")
            return jsonify({
                'success': False,
                'error': f"Incomplete credentials. Missing fields: {', '.join(missing_fields)}. Please log out and log in again."
            }), 400
        
        # Create credentials object and refresh if needed
        credentials = Credentials(**credentials_dict)
        
        # Check if token is expired and refresh it
        if credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired OAuth token")
            try:
                credentials.refresh(Request())
                logger.info("Successfully refreshed OAuth token")
                
                # Update session with refreshed credentials
                session['credentials'] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                logger.info("Updated session with refreshed credentials")
            except Exception as refresh_error:
                logger.error(f"Error refreshing OAuth token: {str(refresh_error)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'error': f"Failed to refresh OAuth token: {str(refresh_error)}. Please log out and log in again."
                }), 401
        
        # Get Google Ads configuration
        customer_id = current_app.config['GOOGLE_ADS_CUSTOMER_ID']
        
        # Check if we're using the old incorrect ID and switch to the MCC ID
        if str(customer_id).strip() == "8437927403":
            customer_id = "5686645688"  # AllerVie MCC ID
            logger.warning(f"Using MCC ID instead of client ID: {customer_id}")
        
        # Format customer ID properly (remove quotes and other non-numeric characters)
        customer_id = str(customer_id).replace('-', '').strip().replace('"', '').replace("'", "")
        logger.info(f"Using Google Ads Customer ID: {customer_id}")
        
        developer_token = current_app.config['GOOGLE_ADS_DEVELOPER_TOKEN']
        
        # Log the access attempt (without sensitive info)
        logger.info(f"Accessing Google Ads API with customer_id: {customer_id}")
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Log the request parameters
        logger.info(f"Requested campaign data for the last {days} days")
        
        # Create GoogleAdsAnalytics instance
        try:
            from app.analytics.google_ads import GoogleAdsAnalytics
            google_ads = GoogleAdsAnalytics(credentials, customer_id, developer_token)
            
            # Log the credential status
            logger.info(f"OAuth credential status - expired: {credentials.expired}, token: {'Present' if credentials.token else 'Missing'}")
            
            # Get campaign performance data (this will try GRPC first, then REST API if needed)
            logger.info("Fetching campaign performance data...")
            data = google_ads.get_campaign_performance(days)
            
            if not data:
                logger.warning("No campaign data returned from Google Ads API")
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': 'No campaign data found for the specified period. Check that your Google Ads account has active campaigns.'
                })
            
            # Log success
            logger.info(f"Successfully retrieved {len(data)} campaigns")
            
            return jsonify({
                'success': True,
                'data': data
            })
        except Exception as api_error:
            # Log the detailed error for debugging
            logger.error(f"Google Ads API error details: {str(api_error)}")
            logger.error(traceback.format_exc())
            
            # Try to parse JSON error response if present
            error_message = str(api_error)
            try:
                if "{" in error_message and "}" in error_message:
                    json_start = error_message.find("{")
                    json_end = error_message.rfind("}") + 1
                    json_str = error_message[json_start:json_end]
                    error_json = json.loads(json_str)
                    
                    # Extract more detailed error information
                    if "error" in error_json:
                        error_info = error_json["error"]
                        detailed_message = f"API Error: {error_info.get('message', 'Unknown error')}"
                        
                        # Add error details if present
                        if "details" in error_info:
                            for detail in error_info["details"]:
                                if "@type" in detail and "googleads" in detail["@type"].lower():
                                    if "errors" in detail:
                                        for error in detail["errors"]:
                                            error_code = error.get("errorCode", {})
                                            error_type = next(iter(error_code.keys())) if error_code else "Unknown"
                                            error_value = error_code.get(error_type) if error_code else "Unknown"
                                            detailed_message += f"\nError type: {error_type}, Value: {error_value}"
                                            
                                            if "message" in error:
                                                detailed_message += f"\nDetails: {error['message']}"
                        
                        error_message = detailed_message
            except Exception as json_error:
                # If JSON parsing fails, use the original error message
                logger.error(f"Error parsing JSON error: {str(json_error)}")
            
            # Return a user-friendly error
            return jsonify({
                'success': False,
                'error': f"Error accessing Google Ads API: {error_message}",
                'error_type': type(api_error).__name__
            }), 500
            
    except GoogleAdsException as ex:
        # Handle Google Ads API errors specifically
        error_message = []
        
        for error in ex.failure.errors:
            error_message.append(f"Error: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    error_message.append(f"\tOn field: {field_path_element.field_name}")
            
        error_str = '\n'.join(error_message)
        logger.error(f"Google Ads API exception: {error_str}")
        
        return jsonify({
            'success': False,
            'error': error_str
        }), 500
    except Exception as e:
        # Handle other unexpected errors
        logger.error(f"Unexpected error in ads_campaigns: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }), 500