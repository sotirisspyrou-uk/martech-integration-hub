"""
LinkedIn Ads API Integration for MarTech Integration Hub

Comprehensive LinkedIn Marketing Solutions API integration for B2B campaign management,
lead generation, sponsored content, and professional audience targeting.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import urllib.parse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class LinkedInCampaignType(Enum):
    """LinkedIn Campaign types."""
    SPONSORED_CONTENT = "SPONSORED_CONTENT"
    SPONSORED_MESSAGING = "SPONSORED_MESSAGING"
    TEXT_ADS = "TEXT_ADS"
    DYNAMIC_ADS = "DYNAMIC_ADS"


class LinkedInObjective(Enum):
    """LinkedIn Campaign objectives."""
    BRAND_AWARENESS = "BRAND_AWARENESS"
    WEBSITE_VISITS = "WEBSITE_VISITS"
    ENGAGEMENT = "ENGAGEMENT"
    VIDEO_VIEWS = "VIDEO_VIEWS"
    LEAD_GENERATION = "LEAD_GENERATION"
    WEBSITE_CONVERSIONS = "WEBSITE_CONVERSIONS"
    JOB_APPLICANTS = "JOB_APPLICANTS"
    TALENT_LEADS = "TALENT_LEADS"


class LinkedInStatus(Enum):
    """LinkedIn entity status values."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    DRAFT = "DRAFT"
    PENDING_DELETION = "PENDING_DELETION"


class LinkedInBidType(Enum):
    """LinkedIn bid types."""
    CPC = "CPC"
    CPM = "CPM"
    CPS = "CPS"  # Cost per send for sponsored messaging


class LinkedInMatchType(Enum):
    """LinkedIn audience matching types."""
    EXACT = "EXACT"
    BROAD = "BROAD"


@dataclass
class LinkedInAccount:
    """LinkedIn Ad Account information."""
    account_id: str
    name: str
    type: str
    status: LinkedInStatus
    currency: str = "USD"
    version: str = "2"
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None
    reference: Optional[str] = None


@dataclass
class LinkedInCampaignGroup:
    """LinkedIn Campaign Group (Campaign) data structure."""
    campaign_group_id: str
    name: str
    account_id: str
    status: LinkedInStatus
    objective_type: LinkedInObjective
    campaign_type: LinkedInCampaignType
    cost_type: LinkedInBidType
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    run_schedule: Optional[Dict[str, Any]] = None
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None


@dataclass
class LinkedInCampaign:
    """LinkedIn Campaign (Ad Set) data structure."""
    campaign_id: str
    name: str
    campaign_group_id: str
    account_id: str
    status: LinkedInStatus
    cost_type: LinkedInBidType
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    unit_cost: Optional[float] = None
    targeting: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None


@dataclass
class LinkedInCreative:
    """LinkedIn Ad Creative data structure."""
    creative_id: str
    campaign_id: str
    status: LinkedInStatus
    type: str = "SPONSORED_CONTENT"
    variables: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    last_modified_time: Optional[datetime] = None


@dataclass
class LinkedInAnalytics:
    """LinkedIn Analytics data structure."""
    impressions: int = 0
    clicks: int = 0
    cost_in_local_currency: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    cpm: float = 0.0
    conversions: int = 0
    conversion_value_in_local_currency: float = 0.0
    video_views: int = 0
    video_completions: int = 0
    video_first_quartile_completions: int = 0
    video_midpoint_completions: int = 0
    video_third_quartile_completions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    follows: int = 0
    leads: int = 0
    date_range: Optional[Dict[str, str]] = None
    pivot_value: Optional[str] = None


class LinkedInAdsConnector:
    """
    LinkedIn Marketing Solutions API connector for B2B advertising.
    
    Features:
    - Campaign Group and Campaign management
    - Sponsored Content, Messaging, and Text Ads
    - Professional audience targeting
    - Lead generation forms
    - Video advertising
    - Analytics and reporting
    - Conversion tracking
    """
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        
        # Setup session headers
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'MarTech-Integration-Hub/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': '202311'
        })
        
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
        # Validate credentials
        self._validate_token()
        
        logger.info("LinkedIn Ads Connector initialized successfully")
    
    def _validate_token(self) -> bool:
        """Validate the access token."""
        try:
            url = f"{self.BASE_URL}/people/~"
            response = self._make_request('GET', url)
            
            if 'id' in response:
                logger.info(f"Token validated for LinkedIn user: {response.get('id')}")
                return True
            else:
                raise ValueError("Invalid access token")
                
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            # Continue for demo purposes
            logger.info("Running in demo mode")
            return False
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and error handling."""
        
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            # Return mock data for demo purposes
            return self._get_mock_response(url, method)
        except ValueError as e:
            logger.error(f"JSON parsing error: {e}")
            return {}
    
    def _get_mock_response(self, url: str, method: str) -> Dict[str, Any]:
        """Generate mock responses for demo purposes."""
        if "adAccountsV2" in url:
            return {
                "elements": [
                    {
                        "id": "123456789",
                        "name": "Demo B2B Marketing Account",
                        "type": "BUSINESS",
                        "status": "ACTIVE",
                        "currency": "USD",
                        "version": {"versionTag": "2"},
                        "createdTime": 1640995200000,
                        "lastModifiedTime": 1672531200000
                    }
                ]
            }
        elif "adCampaignGroupsV2" in url:
            return {
                "elements": [
                    {
                        "id": "987654321",
                        "name": "B2B Lead Generation Campaign",
                        "account": "urn:li:sponsoredAccount:123456789",
                        "status": "ACTIVE",
                        "objectiveType": "LEAD_GENERATION",
                        "type": "SPONSORED_CONTENT",
                        "costType": "CPC",
                        "dailyBudget": {"amount": "50.00", "currencyCode": "USD"},
                        "createdTime": 1672531200000,
                        "lastModifiedTime": 1672617600000
                    }
                ]
            }
        elif "adCampaignsV2" in url:
            return {
                "elements": [
                    {
                        "id": "456789123",
                        "name": "Tech Decision Makers - Software Demo",
                        "campaignGroup": "urn:li:sponsoredCampaignGroup:987654321",
                        "account": "urn:li:sponsoredAccount:123456789",
                        "status": "ACTIVE",
                        "costType": "CPC",
                        "unitCost": {"amount": "2.50", "currencyCode": "USD"},
                        "dailyBudget": {"amount": "25.00", "currencyCode": "USD"},
                        "targeting": {
                            "includedTargetingFacets": {
                                "titles": ["Software Engineer", "CTO", "VP of Engineering"],
                                "seniorities": ["SENIOR", "MANAGER", "VP", "CXO"],
                                "industries": ["IT_AND_SERVICES", "COMPUTER_SOFTWARE"]
                            }
                        },
                        "createdTime": 1672531200000
                    }
                ]
            }
        elif "adAnalyticsV2" in url:
            return {
                "elements": [
                    {
                        "impressions": 15420,
                        "clicks": 342,
                        "costInLocalCurrency": 855.0,
                        "ctr": 2.22,
                        "cpc": 2.50,
                        "cpm": 55.45,
                        "conversions": 23,
                        "conversionValueInLocalCurrency": 4600.0,
                        "videoViews": 8920,
                        "likes": 156,
                        "comments": 34,
                        "shares": 67,
                        "follows": 89,
                        "leads": 23,
                        "dateRange": {
                            "start": {"day": 1, "month": 1, "year": 2024},
                            "end": {"day": 31, "month": 1, "year": 2024}
                        }
                    }
                ]
            }
        else:
            return {}
    
    def get_ad_accounts(self) -> List[LinkedInAccount]:
        """Get list of LinkedIn ad accounts."""
        try:
            url = f"{self.BASE_URL}/adAccountsV2"
            params = {
                'q': 'search',
                'search': '(status:(values:List(ACTIVE)))'
            }
            
            response = self._make_request('GET', url, params=params)
            
            accounts = []
            for account_data in response.get('elements', []):
                account = LinkedInAccount(
                    account_id=account_data.get('id', ''),
                    name=account_data.get('name', ''),
                    type=account_data.get('type', 'BUSINESS'),
                    status=LinkedInStatus(account_data.get('status', 'ACTIVE')),
                    currency=account_data.get('currency', 'USD'),
                    version=account_data.get('version', {}).get('versionTag', '2'),
                    created_time=datetime.fromtimestamp(
                        account_data.get('createdTime', 0) / 1000
                    ) if account_data.get('createdTime') else None,
                    last_modified_time=datetime.fromtimestamp(
                        account_data.get('lastModifiedTime', 0) / 1000
                    ) if account_data.get('lastModifiedTime') else None,
                    reference=account_data.get('reference')
                )
                accounts.append(account)
            
            logger.info(f"Retrieved {len(accounts)} LinkedIn ad accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get ad accounts: {e}")
            return []
    
    def get_campaign_groups(self, account_id: str) -> List[LinkedInCampaignGroup]:
        """Get campaign groups (campaigns) for an account."""
        try:
            url = f"{self.BASE_URL}/adCampaignGroupsV2"
            params = {
                'q': 'search',
                'search': f'(account:(values:List(urn:li:sponsoredAccount:{account_id})))'
            }
            
            response = self._make_request('GET', url, params=params)
            
            campaign_groups = []
            for cg_data in response.get('elements', []):
                # Parse budget
                daily_budget = None
                total_budget = None
                
                if 'dailyBudget' in cg_data:
                    daily_budget = float(cg_data['dailyBudget'].get('amount', 0))
                if 'totalBudget' in cg_data:
                    total_budget = float(cg_data['totalBudget'].get('amount', 0))
                
                campaign_group = LinkedInCampaignGroup(
                    campaign_group_id=cg_data.get('id', ''),
                    name=cg_data.get('name', ''),
                    account_id=account_id,
                    status=LinkedInStatus(cg_data.get('status', 'ACTIVE')),
                    objective_type=LinkedInObjective(cg_data.get('objectiveType', 'WEBSITE_VISITS')),
                    campaign_type=LinkedInCampaignType(cg_data.get('type', 'SPONSORED_CONTENT')),
                    cost_type=LinkedInBidType(cg_data.get('costType', 'CPC')),
                    daily_budget=daily_budget,
                    total_budget=total_budget,
                    run_schedule=cg_data.get('runSchedule'),
                    created_time=datetime.fromtimestamp(
                        cg_data.get('createdTime', 0) / 1000
                    ) if cg_data.get('createdTime') else None,
                    last_modified_time=datetime.fromtimestamp(
                        cg_data.get('lastModifiedTime', 0) / 1000
                    ) if cg_data.get('lastModifiedTime') else None
                )
                campaign_groups.append(campaign_group)
            
            logger.info(f"Retrieved {len(campaign_groups)} campaign groups")
            return campaign_groups
            
        except Exception as e:
            logger.error(f"Failed to get campaign groups: {e}")
            return []
    
    def get_campaigns(self, account_id: str, campaign_group_id: Optional[str] = None) -> List[LinkedInCampaign]:
        """Get campaigns (ad sets) for an account or campaign group."""
        try:
            url = f"{self.BASE_URL}/adCampaignsV2"
            
            if campaign_group_id:
                search_query = f'(campaignGroup:(values:List(urn:li:sponsoredCampaignGroup:{campaign_group_id})))'
            else:
                search_query = f'(account:(values:List(urn:li:sponsoredAccount:{account_id})))'
            
            params = {
                'q': 'search',
                'search': search_query
            }
            
            response = self._make_request('GET', url, params=params)
            
            campaigns = []
            for campaign_data in response.get('elements', []):
                # Parse budget and unit cost
                daily_budget = None
                total_budget = None
                unit_cost = None
                
                if 'dailyBudget' in campaign_data:
                    daily_budget = float(campaign_data['dailyBudget'].get('amount', 0))
                if 'totalBudget' in campaign_data:
                    total_budget = float(campaign_data['totalBudget'].get('amount', 0))
                if 'unitCost' in campaign_data:
                    unit_cost = float(campaign_data['unitCost'].get('amount', 0))
                
                # Extract campaign group ID from URN
                cg_urn = campaign_data.get('campaignGroup', '')
                cg_id = cg_urn.split(':')[-1] if cg_urn else ''
                
                campaign = LinkedInCampaign(
                    campaign_id=campaign_data.get('id', ''),
                    name=campaign_data.get('name', ''),
                    campaign_group_id=cg_id,
                    account_id=account_id,
                    status=LinkedInStatus(campaign_data.get('status', 'ACTIVE')),
                    cost_type=LinkedInBidType(campaign_data.get('costType', 'CPC')),
                    daily_budget=daily_budget,
                    total_budget=total_budget,
                    unit_cost=unit_cost,
                    targeting=campaign_data.get('targeting', {}),
                    created_time=datetime.fromtimestamp(
                        campaign_data.get('createdTime', 0) / 1000
                    ) if campaign_data.get('createdTime') else None,
                    last_modified_time=datetime.fromtimestamp(
                        campaign_data.get('lastModifiedTime', 0) / 1000
                    ) if campaign_data.get('lastModifiedTime') else None
                )
                campaigns.append(campaign)
            
            logger.info(f"Retrieved {len(campaigns)} campaigns")
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            return []
    
    def get_creatives(self, account_id: str, campaign_id: Optional[str] = None) -> List[LinkedInCreative]:
        """Get creatives for an account or campaign."""
        try:
            url = f"{self.BASE_URL}/adCreativesV2"
            
            if campaign_id:
                search_query = f'(campaign:(values:List(urn:li:sponsoredCampaign:{campaign_id})))'
            else:
                search_query = f'(account:(values:List(urn:li:sponsoredAccount:{account_id})))'
            
            params = {
                'q': 'search',
                'search': search_query
            }
            
            response = self._make_request('GET', url, params=params)
            
            creatives = []
            for creative_data in response.get('elements', []):
                # Extract campaign ID from URN
                campaign_urn = creative_data.get('campaign', '')
                camp_id = campaign_urn.split(':')[-1] if campaign_urn else ''
                
                creative = LinkedInCreative(
                    creative_id=creative_data.get('id', ''),
                    campaign_id=camp_id,
                    status=LinkedInStatus(creative_data.get('status', 'ACTIVE')),
                    type=creative_data.get('type', 'SPONSORED_CONTENT'),
                    variables=creative_data.get('variables', {}),
                    created_time=datetime.fromtimestamp(
                        creative_data.get('createdTime', 0) / 1000
                    ) if creative_data.get('createdTime') else None,
                    last_modified_time=datetime.fromtimestamp(
                        creative_data.get('lastModifiedTime', 0) / 1000
                    ) if creative_data.get('lastModifiedTime') else None
                )
                creatives.append(creative)
            
            logger.info(f"Retrieved {len(creatives)} creatives")
            return creatives
            
        except Exception as e:
            logger.error(f"Failed to get creatives: {e}")
            return []
    
    def get_analytics(self, 
                     account_id: str,
                     date_from: Optional[datetime] = None,
                     date_to: Optional[datetime] = None,
                     pivot: str = "CAMPAIGN",
                     time_granularity: str = "DAILY",
                     fields: Optional[List[str]] = None) -> List[LinkedInAnalytics]:
        """Get analytics data for campaigns."""
        try:
            # Default date range (last 30 days)
            if not date_from:
                date_from = datetime.now() - timedelta(days=30)
            if not date_to:
                date_to = datetime.now()
            
            # Default fields
            if not fields:
                fields = [
                    'impressions', 'clicks', 'costInLocalCurrency', 'ctr', 'cpc', 'cpm',
                    'conversions', 'conversionValueInLocalCurrency',
                    'videoViews', 'videoCompletions', 'videoFirstQuartileCompletions',
                    'videoMidpointCompletions', 'videoThirdQuartileCompletions',
                    'likes', 'comments', 'shares', 'follows', 'leads'
                ]
            
            url = f"{self.BASE_URL}/adAnalyticsV2"
            
            params = {
                'q': 'analytics',
                'pivot': pivot,
                'timeGranularity': time_granularity,
                'dateRange.start.day': date_from.day,
                'dateRange.start.month': date_from.month,
                'dateRange.start.year': date_from.year,
                'dateRange.end.day': date_to.day,
                'dateRange.end.month': date_to.month,
                'dateRange.end.year': date_to.year,
                'campaigns[0]': f'urn:li:sponsoredAccount:{account_id}',
                'fields': ','.join(fields)
            }
            
            response = self._make_request('GET', url, params=params)
            
            analytics_list = []
            for analytics_data in response.get('elements', []):
                analytics = LinkedInAnalytics(
                    impressions=int(analytics_data.get('impressions', 0)),
                    clicks=int(analytics_data.get('clicks', 0)),
                    cost_in_local_currency=float(analytics_data.get('costInLocalCurrency', 0)),
                    ctr=float(analytics_data.get('ctr', 0)),
                    cpc=float(analytics_data.get('cpc', 0)),
                    cpm=float(analytics_data.get('cpm', 0)),
                    conversions=int(analytics_data.get('conversions', 0)),
                    conversion_value_in_local_currency=float(analytics_data.get('conversionValueInLocalCurrency', 0)),
                    video_views=int(analytics_data.get('videoViews', 0)),
                    video_completions=int(analytics_data.get('videoCompletions', 0)),
                    video_first_quartile_completions=int(analytics_data.get('videoFirstQuartileCompletions', 0)),
                    video_midpoint_completions=int(analytics_data.get('videoMidpointCompletions', 0)),
                    video_third_quartile_completions=int(analytics_data.get('videoThirdQuartileCompletions', 0)),
                    likes=int(analytics_data.get('likes', 0)),
                    comments=int(analytics_data.get('comments', 0)),
                    shares=int(analytics_data.get('shares', 0)),
                    follows=int(analytics_data.get('follows', 0)),
                    leads=int(analytics_data.get('leads', 0)),
                    date_range=analytics_data.get('dateRange'),
                    pivot_value=analytics_data.get('pivotValue')
                )
                analytics_list.append(analytics)
            
            logger.info(f"Retrieved {len(analytics_list)} analytics records")
            return analytics_list
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return []
    
    def create_campaign_group(self, 
                             account_id: str,
                             name: str,
                             objective_type: LinkedInObjective,
                             campaign_type: LinkedInCampaignType = LinkedInCampaignType.SPONSORED_CONTENT,
                             cost_type: LinkedInBidType = LinkedInBidType.CPC,
                             daily_budget: Optional[float] = None,
                             total_budget: Optional[float] = None) -> Optional[str]:
        """Create a new campaign group."""
        try:
            url = f"{self.BASE_URL}/adCampaignGroupsV2"
            
            data = {
                'name': name,
                'account': f'urn:li:sponsoredAccount:{account_id}',
                'status': 'PAUSED',  # Start paused for safety
                'objectiveType': objective_type.value,
                'type': campaign_type.value,
                'costType': cost_type.value
            }
            
            # Add budget
            if daily_budget:
                data['dailyBudget'] = {
                    'amount': str(daily_budget),
                    'currencyCode': 'USD'
                }
            elif total_budget:
                data['totalBudget'] = {
                    'amount': str(total_budget),
                    'currencyCode': 'USD'
                }
            else:
                raise ValueError("Either daily_budget or total_budget must be specified")
            
            response = self._make_request('POST', url, json=data)
            
            campaign_group_id = response.get('id')
            logger.info(f"Created campaign group {campaign_group_id}: {name}")
            return campaign_group_id
            
        except Exception as e:
            logger.error(f"Failed to create campaign group: {e}")
            return None
    
    def create_campaign(self,
                       account_id: str,
                       campaign_group_id: str,
                       name: str,
                       targeting: Dict[str, Any],
                       cost_type: LinkedInBidType = LinkedInBidType.CPC,
                       unit_cost: Optional[float] = None,
                       daily_budget: Optional[float] = None) -> Optional[str]:
        """Create a new campaign."""
        try:
            url = f"{self.BASE_URL}/adCampaignsV2"
            
            data = {
                'name': name,
                'account': f'urn:li:sponsoredAccount:{account_id}',
                'campaignGroup': f'urn:li:sponsoredCampaignGroup:{campaign_group_id}',
                'status': 'PAUSED',  # Start paused for safety
                'costType': cost_type.value,
                'targeting': targeting
            }
            
            # Add unit cost
            if unit_cost:
                data['unitCost'] = {
                    'amount': str(unit_cost),
                    'currencyCode': 'USD'
                }
            
            # Add daily budget
            if daily_budget:
                data['dailyBudget'] = {
                    'amount': str(daily_budget),
                    'currencyCode': 'USD'
                }
            
            response = self._make_request('POST', url, json=data)
            
            campaign_id = response.get('id')
            logger.info(f"Created campaign {campaign_id}: {name}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return None
    
    def update_campaign_status(self, campaign_id: str, status: LinkedInStatus) -> bool:
        """Update campaign status."""
        try:
            url = f"{self.BASE_URL}/adCampaignsV2/{campaign_id}"
            data = {'status': status.value}
            
            response = self._make_request('PATCH', url, json=data)
            
            success = 'id' in response
            logger.info(f"Updated campaign {campaign_id} status to {status.value}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update campaign status: {e}")
            return False
    
    def update_campaign_budget(self, campaign_id: str, daily_budget: Optional[float] = None, unit_cost: Optional[float] = None) -> bool:
        """Update campaign budget or bid."""
        try:
            url = f"{self.BASE_URL}/adCampaignsV2/{campaign_id}"
            data = {}
            
            if daily_budget:
                data['dailyBudget'] = {
                    'amount': str(daily_budget),
                    'currencyCode': 'USD'
                }
            
            if unit_cost:
                data['unitCost'] = {
                    'amount': str(unit_cost),
                    'currencyCode': 'USD'
                }
            
            if not data:
                raise ValueError("Either daily_budget or unit_cost must be specified")
            
            response = self._make_request('PATCH', url, json=data)
            
            success = 'id' in response
            logger.info(f"Updated campaign {campaign_id} budget: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update campaign budget: {e}")
            return False
    
    def get_targeting_facets(self, facet_type: str) -> List[Dict[str, Any]]:
        """Get available targeting facets (industries, job functions, etc.)."""
        try:
            url = f"{self.BASE_URL}/adTargetingFacets"
            params = {
                'facetType': facet_type.upper()
            }
            
            response = self._make_request('GET', url, params=params)
            
            facets = response.get('elements', [])
            logger.info(f"Retrieved {len(facets)} {facet_type} targeting facets")
            return facets
            
        except Exception as e:
            logger.error(f"Failed to get targeting facets: {e}")
            return []
    
    def get_account_analytics_summary(self, account_id: str, days: int = 30) -> Dict[str, Any]:
        """Get account-level analytics summary."""
        try:
            analytics_data = self.get_analytics(
                account_id=account_id,
                date_from=datetime.now() - timedelta(days=days),
                date_to=datetime.now(),
                pivot="ACCOUNT"
            )
            
            if not analytics_data:
                return {}
            
            # Aggregate data
            total_analytics = LinkedInAnalytics()
            for daily_data in analytics_data:
                total_analytics.impressions += daily_data.impressions
                total_analytics.clicks += daily_data.clicks
                total_analytics.cost_in_local_currency += daily_data.cost_in_local_currency
                total_analytics.conversions += daily_data.conversions
                total_analytics.conversion_value_in_local_currency += daily_data.conversion_value_in_local_currency
                total_analytics.video_views += daily_data.video_views
                total_analytics.video_completions += daily_data.video_completions
                total_analytics.likes += daily_data.likes
                total_analytics.comments += daily_data.comments
                total_analytics.shares += daily_data.shares
                total_analytics.follows += daily_data.follows
                total_analytics.leads += daily_data.leads
            
            # Calculate derived metrics
            summary = {
                'account_id': account_id,
                'period_days': days,
                'total_spend': total_analytics.cost_in_local_currency,
                'total_impressions': total_analytics.impressions,
                'total_clicks': total_analytics.clicks,
                'total_conversions': total_analytics.conversions,
                'total_leads': total_analytics.leads,
                'total_video_views': total_analytics.video_views,
                'total_engagement': total_analytics.likes + total_analytics.comments + total_analytics.shares,
                'average_cpc': total_analytics.cost_in_local_currency / max(total_analytics.clicks, 1),
                'average_cpm': (total_analytics.cost_in_local_currency / max(total_analytics.impressions, 1)) * 1000,
                'average_ctr': (total_analytics.clicks / max(total_analytics.impressions, 1)) * 100,
                'conversion_rate': (total_analytics.conversions / max(total_analytics.clicks, 1)) * 100,
                'cost_per_conversion': total_analytics.cost_in_local_currency / max(total_analytics.conversions, 1),
                'cost_per_lead': total_analytics.cost_in_local_currency / max(total_analytics.leads, 1),
                'roas': total_analytics.conversion_value_in_local_currency / max(total_analytics.cost_in_local_currency, 1),
                'video_completion_rate': (total_analytics.video_completions / max(total_analytics.video_views, 1)) * 100,
                'engagement_rate': ((total_analytics.likes + total_analytics.comments + total_analytics.shares) / max(total_analytics.impressions, 1)) * 100
            }
            
            logger.info(f"Generated analytics summary for account {account_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate analytics summary: {e}")
            return {}
    
    def get_b2b_targeting_recommendations(self, account_id: str, industry: str, job_function: str) -> Dict[str, Any]:
        """Get B2B targeting recommendations based on industry and job function."""
        try:
            # Get targeting facets for industries and job functions
            industry_facets = self.get_targeting_facets('INDUSTRIES')
            job_function_facets = self.get_targeting_facets('JOB_FUNCTIONS')
            seniority_facets = self.get_targeting_facets('SENIORITIES')
            
            # Find relevant facets
            relevant_industries = [f for f in industry_facets if industry.lower() in f.get('name', '').lower()]
            relevant_functions = [f for f in job_function_facets if job_function.lower() in f.get('name', '').lower()]
            
            # Create targeting recommendations
            targeting_config = {
                'includedTargetingFacets': {
                    'industries': [f.get('id') for f in relevant_industries[:5]],
                    'jobFunctions': [f.get('id') for f in relevant_functions[:3]],
                    'seniorities': ['SENIOR', 'MANAGER', 'VP', 'CXO'],  # Target decision makers
                    'locations': ['us:0'],  # US targeting (example)
                    'degrees': ['BA', 'MA', 'MBA']  # Professional education
                }
            }
            
            # Calculate estimated audience size (mock calculation)
            estimated_reach = len(relevant_industries) * len(relevant_functions) * 50000
            
            recommendations = {
                'targeting_config': targeting_config,
                'estimated_reach': min(estimated_reach, 1000000),  # Cap at 1M
                'recommended_bid_range': {
                    'min_cpc': 2.50,
                    'max_cpc': 8.00,
                    'suggested_cpc': 4.25
                },
                'campaign_suggestions': {
                    'daily_budget_range': {
                        'min': 25,
                        'recommended': 100,
                        'max': 500
                    },
                    'content_types': ['SPONSORED_CONTENT', 'SPONSORED_MESSAGING'],
                    'objectives': ['LEAD_GENERATION', 'WEBSITE_CONVERSIONS', 'BRAND_AWARENESS']
                },
                'best_practices': [
                    'Use professional, business-focused creative content',
                    'Highlight specific business value propositions',
                    'Target during business hours for better engagement',
                    'Use LinkedIn Lead Gen Forms for higher conversion rates',
                    'Test different seniority levels to optimize reach vs. quality'
                ]
            }
            
            logger.info(f"Generated B2B targeting recommendations for {industry} - {job_function}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate targeting recommendations: {e}")
            return {}
    
    def optimize_campaigns_for_leads(self, account_id: str) -> Dict[str, Any]:
        """Optimize campaigns specifically for lead generation performance."""
        try:
            campaigns = self.get_campaigns(account_id)
            analytics_data = self.get_analytics(
                account_id=account_id,
                date_from=datetime.now() - timedelta(days=14)  # Last 2 weeks
            )
            
            optimization_results = {
                'processed_campaigns': 0,
                'paused_campaigns': [],
                'budget_increased': [],
                'bid_adjustments': [],
                'recommendations': []
            }
            
            for campaign in campaigns:
                if campaign.status != LinkedInStatus.ACTIVE:
                    continue
                
                # Get campaign-specific analytics
                campaign_analytics = [a for a in analytics_data if a.pivot_value == campaign.campaign_id]
                
                if not campaign_analytics:
                    continue
                
                # Aggregate metrics
                total_cost = sum(a.cost_in_local_currency for a in campaign_analytics)
                total_leads = sum(a.leads for a in campaign_analytics)
                total_clicks = sum(a.clicks for a in campaign_analytics)
                
                # Calculate cost per lead
                cost_per_lead = total_cost / max(total_leads, 1)
                click_to_lead_rate = (total_leads / max(total_clicks, 1)) * 100
                
                # Optimization logic
                if cost_per_lead > 50 and total_leads < 5:  # High cost, low leads
                    # Pause underperforming campaigns
                    success = self.update_campaign_status(campaign.campaign_id, LinkedInStatus.PAUSED)
                    if success:
                        optimization_results['paused_campaigns'].append({
                            'campaign_id': campaign.campaign_id,
                            'name': campaign.name,
                            'cost_per_lead': cost_per_lead,
                            'total_leads': total_leads
                        })
                
                elif cost_per_lead < 25 and total_leads > 10:  # Good performance
                    # Increase budget for high performers
                    if campaign.daily_budget and campaign.daily_budget < 200:
                        new_budget = min(campaign.daily_budget * 1.3, 200)  # Increase by 30%, cap at $200
                        success = self.update_campaign_budget(campaign.campaign_id, daily_budget=new_budget)
                        if success:
                            optimization_results['budget_increased'].append({
                                'campaign_id': campaign.campaign_id,
                                'name': campaign.name,
                                'old_budget': campaign.daily_budget,
                                'new_budget': new_budget,
                                'cost_per_lead': cost_per_lead
                            })
                
                elif click_to_lead_rate < 5 and campaign.unit_cost:  # Low conversion rate
                    # Reduce bid to get more qualified traffic
                    new_bid = campaign.unit_cost * 0.8  # Reduce by 20%
                    success = self.update_campaign_budget(campaign.campaign_id, unit_cost=new_bid)
                    if success:
                        optimization_results['bid_adjustments'].append({
                            'campaign_id': campaign.campaign_id,
                            'name': campaign.name,
                            'old_bid': campaign.unit_cost,
                            'new_bid': new_bid,
                            'click_to_lead_rate': click_to_lead_rate
                        })
                
                optimization_results['processed_campaigns'] += 1
            
            # Generate recommendations
            if len(optimization_results['paused_campaigns']) > 0:
                optimization_results['recommendations'].append(
                    "Review paused campaigns' targeting and creative to improve performance"
                )
            
            if len(optimization_results['budget_increased']) > 0:
                optimization_results['recommendations'].append(
                    "Monitor increased budgets closely to maintain cost per lead efficiency"
                )
            
            if len(optimization_results['bid_adjustments']) > 0:
                optimization_results['recommendations'].append(
                    "Test new creative variations for campaigns with reduced bids to improve conversion rates"
                )
            
            logger.info(f"Campaign optimization completed for {optimization_results['processed_campaigns']} campaigns")
            return optimization_results
            
        except Exception as e:
            logger.error(f"Campaign optimization failed: {e}")
            return {'error': str(e)}


def create_sample_linkedin_connector() -> Optional[LinkedInAdsConnector]:
    """Create a sample LinkedIn Ads connector for demonstration."""
    
    # This would be a real access token in production
    sample_access_token = "demo_linkedin_access_token_12345"
    
    try:
        # This would work with real credentials
        connector = LinkedInAdsConnector(access_token=sample_access_token)
        return connector
    except:
        # Return a mock connector for demo purposes
        logger.info("Creating demo LinkedIn Ads connector (credentials not valid)")
        return None


def run_linkedin_ads_demo():
    """
    Run the LinkedIn Ads connector demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("💼 LinkedIn Ads API Connector Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • B2B campaign management")
    print("  • Professional audience targeting")
    print("  • Lead generation optimization")
    print("  • Sponsored Content & Messaging")
    print("  • Video advertising")
    print("  • Analytics and reporting")
    print("  • Conversion tracking")
    
    print("\n📊 B2B Marketing Capabilities:")
    print("  • Job title and seniority targeting")
    print("  • Industry and company size filtering")
    print("  • Skills and education targeting")
    print("  • Account-based marketing (ABM)")
    print("  • Lead generation forms")
    print("  • Cost-per-lead optimization")
    
    print("\n📈 Available Campaign Types:")
    for campaign_type in LinkedInCampaignType:
        print(f"  • {campaign_type.value}")
    
    print("\n🎯 Campaign Objectives:")
    for objective in LinkedInObjective:
        print(f"  • {objective.value}")
    
    print("\n💰 Bid Types:")
    for bid_type in LinkedInBidType:
        print(f"  • {bid_type.value}")
    
    # Demonstrate connector initialization
    print("\n🚀 Initializing LinkedIn Ads connector...")
    connector = create_sample_linkedin_connector()
    
    if connector:
        print("✅ Connector initialized successfully")
        
        # Example usage
        print("\n📋 Example Operations:")
        print("  • Get ad accounts: connector.get_ad_accounts()")
        print("  • Get campaign groups: connector.get_campaign_groups(account_id)")
        print("  • Get campaigns: connector.get_campaigns(account_id)")
        print("  • Get analytics: connector.get_analytics(account_id)")
        print("  • Optimize for leads: connector.optimize_campaigns_for_leads(account_id)")
        
    else:
        print("ℹ️  Demo mode - connector requires valid LinkedIn credentials")
        print("   In production, use real access tokens from LinkedIn Developer Program")
    
    # Sample analytics data
    print("\n📊 Sample B2B Performance Data:")
    sample_data = LinkedInAnalytics(
        impressions=15420,
        clicks=342,
        cost_in_local_currency=855.0,
        ctr=2.22,
        cpc=2.50,
        cpm=55.45,
        conversions=23,
        conversion_value_in_local_currency=4600.0,
        video_views=8920,
        likes=156,
        comments=34,
        shares=67,
        follows=89,
        leads=23
    )
    
    print(f"   • Impressions: {sample_data.impressions:,}")
    print(f"   • Clicks: {sample_data.clicks:,}")
    print(f"   • Spend: ${sample_data.cost_in_local_currency:,.2f}")
    print(f"   • CTR: {sample_data.ctr:.2f}%")
    print(f"   • CPC: ${sample_data.cpc:.2f}")
    print(f"   • CPM: ${sample_data.cpm:.2f}")
    print(f"   • Leads: {sample_data.leads}")
    print(f"   • Cost per Lead: ${sample_data.cost_in_local_currency / max(sample_data.leads, 1):.2f}")
    print(f"   • Engagement: {sample_data.likes + sample_data.comments + sample_data.shares}")
    print(f"   • Video Views: {sample_data.video_views:,}")
    
    # Sample B2B targeting
    print("\n🎯 Sample B2B Targeting Configuration:")
    targeting_example = {
        'industries': ['IT and Services', 'Computer Software', 'Financial Services'],
        'job_functions': ['Engineering', 'Information Technology', 'Operations'],
        'seniorities': ['Manager', 'Director', 'VP', 'CXO'],
        'company_sizes': ['51-200', '201-500', '501-1000', '1001-5000'],
        'degrees': ['Bachelor', 'Master', 'MBA']
    }
    
    for category, values in targeting_example.items():
        print(f"   • {category.title()}: {', '.join(values[:3])}...")
    
    # Sample optimization results
    print("\n⚙️  Sample Lead Generation Optimization:")
    optimization_sample = {
        'campaigns_processed': 12,
        'campaigns_paused': 3,
        'budgets_increased': 2,
        'bids_adjusted': 4,
        'estimated_cost_savings': 245.50,
        'estimated_lead_increase': 15
    }
    
    print(f"   • Campaigns Processed: {optimization_sample['campaigns_processed']}")
    print(f"   • Underperformers Paused: {optimization_sample['campaigns_paused']}")
    print(f"   • High Performer Budgets Increased: {optimization_sample['budgets_increased']}")
    print(f"   • Bid Adjustments Made: {optimization_sample['bids_adjusted']}")
    print(f"   • Estimated Monthly Savings: ${optimization_sample['estimated_cost_savings']:.2f}")
    print(f"   • Estimated Additional Leads: {optimization_sample['estimated_lead_increase']}")
    
    print("\n🌟 Advanced B2B Features:")
    print("  • Account-based marketing (ABM) targeting")
    print("  • Lead generation form integration")
    print("  • Professional demographic targeting")
    print("  • Company and industry insights")
    print("  • Video advertising for B2B content")
    print("  • Conversion tracking and attribution")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return connector


if __name__ == "__main__":
    run_linkedin_ads_demo()

