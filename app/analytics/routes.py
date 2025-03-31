from flask import Blueprint, jsonify, request, current_app, session
from google.oauth2.credentials import Credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

analytics_bp = Blueprint('analytics', __name__)

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
        
        # Define request
        request = RunReportRequest(
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
        response = client.run_report(request)
        
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
        
        # Define request
        request = RunReportRequest(
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
        response = client.run_report(request)
        
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
        
        # Create credentials object
        credentials = Credentials(**session['credentials'])
        
        # Get Google Ads configuration
        customer_id = current_app.config['GOOGLE_ADS_CUSTOMER_ID']
        developer_token = current_app.config['GOOGLE_ADS_DEVELOPER_TOKEN']
        
        # Create Google Ads client
        client = GoogleAdsClient.load_from_dict({
            "credentials": {
                "refresh_token": credentials.refresh_token,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "token_uri": credentials.token_uri
            },
            "developer_token": developer_token,
            "use_proto_plus": True
        })
        
        # Get Google Ads service
        ga_service = client.get_service("GoogleAdsService")
        
        # Get requested time period
        days = request.args.get('days', default=30, type=int)
        
        # Calculate date range for query
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for GAQL query
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Build GAQL query
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date BETWEEN '{start_date_str}' AND '{end_date_str}'
            ORDER BY metrics.impressions DESC
        """
        
        # Execute query
        response = ga_service.search(
            customer_id=customer_id,
            query=query
        )
        
        # Format response data
        data = []
        for row in response:
            campaign = row.campaign
            metrics = row.metrics
            
            data.append({
                'campaign_id': campaign.id,
                'campaign_name': campaign.name,
                'campaign_status': campaign.status.name,
                'impressions': metrics.impressions,
                'clicks': metrics.clicks,
                'cost': metrics.cost_micros / 1000000,
                'conversions': metrics.conversions,
                'conversion_value': metrics.conversions_value,
                'ctr': metrics.ctr * 100,
                'average_cpc': metrics.average_cpc / 1000000
            })
        
        return jsonify({
            'success': True,
            'data': data
        })
    except GoogleAdsException as ex:
        # Handle Google Ads API errors
        error_message = []
        
        for error in ex.failure.errors:
            error_message.append(f"Error: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    error_message.append(f"\tOn field: {field_path_element.field_name}")
            
        return jsonify({
            'success': False,
            'error': '\n'.join(error_message)
        }), 500
    except Exception as e:
        # Handle other errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500