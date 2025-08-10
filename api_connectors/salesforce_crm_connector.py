import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import settings

logger = logging.getLogger(__name__)


class SalesforceConnector:
    """
    Salesforce API integration for lead and opportunity data.
    Custom field mapping, real-time sync, and marketing qualified lead tracking.
    """
    
    def __init__(
        self, 
        username: Optional[str] = None,
        password: Optional[str] = None,
        security_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        instance_url: Optional[str] = None,
        api_version: str = "58.0"
    ):
        self.username = username or settings.salesforce_username
        self.password = password or settings.salesforce_password
        self.security_token = security_token or settings.salesforce_security_token
        self.client_id = client_id or settings.salesforce_client_id
        self.client_secret = client_secret or settings.salesforce_client_secret
        self.instance_url = instance_url
        self.api_version = api_version
        
        self.session = None
        self.access_token = None
        self.last_sync = None
        self._setup_session()
    
    def _setup_session(self):
        """Set up requests session with retry strategy."""
        self.session = requests.Session()
        
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
    
    def connect(self) -> bool:
        """Authenticate with Salesforce and establish connection."""
        try:
            # OAuth 2.0 Username-Password Flow
            auth_url = "https://login.salesforce.com/services/oauth2/token"
            
            auth_data = {
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': self.username,
                'password': f"{self.password}{self.security_token}"
            }
            
            response = self.session.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            auth_result = response.json()
            self.access_token = auth_result['access_token']
            self.instance_url = auth_result['instance_url']
            
            # Set up headers for API calls
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            logger.info("Salesforce connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            return False
    
    def get_leads(
        self, 
        limit: int = 1000,
        where_clause: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get leads from Salesforce with optional filtering."""
        try:
            # Build SOQL query
            fields = [
                'Id', 'FirstName', 'LastName', 'Email', 'Phone', 'Company',
                'Title', 'LeadSource', 'Status', 'Rating', 'Industry',
                'AnnualRevenue', 'NumberOfEmployees', 'Website', 'City',
                'State', 'Country', 'PostalCode', 'CreatedDate', 
                'LastModifiedDate', 'LastActivityDate', 'IsConverted',
                'ConvertedAccountId', 'ConvertedContactId', 'ConvertedOpportunityId'
            ]
            
            query = f"SELECT {', '.join(fields)} FROM Lead"
            
            # Add WHERE conditions
            conditions = []
            if where_clause:
                conditions.append(where_clause)
            
            if modified_since:
                modified_str = modified_since.strftime('%Y-%m-%dT%H:%M:%SZ')
                conditions.append(f"LastModifiedDate >= {modified_str}")
            
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
            
            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"
            
            return self._execute_soql_query(query)
            
        except Exception as e:
            logger.error(f"Failed to get leads: {e}")
            return []
    
    def get_contacts(
        self, 
        limit: int = 1000,
        where_clause: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get contacts from Salesforce with optional filtering."""
        try:
            fields = [
                'Id', 'FirstName', 'LastName', 'Email', 'Phone', 'AccountId',
                'Title', 'Department', 'LeadSource', 'MailingCity', 'MailingState',
                'MailingCountry', 'MailingPostalCode', 'CreatedDate', 
                'LastModifiedDate', 'LastActivityDate', 'Account.Name',
                'Account.Industry', 'Account.AnnualRevenue', 'Account.NumberOfEmployees'
            ]
            
            query = f"SELECT {', '.join(fields)} FROM Contact"
            
            conditions = []
            if where_clause:
                conditions.append(where_clause)
            
            if modified_since:
                modified_str = modified_since.strftime('%Y-%m-%dT%H:%M:%SZ')
                conditions.append(f"LastModifiedDate >= {modified_str}")
            
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
            
            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"
            
            return self._execute_soql_query(query)
            
        except Exception as e:
            logger.error(f"Failed to get contacts: {e}")
            return []
    
    def get_opportunities(
        self, 
        limit: int = 1000,
        where_clause: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get opportunities from Salesforce with optional filtering."""
        try:
            fields = [
                'Id', 'Name', 'AccountId', 'Amount', 'CloseDate', 'StageName',
                'Probability', 'ForecastCategoryName', 'LeadSource', 'Type',
                'CreatedDate', 'LastModifiedDate', 'LastActivityDate',
                'Account.Name', 'Account.Industry', 'Owner.Name', 'Owner.Email'
            ]
            
            query = f"SELECT {', '.join(fields)} FROM Opportunity"
            
            conditions = []
            if where_clause:
                conditions.append(where_clause)
            
            if modified_since:
                modified_str = modified_since.strftime('%Y-%m-%dT%H:%M:%SZ')
                conditions.append(f"LastModifiedDate >= {modified_str}")
            
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
            
            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"
            
            return self._execute_soql_query(query)
            
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            return []
    
    def get_accounts(
        self, 
        limit: int = 1000,
        where_clause: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get accounts from Salesforce with optional filtering."""
        try:
            fields = [
                'Id', 'Name', 'Type', 'Industry', 'AnnualRevenue', 
                'NumberOfEmployees', 'Phone', 'Website', 'BillingCity',
                'BillingState', 'BillingCountry', 'BillingPostalCode',
                'CreatedDate', 'LastModifiedDate', 'LastActivityDate',
                'Owner.Name', 'Owner.Email'
            ]
            
            query = f"SELECT {', '.join(fields)} FROM Account"
            
            conditions = []
            if where_clause:
                conditions.append(where_clause)
            
            if modified_since:
                modified_str = modified_since.strftime('%Y-%m-%dT%H:%M:%SZ')
                conditions.append(f"LastModifiedDate >= {modified_str}")
            
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
            
            query += f" ORDER BY LastModifiedDate DESC LIMIT {limit}"
            
            return self._execute_soql_query(query)
            
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """Create a new lead in Salesforce."""
        try:
            url = f"{self.instance_url}/services/data/v{self.api_version}/sobjects/Lead/"
            
            response = self.session.post(url, json=lead_data)
            response.raise_for_status()
            
            result = response.json()
            lead_id = result.get('id')
            
            logger.info(f"Successfully created lead with ID: {lead_id}")
            return lead_id
            
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            return None
    
    def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing lead in Salesforce."""
        try:
            url = f"{self.instance_url}/services/data/v{self.api_version}/sobjects/Lead/{lead_id}"
            
            response = self.session.patch(url, json=update_data)
            response.raise_for_status()
            
            logger.info(f"Successfully updated lead: {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id}: {e}")
            return False
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Optional[str]:
        """Create a new contact in Salesforce."""
        try:
            url = f"{self.instance_url}/services/data/v{self.api_version}/sobjects/Contact/"
            
            response = self.session.post(url, json=contact_data)
            response.raise_for_status()
            
            result = response.json()
            contact_id = result.get('id')
            
            logger.info(f"Successfully created contact with ID: {contact_id}")
            return contact_id
            
        except Exception as e:
            logger.error(f"Failed to create contact: {e}")
            return None
    
    def update_contact(self, contact_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing contact in Salesforce."""
        try:
            url = f"{self.instance_url}/services/data/v{self.api_version}/sobjects/Contact/{contact_id}"
            
            response = self.session.patch(url, json=update_data)
            response.raise_for_status()
            
            logger.info(f"Successfully updated contact: {contact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update contact {contact_id}: {e}")
            return False
    
    def get_marketing_qualified_leads(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get marketing qualified leads for specified time period."""
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Customize this query based on your MQL criteria
            where_clause = """
                (Status = 'Marketing Qualified Lead' OR Status = 'MQL') 
                AND IsConverted = false
            """
            
            return self.get_leads(
                where_clause=where_clause,
                modified_since=since_date,
                limit=5000
            )
            
        except Exception as e:
            logger.error(f"Failed to get marketing qualified leads: {e}")
            return []
    
    def track_lead_attribution(self, lead_id: str) -> Dict[str, Any]:
        """Get attribution data for a specific lead."""
        try:
            # Get lead with campaign and source information
            query = f"""
                SELECT Id, FirstName, LastName, Email, Company, LeadSource,
                       CreatedDate, LastModifiedDate, 
                       utm_source__c, utm_medium__c, utm_campaign__c, utm_content__c,
                       Initial_Referring_Domain__c, Landing_Page__c,
                       Campaign.Name, Campaign.Type
                FROM Lead 
                WHERE Id = '{lead_id}'
            """
            
            results = self._execute_soql_query(query)
            
            if results:
                lead = results[0]
                
                # Get related campaign members if applicable
                campaign_query = f"""
                    SELECT Id, CampaignId, Campaign.Name, Campaign.Type,
                           FirstRespondedDate, Status
                    FROM CampaignMember 
                    WHERE LeadId = '{lead_id}'
                """
                
                campaigns = self._execute_soql_query(campaign_query)
                lead['campaigns'] = campaigns
                
                return lead
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get lead attribution for {lead_id}: {e}")
            return {}
    
    def _execute_soql_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SOQL query and return results."""
        try:
            url = f"{self.instance_url}/services/data/v{self.api_version}/query/"
            params = {'q': query}
            
            all_records = []
            
            while url:
                response = self.session.get(url, params=params if params else None)
                response.raise_for_status()
                
                data = response.json()
                
                if 'records' in data:
                    all_records.extend(data['records'])
                
                # Handle pagination
                url = data.get('nextRecordsUrl')
                if url:
                    url = self.instance_url + url
                    params = None  # Clear params for subsequent requests
            
            return all_records
            
        except Exception as e:
            logger.error(f"Failed to execute SOQL query: {e}")
            return []
    
    def bulk_upsert_leads(self, leads_data: List[Dict[str, Any]], external_id_field: str = 'Email') -> Dict[str, Any]:
        """Bulk upsert leads using Salesforce Bulk API."""
        try:
            # This is a simplified version - full Bulk API implementation would be more complex
            results = {'success': 0, 'errors': 0, 'details': []}
            
            for lead_data in leads_data:
                try:
                    # Check if lead exists by external ID
                    existing_lead = self._find_lead_by_field(external_id_field, lead_data.get(external_id_field))
                    
                    if existing_lead:
                        # Update existing lead
                        success = self.update_lead(existing_lead['Id'], lead_data)
                        if success:
                            results['success'] += 1
                            results['details'].append({'id': existing_lead['Id'], 'action': 'updated'})
                        else:
                            results['errors'] += 1
                            results['details'].append({'error': f"Failed to update lead {existing_lead['Id']}"})
                    else:
                        # Create new lead
                        lead_id = self.create_lead(lead_data)
                        if lead_id:
                            results['success'] += 1
                            results['details'].append({'id': lead_id, 'action': 'created'})
                        else:
                            results['errors'] += 1
                            results['details'].append({'error': "Failed to create lead"})
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({'error': str(e)})
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk upsert failed: {e}")
            return {'success': 0, 'errors': len(leads_data), 'error': str(e)}
    
    def _find_lead_by_field(self, field: str, value: str) -> Optional[Dict[str, Any]]:
        """Find a lead by specific field value."""
        try:
            query = f"SELECT Id, {field} FROM Lead WHERE {field} = '{value}' LIMIT 1"
            results = self._execute_soql_query(query)
            return results[0] if results else None
        except Exception:
            return None
    
    def sync(self) -> Dict[str, Any]:
        """Perform full data synchronization."""
        logger.info("Starting Salesforce data sync")
        
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
            
            # Sync leads
            leads = self.get_leads(modified_since=since_date, limit=5000)
            sync_results['data']['leads'] = leads
            sync_results['summary']['leads_count'] = len(leads)
            
            # Sync contacts
            contacts = self.get_contacts(modified_since=since_date, limit=5000)
            sync_results['data']['contacts'] = contacts
            sync_results['summary']['contacts_count'] = len(contacts)
            
            # Sync opportunities
            opportunities = self.get_opportunities(modified_since=since_date, limit=5000)
            sync_results['data']['opportunities'] = opportunities
            sync_results['summary']['opportunities_count'] = len(opportunities)
            
            # Sync accounts
            accounts = self.get_accounts(modified_since=since_date, limit=5000)
            sync_results['data']['accounts'] = accounts
            sync_results['summary']['accounts_count'] = len(accounts)
            
            # Get MQLs
            mqls = self.get_marketing_qualified_leads()
            sync_results['data']['marketing_qualified_leads'] = mqls
            sync_results['summary']['mqls_count'] = len(mqls)
            
            self.last_sync = sync_start
            sync_results['sync_duration'] = (datetime.now() - sync_start).total_seconds()
            
            logger.info(f"Salesforce sync completed successfully in {sync_results['sync_duration']:.2f} seconds")
            return sync_results
            
        except Exception as e:
            logger.error(f"Salesforce sync failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def disconnect(self):
        """Clean up connection resources."""
        if self.session:
            self.session.close()
        
        self.access_token = None
        self.instance_url = None
        logger.info("Salesforce connector disconnected")
    
    def get_custom_objects(self, object_name: str, fields: List[str], limit: int = 1000) -> List[Dict[str, Any]]:
        """Get data from custom Salesforce objects."""
        try:
            query = f"SELECT {', '.join(fields)} FROM {object_name} ORDER BY LastModifiedDate DESC LIMIT {limit}"
            return self._execute_soql_query(query)
        except Exception as e:
            logger.error(f"Failed to get custom object {object_name}: {e}")
            return []