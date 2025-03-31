from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from datetime import datetime, timedelta
import os
import logging

class GoogleAdsAnalytics:
    """Google Ads API integration"""
    
    def __init__(self, credentials, customer_id, developer_token):
        """Initialize with OAuth credentials and Google Ads account info"""
        self.customer_id = customer_id
        self.developer_token = developer_token
        
        # Ensure no YAML config file is used
        os.environ["GOOGLE_ADS_CONFIGURATION_FILE_PATH"] = ""
        os.environ["GOOGLE_ADS_YAML_CONFIG_PATH"] = ""
        
        # Create Google Ads Client configuration
        client_config = {
            "credentials": {
                "refresh_token": credentials.refresh_token,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "token_uri": credentials.token_uri
            },
            "developer_token": developer_token,
            "use_proto_plus": True,
            "login_customer_id": customer_id
        }
        
        # Create Google Ads Client
        self.client = GoogleAdsClient.load_from_dict(client_config)
    
    def get_campaign_performance(self, days=30):
        """Get campaign performance data for the specified number of days"""
        ga_service = self.client.get_service("GoogleAdsService")
        
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
        
        try:
            # Execute the query
            response = ga_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            # Process the results
            results = []
            for row in response:
                campaign = row.campaign
                metrics = row.metrics
                
                # Format the data
                results.append({
                    'campaign_id': campaign.id,
                    'campaign_name': campaign.name,
                    'campaign_status': campaign.status.name,
                    'impressions': metrics.impressions,
                    'clicks': metrics.clicks,
                    'cost': metrics.cost_micros / 1000000,  # Convert micros to standard currency
                    'conversions': metrics.conversions,
                    'conversion_value': metrics.conversions_value,
                    'ctr': metrics.ctr * 100,  # Convert to percentage
                    'average_cpc': metrics.average_cpc / 1000000  # Convert micros to standard currency
                })
                
            return results
            
        except GoogleAdsException as ex:
            # Handle Google Ads API errors
            error_message = []
            
            for error in ex.failure.errors:
                error_message.append(f"Error: {error.message}")
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        error_message.append(f"\tOn field: {field_path_element.field_name}")
                
            raise Exception('\n'.join(error_message))
