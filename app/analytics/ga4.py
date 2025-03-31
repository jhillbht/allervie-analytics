from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange
from google.analytics.data_v1beta.types import Dimension, Metric
from datetime import datetime, timedelta

class GA4Analytics:
    """Google Analytics 4 (GA4) API integration"""
    
    def __init__(self, credentials, property_id):
        """Initialize with OAuth credentials and GA4 property ID"""
        self.client = BetaAnalyticsDataClient(credentials=credentials)
        self.property_id = property_id
    
    def get_active_users(self, days=30):
        """Get active users data for the specified number of days"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Define dimensions and metrics
        dimensions = [Dimension(name="date")]
        metrics = [
            Metric(name="activeUsers"),
            Metric(name="newUsers")
        ]
        
        # Create date range
        date_ranges = [
            DateRange(
                start_date=start_date,
                end_date=end_date
            )
        ]
        
        # Build and run the request
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            dimensions=dimensions,
            metrics=metrics,
            date_ranges=date_ranges
        )
        
        response = self.client.run_report(request)
        
        # Format the response data
        return self._format_response(response)
    
    def get_traffic_sources(self, days=30):
        """Get traffic source data for the specified number of days"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Define dimensions and metrics
        dimensions = [Dimension(name="sessionSource")]
        metrics = [
            Metric(name="sessions"),
            Metric(name="activeUsers")
        ]
        
        # Create date range
        date_ranges = [
            DateRange(
                start_date=start_date,
                end_date=end_date
            )
        ]
        
        # Build and run the request
        request = RunReportRequest(
            property=f'properties/{self.property_id}',
            dimensions=dimensions,
            metrics=metrics,
            date_ranges=date_ranges
        )
        
        response = self.client.run_report(request)
        
        # Format the response data
        return self._format_response(response)
    
    def _format_response(self, response):
        """Format the API response into a JSON-friendly structure"""
        formatted_data = []
        
        # Iterate through each row in the response
        for row in response.rows:
            data_point = {}
            
            # Add dimensions to the data point
            for i, dimension in enumerate(response.dimension_headers):
                data_point[dimension.name] = row.dimension_values[i].value
                
            # Add metrics to the data point
            for i, metric in enumerate(response.metric_headers):
                value = row.metric_values[i].value
                # Try to convert to float for numeric values
                try:
                    data_point[metric.name] = float(value)
                except ValueError:
                    data_point[metric.name] = value
                
            formatted_data.append(data_point)
            
        return formatted_data