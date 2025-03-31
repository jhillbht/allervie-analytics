from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from datetime import datetime, timedelta
import os
import logging
import json
import requests
from google.auth.transport.requests import Request

class GoogleAdsAnalytics:
    """Google Ads API integration with REST API fallback"""
    
    def __init__(self, credentials, customer_id, developer_token):
        """Initialize with OAuth credentials and Google Ads account info"""
        # Check if customer_id matches the MCC ID format (from the second image)
        # If it matches the old incorrect ID, use the MCC ID instead
        if str(customer_id).strip() == "8437927403":
            customer_id = "5686645688"  # AllerVie MCC ID from the second image
            logging.warning(f"Replaced incorrect customer ID with MCC ID: {customer_id}")
            
        # Ensure customer_id is properly formatted (no dashes or other formatting)
        self.customer_id = str(customer_id).replace('-', '').strip().replace('"', '').replace("'", "")
        logging.info(f"Using Google Ads customer_id: {self.customer_id}")
        
        self.developer_token = developer_token
        self.credentials = credentials
        
        # Ensure credentials are fresh
        if self.credentials.expired and self.credentials.refresh_token:
            logging.info("Refreshing expired OAuth credentials")
            try:
                self.credentials.refresh(Request())
                logging.info("Successfully refreshed OAuth credentials")
            except Exception as e:
                logging.error(f"Failed to refresh OAuth credentials: {str(e)}")
                raise Exception(f"OAuth token refresh failed: {str(e)}")
        
        # Log token info (first few characters only for security)
        if self.credentials.token:
            token_preview = self.credentials.token[:10] + "..." if len(self.credentials.token) > 10 else "..."
            logging.info(f"OAuth token length: {len(self.credentials.token)}, preview: {token_preview}")
        else:
            logging.error("OAuth token is missing or empty")
            raise Exception("OAuth token is missing, please log out and log in again")
        
        # Path to the YAML configuration file
        yaml_path = os.path.join(os.getcwd(), "google-ads.yaml")
        logging.info(f"YAML configuration path: {yaml_path}")
        
        # Set configuration file path
        os.environ["GOOGLE_ADS_CONFIGURATION_FILE_PATH"] = yaml_path
        
        # Update the refresh_token in the YAML configuration
        self._update_refresh_token(yaml_path, credentials.refresh_token)
        
        # Try to create Google Ads Client
        try:
            # Create Google Ads Client from the YAML file
            self.client = GoogleAdsClient.load_from_storage(yaml_path)
            self.use_rest_fallback = False
            logging.info("Successfully initialized Google Ads GRPC client")
        except Exception as e:
            logging.error(f"Failed to create Google Ads GRPC client: {str(e)}")
            logging.info("Will use REST API fallback for Google Ads")
            self.use_rest_fallback = True
    
    def _update_refresh_token(self, yaml_path, refresh_token):
        """Update the refresh_token in the YAML configuration file"""
        if not os.path.exists(yaml_path):
            # Create a new YAML file if it doesn't exist
            logging.info(f"Creating new Google Ads YAML configuration file at {yaml_path}")
            yaml_content = f"""# Google Ads API Configuration

developer_token: {self.developer_token}

# Required for manager accounts only: Specify the login customer ID used to authenticate API calls.
login_customer_id: {self.customer_id}

# Required for manager accounts only: Specify the linked customer ID.
linked_customer_id: {self.customer_id}

# API Version (using v19 as of March 2025)
api_version: v19

# OAuth2 configuration
use_proto_plus: True

# Configure OAuth2 installed application flow (non-service account)
client_id: {self.credentials.client_id}
client_secret: {self.credentials.client_secret}
refresh_token: {refresh_token}
"""
            
            # Write the YAML file
            with open(yaml_path, 'w') as file:
                file.write(yaml_content)
                
            logging.info(f"Created new YAML configuration file with refresh_token")
            return
        
        # Read the YAML file
        with open(yaml_path, 'r') as file:
            yaml_content = file.read()
        
        # Update login_customer_id and linked_customer_id to ensure they match
        import re
        yaml_content = re.sub(
            r'login_customer_id:.*', 
            f'login_customer_id: {self.customer_id}',
            yaml_content
        )
        yaml_content = re.sub(
            r'linked_customer_id:.*', 
            f'linked_customer_id: {self.customer_id}',
            yaml_content
        )
        
        # Check if refresh_token needs to be added or updated
        if 'refresh_token:' not in yaml_content:
            # Add refresh_token at the end of the file
            yaml_content += f"\nrefresh_token: {refresh_token}\n"
        else:
            # Replace existing refresh_token
            yaml_content = re.sub(
                r'refresh_token:.*', 
                f'refresh_token: {refresh_token}',
                yaml_content
            )
        
        # Write the updated YAML file
        with open(yaml_path, 'w') as file:
            file.write(yaml_content)
        
        logging.info(f"Updated refresh_token and customer IDs in {yaml_path}")
    
    def get_campaign_performance(self, days=30):
        """Get campaign performance data for the specified number of days"""
        try:
            # First try using the GRPC client
            if not self.use_rest_fallback:
                return self._get_campaign_performance_grpc(days)
        except Exception as e:
            logging.warning(f"GRPC client failed, falling back to REST API: {str(e)}")
            self.use_rest_fallback = True
        
        # If GRPC fails or is disabled, use REST API fallback
        return self._get_campaign_performance_rest(days)
    
    def _get_campaign_performance_grpc(self, days=30):
        """Get campaign performance data using GRPC client"""
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
            # Log the customer ID being used
            logging.info(f"Executing GRPC query for customer_id: {self.customer_id}")
            
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
    
    def _get_campaign_performance_rest(self, days=30):
        """Fallback implementation using Google Ads REST API"""
        logging.info("Using REST API for Google Ads")
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for query
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Make sure the credentials are fresh
        if self.credentials.expired and self.credentials.refresh_token:
            logging.info("Refreshing expired OAuth credentials for REST API")
            try:
                self.credentials.refresh(Request())
                logging.info("Successfully refreshed OAuth credentials for REST API")
            except Exception as e:
                logging.error(f"Failed to refresh OAuth credentials: {str(e)}")
                raise Exception(f"OAuth token refresh failed for REST API: {str(e)}")
        
        # Double-check token validity
        if not self.credentials.token:
            logging.error("OAuth token is missing or empty for REST API call")
            raise Exception("OAuth token is missing for REST API call")
        
        # Prepare the Google Ads REST API request
        # Use v19 which is the current version as of March 2025
        api_version = "v19"
        
        # Use correct endpoint format:
        # https://googleads.googleapis.com/{version}/customers/{customer_id}/googleAds:search
        base_url = f"https://googleads.googleapis.com/{api_version}/customers/{self.customer_id}/googleAds:search"
        
        # Log the URL being used
        logging.info(f"Google Ads REST API URL: {base_url}")
        
        # Build the GAQL query
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
        
        # Prepare the request data
        request_data = {
            "query": query
        }
        
        # Prepare the authorization header
        # Ensure token is properly formatted
        token = self.credentials.token.strip()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json"
        }
        
        # Add login-customer-id header for manager accounts
        headers["login-customer-id"] = self.customer_id
        
        # Log headers (without sensitive information)
        safe_headers = headers.copy()
        safe_headers["Authorization"] = f"Bearer {token[:5]}..." if len(token) > 5 else "Bearer [REDACTED]"
        safe_headers["developer-token"] = "[REDACTED]"
        logging.info(f"Request headers: {safe_headers}")
        
        # Make the request
        logging.info(f"Making REST API request to Google Ads")
        response = requests.post(base_url, headers=headers, json=request_data)
        
        # Log the response status
        logging.info(f"REST API response status: {response.status_code}")
        
        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f"Google Ads REST API request failed with status {response.status_code}: {response.text}"
            logging.error(error_msg)
            
            # Check for token-related errors
            if response.status_code == 401:
                logging.error("Authentication error detected. Token might be invalid.")
                # Try to extract more detailed error information
                try:
                    error_data = response.json()
                    logging.error(f"Authentication error details: {json.dumps(error_data, indent=2)}")
                except:
                    logging.error("Could not parse error response as JSON")
            
            raise Exception(error_msg)
        
        # Parse the response
        response_data = response.json()
        
        # Log the success
        logging.info("Successfully received response from Google Ads REST API")
        
        # Process the results
        results = []
        
        if "results" in response_data:
            for result in response_data["results"]:
                # Extract the data from the result
                campaign_id = result.get("campaign", {}).get("id")
                campaign_name = result.get("campaign", {}).get("name")
                campaign_status = result.get("campaign", {}).get("status")
                
                metrics = result.get("metrics", {})
                impressions = float(metrics.get("impressions", 0))
                clicks = float(metrics.get("clicks", 0))
                cost_micros = float(metrics.get("costMicros", 0))
                conversions = float(metrics.get("conversions", 0))
                conversions_value = float(metrics.get("conversionsValue", 0))
                ctr = float(metrics.get("ctr", 0)) * 100  # Convert to percentage
                average_cpc = float(metrics.get("averageCpc", 0)) / 1000000  # Convert micros to standard currency
                
                # Format the data
                results.append({
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'campaign_status': campaign_status,
                    'impressions': impressions,
                    'clicks': clicks,
                    'cost': cost_micros / 1000000,  # Convert micros to standard currency
                    'conversions': conversions,
                    'conversion_value': conversions_value,
                    'ctr': ctr,
                    'average_cpc': average_cpc
                })
        
        if not results:
            logging.warning("No campaign data returned from Google Ads REST API")
            
        return results