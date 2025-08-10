import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
from hubspot.crm.companies import SimplePublicObjectInput as CompanyInput
from hubspot.crm.deals import SimplePublicObjectInput as DealInput
from config.settings import settings

logger = logging.getLogger(__name__)


class HubSpotConnector:
    """
    HubSpot API integration for marketing automation and CRM data.
    Contact lifecycle management, campaign tracking, and lead nurturing workflows.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.hubspot_api_key
        self.client = None
        self.session = None
        self.base_url = "https://api.hubapi.com"
        self.last_sync = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HubSpot API client."""
        try:
            if self.api_key:
                self.client = HubSpot(api_key=self.api_key)
                
                # Set up requests session for additional API calls
                self.session = requests.Session()
                self.session.headers.update({
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                })
                
                # Configure retry strategy
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    method_whitelist=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH"],
                    backoff_factor=1
                )
                
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self.session.mount("http://", adapter)
                self.session.mount("https://", adapter)
                
                logger.info("HubSpot client initialized successfully")
            else:
                logger.error("HubSpot API key not provided")
                
        except Exception as e:
            logger.error(f"Failed to initialize HubSpot client: {e}")
            raise
    
    def connect(self) -> bool:
        """Test connection to HubSpot API."""
        try:
            # Test connection by fetching account info
            url = f"{self.base_url}/account-info/v3/details"
            response = self.session.get(url)
            response.raise_for_status()
            
            account_info = response.json()
            logger.info(f"Connected to HubSpot account: {account_info.get('companyName', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"HubSpot connection test failed: {e}")
            return False
    
    def get_contacts(
        self, 
        limit: int = 100,
        properties: Optional[List[str]] = None,
        last_modified_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get contacts from HubSpot with optional filtering."""
        try:
            if not properties:
                properties = [
                    'email', 'firstname', 'lastname', 'company', 'phone', 'website',
                    'jobtitle', 'industry', 'lifecyclestage', 'hubspotscore',
                    'createdate', 'lastmodifieddate', 'hs_lead_status',
                    'hs_analytics_source', 'hs_analytics_source_data_1',
                    'hs_analytics_source_data_2', 'hs_latest_source',
                    'hs_latest_source_data_1', 'hs_latest_source_data_2'
                ]
            
            all_contacts = []
            after = None
            
            while True:
                try:
                    api_response = self.client.crm.contacts.basic_api.get_page(
                        limit=min(limit, 100),  # HubSpot max is 100 per page
                        properties=properties,
                        after=after
                    )
                    
                    contacts_batch = []
                    for contact in api_response.results:
                        contact_dict = {
                            'id': contact.id,
                            'properties': contact.properties
                        }
                        
                        # Filter by last modified date if provided
                        if last_modified_date:
                            contact_modified = contact.properties.get('lastmodifieddate')
                            if contact_modified:
                                contact_date = datetime.fromisoformat(contact_modified.replace('Z', '+00:00'))
                                if contact_date < last_modified_date:
                                    continue
                        
                        contacts_batch.append(contact_dict)
                    
                    all_contacts.extend(contacts_batch)
                    
                    # Check if we have more pages or reached limit
                    if not api_response.paging or not api_response.paging.next or len(all_contacts) >= limit:
                        break
                    
                    after = api_response.paging.next.after
                    
                except ApiException as e:
                    logger.error(f"Error fetching contacts batch: {e}")
                    break
            
            return all_contacts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            return []
    
    def get_companies(
        self, 
        limit: int = 100,
        properties: Optional[List[str]] = None,
        last_modified_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get companies from HubSpot."""
        try:
            if not properties:
                properties = [
                    'name', 'domain', 'industry', 'annualrevenue', 'numberofemployees',
                    'phone', 'city', 'state', 'country', 'website', 'type',
                    'createdate', 'lastmodifieddate', 'hs_analytics_source'
                ]
            
            all_companies = []
            after = None
            
            while True:
                try:
                    api_response = self.client.crm.companies.basic_api.get_page(
                        limit=min(limit, 100),
                        properties=properties,
                        after=after
                    )
                    
                    companies_batch = []
                    for company in api_response.results:
                        company_dict = {
                            'id': company.id,
                            'properties': company.properties
                        }
                        
                        if last_modified_date:
                            company_modified = company.properties.get('lastmodifieddate')
                            if company_modified:
                                company_date = datetime.fromisoformat(company_modified.replace('Z', '+00:00'))
                                if company_date < last_modified_date:
                                    continue
                        
                        companies_batch.append(company_dict)
                    
                    all_companies.extend(companies_batch)
                    
                    if not api_response.paging or not api_response.paging.next or len(all_companies) >= limit:
                        break
                    
                    after = api_response.paging.next.after
                    
                except ApiException as e:
                    logger.error(f"Error fetching companies batch: {e}")
                    break
            
            return all_companies[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get companies: {e}")
            return []
    
    def get_deals(
        self, 
        limit: int = 100,
        properties: Optional[List[str]] = None,
        last_modified_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get deals/opportunities from HubSpot."""
        try:
            if not properties:
                properties = [
                    'dealname', 'amount', 'dealstage', 'pipeline', 'closedate',
                    'createdate', 'lastmodifieddate', 'hubspot_owner_id',
                    'dealtype', 'hs_analytics_source', 'hs_campaign'
                ]
            
            all_deals = []
            after = None
            
            while True:
                try:
                    api_response = self.client.crm.deals.basic_api.get_page(
                        limit=min(limit, 100),
                        properties=properties,
                        after=after
                    )
                    
                    deals_batch = []
                    for deal in api_response.results:
                        deal_dict = {
                            'id': deal.id,
                            'properties': deal.properties
                        }
                        
                        if last_modified_date:
                            deal_modified = deal.properties.get('lastmodifieddate')
                            if deal_modified:
                                deal_date = datetime.fromisoformat(deal_modified.replace('Z', '+00:00'))
                                if deal_date < last_modified_date:
                                    continue
                        
                        deals_batch.append(deal_dict)
                    
                    all_deals.extend(deals_batch)
                    
                    if not api_response.paging or not api_response.paging.next or len(all_deals) >= limit:
                        break
                    
                    after = api_response.paging.next.after
                    
                except ApiException as e:
                    logger.error(f"Error fetching deals batch: {e}")
                    break
            
            return all_deals[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get deals: {e}")
            return []
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Optional[str]:
        """Create a new contact in HubSpot."""
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=contact_data)
            api_response = self.client.crm.contacts.basic_api.create(
                simple_public_object_input=simple_public_object_input
            )
            
            contact_id = api_response.id
            logger.info(f"Successfully created HubSpot contact with ID: {contact_id}")
            return contact_id
            
        except ApiException as e:
            logger.error(f"Failed to create HubSpot contact: {e}")
            return None
    
    def update_contact(self, contact_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing contact in HubSpot."""
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=update_data)
            self.client.crm.contacts.basic_api.update(
                contact_id=contact_id,
                simple_public_object_input=simple_public_object_input
            )
            
            logger.info(f"Successfully updated HubSpot contact: {contact_id}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to update HubSpot contact {contact_id}: {e}")
            return False
    
    def get_contact_lifecycle_stages(self) -> List[Dict[str, Any]]:
        """Get available lifecycle stages."""
        try:
            url = f"{self.base_url}/properties/v1/contacts/properties/lifecyclestage"
            response = self.session.get(url)
            response.raise_for_status()
            
            property_info = response.json()
            return property_info.get('options', [])
            
        except Exception as e:
            logger.error(f"Failed to get lifecycle stages: {e}")
            return []
    
    def get_campaigns(self) -> List[Dict[str, Any]]:
        """Get marketing campaigns from HubSpot."""
        try:
            url = f"{self.base_url}/marketing/v3/campaigns"
            response = self.session.get(url)
            response.raise_for_status()
            
            campaigns_data = response.json()
            return campaigns_data.get('results', [])
            
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            return []
    
    def get_email_campaigns(self) -> List[Dict[str, Any]]:
        """Get email campaign performance data."""
        try:
            url = f"{self.base_url}/email/public/v1/campaigns"
            response = self.session.get(url)
            response.raise_for_status()
            
            campaigns_data = response.json()
            return campaigns_data.get('campaigns', [])
            
        except Exception as e:
            logger.error(f"Failed to get email campaigns: {e}")
            return []
    
    def get_forms(self) -> List[Dict[str, Any]]:
        """Get forms and their submission data."""
        try:
            url = f"{self.base_url}/forms/v2/forms"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get forms: {e}")
            return []
    
    def get_form_submissions(self, form_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get submissions for a specific form."""
        try:
            url = f"{self.base_url}/form-integrations/v1/submissions/forms/{form_id}"
            params = {'limit': limit}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            submissions_data = response.json()
            return submissions_data.get('results', [])
            
        except Exception as e:
            logger.error(f"Failed to get form submissions for form {form_id}: {e}")
            return []
    
    def get_contact_analytics(self, contact_id: str) -> Dict[str, Any]:
        """Get analytics data for a specific contact."""
        try:
            # Get contact timeline
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}/associations/emails"
            response = self.session.get(url)
            
            analytics_data = {'contact_id': contact_id, 'timeline': []}
            
            if response.status_code == 200:
                email_data = response.json()
                analytics_data['emails'] = email_data.get('results', [])
            
            # Get page views if available
            timeline_url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            timeline_response = self.session.get(timeline_url)
            
            if timeline_response.status_code == 200:
                contact_data = timeline_response.json()
                analytics_data['properties'] = contact_data.get('properties', {})
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get contact analytics for {contact_id}: {e}")
            return {}
    
    def track_lead_nurturing(self, contact_id: str) -> Dict[str, Any]:
        """Track lead nurturing campaign engagement."""
        try:
            # Get contact's campaign memberships and email engagement
            url = f"{self.base_url}/crm/v3/objects/contacts/{contact_id}"
            params = {
                'properties': [
                    'hs_lead_status', 'lifecyclestage', 'hubspotscore',
                    'num_associated_deals', 'recent_deal_amount',
                    'hs_email_open', 'hs_email_click', 'hs_email_bounce'
                ]
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            contact_data = response.json()
            
            nurturing_data = {
                'contact_id': contact_id,
                'current_stage': contact_data['properties'].get('lifecyclestage'),
                'lead_score': contact_data['properties'].get('hubspotscore'),
                'email_engagement': {
                    'opens': contact_data['properties'].get('hs_email_open', 0),
                    'clicks': contact_data['properties'].get('hs_email_click', 0),
                    'bounces': contact_data['properties'].get('hs_email_bounce', 0)
                }
            }
            
            return nurturing_data
            
        except Exception as e:
            logger.error(f"Failed to track lead nurturing for {contact_id}: {e}")
            return {}
    
    def bulk_update_contacts(self, contact_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple contacts."""
        try:
            results = {'success': 0, 'errors': 0, 'details': []}
            
            # HubSpot batch API allows up to 100 objects per batch
            batch_size = 100
            
            for i in range(0, len(contact_updates), batch_size):
                batch = contact_updates[i:i + batch_size]
                
                try:
                    batch_input = []
                    for update in batch:
                        contact_input = SimplePublicObjectInput(
                            properties=update['properties']
                        )
                        contact_input.id = update['id']
                        batch_input.append(contact_input)
                    
                    # Use batch update API
                    api_response = self.client.crm.contacts.batch_api.update(
                        batch_input_simple_public_object_batch_input={'inputs': batch_input}
                    )
                    
                    for result in api_response.results:
                        results['success'] += 1
                        results['details'].append({
                            'id': result.id,
                            'action': 'updated'
                        })
                        
                except ApiException as e:
                    results['errors'] += len(batch)
                    results['details'].append({
                        'error': f"Batch update failed: {str(e)}"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk contact update failed: {e}")
            return {'success': 0, 'errors': len(contact_updates), 'error': str(e)}
    
    def sync(self) -> Dict[str, Any]:
        """Perform full data synchronization."""
        logger.info("Starting HubSpot data sync")
        
        try:
            sync_start = datetime.now()
            
            # Determine sync period
            if self.last_sync:
                since_date = self.last_sync
            else:
                since_date = datetime.now() - timedelta(days=30)
            
            sync_results = {
                'timestamp': sync_start.isoformat(),
                'sync_period_start': since_date.isoformat(),
                'data': {},
                'summary': {}
            }
            
            # Sync contacts
            contacts = self.get_contacts(limit=1000, last_modified_date=since_date)
            sync_results['data']['contacts'] = contacts
            sync_results['summary']['contacts_count'] = len(contacts)
            
            # Sync companies
            companies = self.get_companies(limit=1000, last_modified_date=since_date)
            sync_results['data']['companies'] = companies
            sync_results['summary']['companies_count'] = len(companies)
            
            # Sync deals
            deals = self.get_deals(limit=1000, last_modified_date=since_date)
            sync_results['data']['deals'] = deals
            sync_results['summary']['deals_count'] = len(deals)
            
            # Get campaigns
            campaigns = self.get_campaigns()
            sync_results['data']['campaigns'] = campaigns
            sync_results['summary']['campaigns_count'] = len(campaigns)
            
            # Get email campaigns
            email_campaigns = self.get_email_campaigns()
            sync_results['data']['email_campaigns'] = email_campaigns
            sync_results['summary']['email_campaigns_count'] = len(email_campaigns)
            
            # Get forms
            forms = self.get_forms()
            sync_results['data']['forms'] = forms
            sync_results['summary']['forms_count'] = len(forms)
            
            self.last_sync = sync_start
            sync_results['sync_duration'] = (datetime.now() - sync_start).total_seconds()
            
            logger.info(f"HubSpot sync completed successfully in {sync_results['sync_duration']:.2f} seconds")
            return sync_results
            
        except Exception as e:
            logger.error(f"HubSpot sync failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def disconnect(self):
        """Clean up connection resources."""
        if self.session:
            self.session.close()
        
        self.client = None
        logger.info("HubSpot connector disconnected")