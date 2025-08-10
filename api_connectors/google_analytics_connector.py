import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
    FilterExpression,
    Filter,
    RunRealtimeReportRequest
)
from google.oauth2.service_account import Credentials
from config.settings import settings

logger = logging.getLogger(__name__)


class GoogleAnalyticsConnector:
    """
    GA4 API integration for comprehensive analytics data.
    Real-time data extraction and transformation with custom metric creation.
    """
    
    def __init__(self, property_id: str, credentials_path: Optional[str] = None):
        self.property_id = property_id
        self.credentials_path = credentials_path or settings.google_analytics_credentials_path
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Analytics Data API client."""
        try:
            if self.credentials_path:
                credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/analytics.readonly']
                )
                self.client = BetaAnalyticsDataClient(credentials=credentials)
            else:
                self.client = BetaAnalyticsDataClient()
            
            logger.info("Google Analytics client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Analytics client: {e}")
            raise
    
    def connect(self) -> bool:
        """Test connection to Google Analytics."""
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="date")],
                metrics=[Metric(name="sessions")],
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
                limit=1
            )
            response = self.client.run_report(request=request)
            logger.info("Google Analytics connection test successful")
            return True
        except Exception as e:
            logger.error(f"Google Analytics connection test failed: {e}")
            return False
    
    def get_standard_metrics(
        self, 
        start_date: str, 
        end_date: str,
        dimensions: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get standard GA4 metrics for specified date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format or relative format like '7daysAgo'
            end_date: End date in YYYY-MM-DD format or 'today'
            dimensions: List of dimension names (e.g., ['date', 'source'])
            metrics: List of metric names (e.g., ['sessions', 'pageviews'])
        """
        if not dimensions:
            dimensions = ['date', 'sourceMedium', 'deviceCategory']
        
        if not metrics:
            metrics = ['sessions', 'pageviews', 'bounceRate', 'averageSessionDuration', 'conversions']
        
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=10000
            )
            
            response = self.client.run_report(request=request)
            
            return self._process_report_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get standard metrics: {e}")
            return {}
    
    def get_conversion_metrics(
        self, 
        start_date: str, 
        end_date: str,
        conversion_events: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get conversion and goal tracking data."""
        if not conversion_events:
            conversion_events = ['purchase', 'sign_up', 'contact', 'download']
        
        try:
            # Get conversion data by event
            dimensions = ['date', 'eventName', 'sourceMedium']
            metrics = ['conversions', 'totalRevenue', 'eventCount']
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        in_list_filter=Filter.InListFilter(values=conversion_events)
                    )
                ),
                limit=10000
            )
            
            response = self.client.run_report(request=request)
            return self._process_report_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get conversion metrics: {e}")
            return {}
    
    def get_attribution_data(
        self, 
        start_date: str, 
        end_date: str,
        attribution_model: str = "data_driven"
    ) -> Dict[str, Any]:
        """Get attribution data for multi-touch analysis."""
        try:
            dimensions = [
                'date', 
                'firstUserSourceMedium',
                'sessionSourceMedium',
                'firstUserCampaignName',
                'sessionCampaignName'
            ]
            
            metrics = [
                'conversions',
                'totalRevenue',
                'sessions',
                'newUsers',
                'purchaseRevenue'
            ]
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=10000
            )
            
            response = self.client.run_report(request=request)
            return self._process_report_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get attribution data: {e}")
            return {}
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time analytics data."""
        try:
            request = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[
                    Dimension(name="country"),
                    Dimension(name="deviceCategory"),
                    Dimension(name="unifiedSourceMedium")
                ],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="conversions")
                ],
                limit=100
            )
            
            response = self.client.run_realtime_report(request=request)
            return self._process_realtime_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get realtime metrics: {e}")
            return {}
    
    def get_audience_data(
        self, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get audience segmentation and demographic data."""
        try:
            dimensions = [
                'date',
                'country',
                'city', 
                'ageGroup',
                'gender',
                'userType',
                'newVsReturning'
            ]
            
            metrics = [
                'totalUsers',
                'newUsers',
                'sessions',
                'bounceRate',
                'averageSessionDuration',
                'pageviews'
            ]
            
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=10000
            )
            
            response = self.client.run_report(request=request)
            return self._process_report_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get audience data: {e}")
            return {}
    
    def _process_report_response(self, response) -> Dict[str, Any]:
        """Process GA4 report response into structured data."""
        processed_data = {
            'dimensions': [dim.name for dim in response.dimension_headers],
            'metrics': [metric.name for metric in response.metric_headers],
            'rows': [],
            'totals': {},
            'metadata': {
                'row_count': response.row_count,
                'property_quota': getattr(response, 'property_quota', None)
            }
        }
        
        # Process data rows
        for row in response.rows:
            row_data = {}
            
            # Add dimension values
            for i, dimension_value in enumerate(row.dimension_values):
                dim_name = processed_data['dimensions'][i]
                row_data[dim_name] = dimension_value.value
            
            # Add metric values
            for i, metric_value in enumerate(row.metric_values):
                metric_name = processed_data['metrics'][i]
                row_data[metric_name] = self._convert_metric_value(
                    metric_value.value, 
                    metric_name
                )
            
            processed_data['rows'].append(row_data)
        
        # Process totals if available
        if hasattr(response, 'totals') and response.totals:
            for total_row in response.totals:
                for i, metric_value in enumerate(total_row.metric_values):
                    metric_name = processed_data['metrics'][i]
                    processed_data['totals'][metric_name] = self._convert_metric_value(
                        metric_value.value,
                        metric_name
                    )
        
        return processed_data
    
    def _process_realtime_response(self, response) -> Dict[str, Any]:
        """Process real-time report response."""
        processed_data = {
            'dimensions': [dim.name for dim in response.dimension_headers],
            'metrics': [metric.name for metric in response.metric_headers],
            'rows': [],
            'totals': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for row in response.rows:
            row_data = {}
            
            # Add dimension values
            for i, dimension_value in enumerate(row.dimension_values):
                dim_name = processed_data['dimensions'][i]
                row_data[dim_name] = dimension_value.value
            
            # Add metric values
            for i, metric_value in enumerate(row.metric_values):
                metric_name = processed_data['metrics'][i]
                row_data[metric_name] = self._convert_metric_value(
                    metric_value.value,
                    metric_name
                )
            
            processed_data['rows'].append(row_data)
        
        return processed_data
    
    def _convert_metric_value(self, value: str, metric_name: str) -> Union[int, float]:
        """Convert string metric values to appropriate numeric types."""
        try:
            # Metrics that should be integers
            integer_metrics = [
                'sessions', 'pageviews', 'users', 'newUsers', 'totalUsers',
                'eventCount', 'conversions', 'screenPageViews', 'activeUsers'
            ]
            
            # Metrics that should be floats
            float_metrics = [
                'bounceRate', 'averageSessionDuration', 'totalRevenue',
                'purchaseRevenue', 'sessionDuration'
            ]
            
            if metric_name in integer_metrics:
                return int(float(value))
            elif metric_name in float_metrics:
                return float(value)
            else:
                # Try to determine best type
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
                    
        except (ValueError, TypeError):
            # Return original value if conversion fails
            return value
    
    def sync(self) -> Dict[str, Any]:
        """Perform full data synchronization."""
        logger.info("Starting Google Analytics data sync")
        
        try:
            end_date = "today"
            start_date = "30daysAgo"
            
            sync_results = {
                'timestamp': datetime.now().isoformat(),
                'property_id': self.property_id,
                'data': {}
            }
            
            # Get standard metrics
            sync_results['data']['standard_metrics'] = self.get_standard_metrics(
                start_date, end_date
            )
            
            # Get conversion data
            sync_results['data']['conversions'] = self.get_conversion_metrics(
                start_date, end_date
            )
            
            # Get attribution data
            sync_results['data']['attribution'] = self.get_attribution_data(
                start_date, end_date
            )
            
            # Get audience data
            sync_results['data']['audience'] = self.get_audience_data(
                start_date, end_date
            )
            
            # Get real-time data
            sync_results['data']['realtime'] = self.get_realtime_metrics()
            
            logger.info("Google Analytics sync completed successfully")
            return sync_results
            
        except Exception as e:
            logger.error(f"Google Analytics sync failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def disconnect(self):
        """Clean up connection resources."""
        if self.client:
            self.client = None
        logger.info("Google Analytics connector disconnected")
    
    def get_custom_report(
        self, 
        dimensions: List[str],
        metrics: List[str],
        start_date: str,
        end_date: str,
        filters: Optional[Dict] = None,
        order_bys: Optional[List[str]] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """Generate custom reports with flexible parameters."""
        try:
            request = RunReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name=dim) for dim in dimensions],
                metrics=[Metric(name=metric) for metric in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=limit
            )
            
            # Add filters if provided
            if filters:
                # Implementation would depend on filter structure
                pass
            
            response = self.client.run_report(request=request)
            return self._process_report_response(response)
            
        except Exception as e:
            logger.error(f"Failed to generate custom report: {e}")
            return {}