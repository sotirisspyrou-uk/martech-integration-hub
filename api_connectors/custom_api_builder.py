"""
Custom API Builder for MarTech Integration Hub

Dynamic API connector generation system that creates standardized integrations
for any marketing platform with REST API capabilities.

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
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, Type
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import aiohttp
from abc import ABC, abstractmethod
import yaml
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, parse_qs
import base64
import hmac
import jwt
from pathlib import Path

logger = logging.getLogger(__name__)


class AuthType(Enum):
    """Supported authentication types."""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    CUSTOM_HEADER = "custom_header"
    HMAC_SIGNATURE = "hmac_signature"
    JWT = "jwt"
    NO_AUTH = "no_auth"


class HTTPMethod(Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class DataFormat(Enum):
    """Supported data formats."""
    JSON = "json"
    XML = "xml"
    FORM_DATA = "form_data"
    URL_ENCODED = "url_encoded"
    CSV = "csv"
    TEXT = "text"


@dataclass
class APIEndpoint:
    """API endpoint configuration."""
    name: str
    path: str
    method: HTTPMethod
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    response_format: DataFormat = DataFormat.JSON
    rate_limit: Optional[Dict[str, int]] = None
    cache_ttl: int = 300
    timeout: int = 30


@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: AuthType
    credentials: Dict[str, str]
    token_url: Optional[str] = None
    refresh_url: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    token_expiry: Optional[datetime] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class APISpec:
    """Complete API specification."""
    platform_name: str
    base_url: str
    version: str
    auth_config: AuthConfig
    endpoints: List[APIEndpoint]
    global_headers: Dict[str, str] = field(default_factory=dict)
    rate_limit_global: Optional[Dict[str, int]] = None
    retry_config: Dict[str, int] = field(default_factory=lambda: {
        'max_retries': 3,
        'backoff_factor': 2,
        'retry_status_codes': [429, 500, 502, 503, 504]
    })
    timeout_default: int = 30
    ssl_verify: bool = True


class BaseAPIConnector(ABC):
    """Abstract base class for API connectors."""
    
    def __init__(self, api_spec: APISpec):
        self.api_spec = api_spec
        self.session = requests.Session()
        self._setup_session()
        self._token_cache = {}
        self._rate_limiter = {}
    
    def _setup_session(self):
        """Setup HTTP session with default headers."""
        self.session.headers.update(self.api_spec.global_headers)
        if not self.api_spec.ssl_verify:
            self.session.verify = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the API."""
        pass
    
    @abstractmethod
    def make_request(self, endpoint: APIEndpoint, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        pass


class CustomAPIConnector(BaseAPIConnector):
    """
    Dynamic API connector that can connect to any REST API based on specification.
    
    Features:
    - Multiple authentication methods
    - Rate limiting and retry logic  
    - Response caching
    - Data transformation
    - Error handling and logging
    """
    
    def __init__(self, api_spec: APISpec):
        super().__init__(api_spec)
        self.cache = {}
        self.last_request_times = {}
        
        # Setup authentication
        self.authenticate()
        
        logger.info(f"Initialized connector for {api_spec.platform_name}")
    
    def authenticate(self) -> bool:
        """Authenticate with the API based on auth configuration."""
        try:
            auth_config = self.api_spec.auth_config
            
            if auth_config.auth_type == AuthType.API_KEY:
                return self._setup_api_key_auth(auth_config)
            elif auth_config.auth_type == AuthType.BEARER_TOKEN:
                return self._setup_bearer_token_auth(auth_config)
            elif auth_config.auth_type == AuthType.OAUTH2:
                return self._setup_oauth2_auth(auth_config)
            elif auth_config.auth_type == AuthType.BASIC_AUTH:
                return self._setup_basic_auth(auth_config)
            elif auth_config.auth_type == AuthType.CUSTOM_HEADER:
                return self._setup_custom_header_auth(auth_config)
            elif auth_config.auth_type == AuthType.HMAC_SIGNATURE:
                return self._setup_hmac_auth(auth_config)
            elif auth_config.auth_type == AuthType.JWT:
                return self._setup_jwt_auth(auth_config)
            elif auth_config.auth_type == AuthType.NO_AUTH:
                return True
            
            logger.error(f"Unsupported auth type: {auth_config.auth_type}")
            return False
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _setup_api_key_auth(self, auth_config: AuthConfig) -> bool:
        """Setup API key authentication."""
        api_key = auth_config.credentials.get('api_key')
        key_param = auth_config.credentials.get('key_param', 'api_key')
        location = auth_config.credentials.get('location', 'header')
        
        if not api_key:
            raise ValueError("API key not provided")
        
        if location == 'header':
            header_name = auth_config.credentials.get('header_name', 'X-API-Key')
            self.session.headers[header_name] = api_key
        elif location == 'query':
            # Will be added to each request
            self._api_key_param = {key_param: api_key}
        
        return True
    
    def _setup_bearer_token_auth(self, auth_config: AuthConfig) -> bool:
        """Setup Bearer token authentication."""
        token = auth_config.credentials.get('token')
        if not token:
            raise ValueError("Bearer token not provided")
        
        self.session.headers['Authorization'] = f'Bearer {token}'
        return True
    
    def _setup_oauth2_auth(self, auth_config: AuthConfig) -> bool:
        """Setup OAuth 2.0 authentication."""
        client_id = auth_config.credentials.get('client_id')
        client_secret = auth_config.credentials.get('client_secret')
        
        if not client_id or not client_secret:
            raise ValueError("OAuth2 credentials incomplete")
        
        # Check for existing token
        if auth_config.token_expiry and auth_config.token_expiry > datetime.now():
            token = auth_config.credentials.get('access_token')
            if token:
                self.session.headers['Authorization'] = f'Bearer {token}'
                return True
        
        # Get new token
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        if auth_config.scopes:
            token_data['scope'] = ' '.join(auth_config.scopes)
        
        response = requests.post(
            auth_config.token_url,
            data=token_data,
            timeout=self.api_spec.timeout_default
        )
        response.raise_for_status()
        
        token_response = response.json()
        access_token = token_response['access_token']
        expires_in = token_response.get('expires_in', 3600)
        
        # Update auth config
        auth_config.credentials['access_token'] = access_token
        auth_config.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
        
        self.session.headers['Authorization'] = f'Bearer {access_token}'
        return True
    
    def _setup_basic_auth(self, auth_config: AuthConfig) -> bool:
        """Setup HTTP Basic authentication."""
        username = auth_config.credentials.get('username')
        password = auth_config.credentials.get('password')
        
        if not username or not password:
            raise ValueError("Basic auth credentials incomplete")
        
        auth_string = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers['Authorization'] = f'Basic {encoded_auth}'
        return True
    
    def _setup_custom_header_auth(self, auth_config: AuthConfig) -> bool:
        """Setup custom header authentication."""
        for header_name, header_value in auth_config.custom_headers.items():
            self.session.headers[header_name] = header_value
        return True
    
    def _setup_hmac_auth(self, auth_config: AuthConfig) -> bool:
        """Setup HMAC signature authentication."""
        self._hmac_secret = auth_config.credentials.get('secret_key')
        self._hmac_key_id = auth_config.credentials.get('key_id')
        
        if not self._hmac_secret:
            raise ValueError("HMAC secret key not provided")
        
        return True
    
    def _setup_jwt_auth(self, auth_config: AuthConfig) -> bool:
        """Setup JWT authentication."""
        private_key = auth_config.credentials.get('private_key')
        algorithm = auth_config.credentials.get('algorithm', 'HS256')
        
        if not private_key:
            raise ValueError("JWT private key not provided")
        
        payload = {
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        # Add custom claims
        for key, value in auth_config.credentials.items():
            if key not in ['private_key', 'algorithm']:
                payload[key] = value
        
        token = jwt.encode(payload, private_key, algorithm=algorithm)
        self.session.headers['Authorization'] = f'Bearer {token}'
        return True
    
    def _generate_hmac_signature(self, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for request."""
        timestamp = str(int(time.time()))
        message = f"{method.upper()}{path}{body}{timestamp}"
        
        signature = hmac.new(
            self._hmac_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{self._hmac_key_id}:{timestamp}:{signature}"
    
    def _check_rate_limit(self, endpoint: APIEndpoint) -> bool:
        """Check if request is within rate limits."""
        now = time.time()
        endpoint_name = endpoint.name
        
        # Check endpoint-specific rate limit
        if endpoint.rate_limit:
            limit = endpoint.rate_limit.get('requests_per_minute', 60)
            window = 60  # 1 minute
            
            if endpoint_name not in self._rate_limiter:
                self._rate_limiter[endpoint_name] = []
            
            # Clean old requests
            cutoff_time = now - window
            self._rate_limiter[endpoint_name] = [
                req_time for req_time in self._rate_limiter[endpoint_name]
                if req_time > cutoff_time
            ]
            
            if len(self._rate_limiter[endpoint_name]) >= limit:
                sleep_time = window - (now - self._rate_limiter[endpoint_name][0])
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached for {endpoint_name}, sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
            
            self._rate_limiter[endpoint_name].append(now)
        
        return True
    
    def _get_cache_key(self, endpoint: APIEndpoint, params: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        key_data = {
            'endpoint': endpoint.name,
            'params': sorted(params.items())
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _is_cached_response_valid(self, cache_entry: Dict[str, Any], ttl: int) -> bool:
        """Check if cached response is still valid."""
        cached_at = datetime.fromisoformat(cache_entry['cached_at'])
        return datetime.now() - cached_at < timedelta(seconds=ttl)
    
    def make_request(self, endpoint: APIEndpoint, **kwargs) -> Dict[str, Any]:
        """Make API request with full error handling and retry logic."""
        
        # Check rate limits
        self._check_rate_limit(endpoint)
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, kwargs)
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cached_response_valid(cache_entry, endpoint.cache_ttl):
                logger.debug(f"Returning cached response for {endpoint.name}")
                return cache_entry['data']
        
        # Prepare request
        url = urljoin(self.api_spec.base_url, endpoint.path)
        
        # Handle path parameters
        if 'path_params' in kwargs:
            for param, value in kwargs['path_params'].items():
                url = url.replace(f'{{{param}}}', str(value))
        
        # Prepare request parameters
        request_params = {}
        request_data = None
        request_json = None
        
        # Add API key to query if needed
        if hasattr(self, '_api_key_param'):
            request_params.update(self._api_key_param)
        
        # Handle query parameters
        if 'params' in kwargs:
            request_params.update(kwargs['params'])
        
        # Handle request body
        if 'data' in kwargs:
            if endpoint.response_format == DataFormat.JSON:
                request_json = kwargs['data']
            else:
                request_data = kwargs['data']
        
        # Add HMAC signature if needed
        if hasattr(self, '_hmac_secret'):
            body_str = json.dumps(request_json) if request_json else ""
            signature = self._generate_hmac_signature(endpoint.method.value, endpoint.path, body_str)
            self.session.headers['X-Signature'] = signature
        
        # Make request with retry logic
        max_retries = self.api_spec.retry_config['max_retries']
        backoff_factor = self.api_spec.retry_config['backoff_factor']
        retry_codes = self.api_spec.retry_config['retry_status_codes']
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(
                    method=endpoint.method.value,
                    url=url,
                    params=request_params,
                    json=request_json,
                    data=request_data,
                    timeout=endpoint.timeout,
                    **kwargs.get('requests_kwargs', {})
                )
                
                # Check if retry needed
                if response.status_code in retry_codes and attempt < max_retries:
                    sleep_time = backoff_factor ** attempt
                    logger.warning(f"Request failed with {response.status_code}, retrying in {sleep_time}s")
                    time.sleep(sleep_time)
                    continue
                
                response.raise_for_status()
                
                # Parse response
                response_data = self._parse_response(response, endpoint.response_format)
                
                # Cache successful response
                self.cache[cache_key] = {
                    'data': response_data,
                    'cached_at': datetime.now().isoformat()
                }
                
                logger.info(f"Successfully called {endpoint.name}")
                return response_data
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    logger.error(f"Request failed after {max_retries + 1} attempts: {e}")
                    raise
                else:
                    sleep_time = backoff_factor ** attempt
                    logger.warning(f"Request attempt {attempt + 1} failed: {e}, retrying in {sleep_time}s")
                    time.sleep(sleep_time)
    
    def _parse_response(self, response: requests.Response, format_type: DataFormat) -> Any:
        """Parse API response based on format type."""
        try:
            if format_type == DataFormat.JSON:
                return response.json()
            elif format_type == DataFormat.XML:
                return self._xml_to_dict(ET.fromstring(response.text))
            elif format_type == DataFormat.CSV:
                return self._parse_csv_response(response.text)
            elif format_type == DataFormat.TEXT:
                return {'text': response.text}
            else:
                return {'raw': response.text}
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return {'raw': response.text, 'parse_error': str(e)}
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        if element.text and element.text.strip():
            result['text'] = element.text.strip()
        
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        if element.attrib:
            result['@attributes'] = element.attrib
        
        return result
    
    def _parse_csv_response(self, csv_text: str) -> Dict[str, Any]:
        """Parse CSV response into structured data."""
        lines = csv_text.strip().split('\n')
        if not lines:
            return {'data': []}
        
        headers = lines[0].split(',')
        data = []
        
        for line in lines[1:]:
            values = line.split(',')
            row = {headers[i]: values[i] if i < len(values) else '' for i in range(len(headers))}
            data.append(row)
        
        return {'headers': headers, 'data': data}
    
    def get_endpoint(self, name: str) -> Optional[APIEndpoint]:
        """Get endpoint configuration by name."""
        for endpoint in self.api_spec.endpoints:
            if endpoint.name == name:
                return endpoint
        return None
    
    def call_endpoint(self, endpoint_name: str, **kwargs) -> Dict[str, Any]:
        """Call endpoint by name."""
        endpoint = self.get_endpoint(endpoint_name)
        if not endpoint:
            raise ValueError(f"Endpoint '{endpoint_name}' not found")
        
        return self.make_request(endpoint, **kwargs)


class CustomAPIBuilder:
    """
    Builder class for creating custom API connectors from specifications.
    
    Features:
    - YAML/JSON configuration support
    - OpenAPI spec import
    - Interactive connector generation
    - Pre-built templates for common platforms
    """
    
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load pre-built API templates."""
        self.templates = {
            'rest_api_basic': {
                'auth_type': AuthType.API_KEY,
                'data_format': DataFormat.JSON,
                'common_endpoints': ['list', 'get', 'create', 'update', 'delete']
            },
            'oauth2_api': {
                'auth_type': AuthType.OAUTH2,
                'data_format': DataFormat.JSON,
                'common_endpoints': ['profile', 'data', 'metrics']
            },
            'webhook_receiver': {
                'auth_type': AuthType.HMAC_SIGNATURE,
                'data_format': DataFormat.JSON,
                'common_endpoints': ['webhook']
            }
        }
    
    def create_from_config(self, config_data: Dict[str, Any]) -> CustomAPIConnector:
        """Create API connector from configuration dictionary."""
        api_spec = self._build_api_spec_from_config(config_data)
        return CustomAPIConnector(api_spec)
    
    def create_from_yaml(self, yaml_file_path: str) -> CustomAPIConnector:
        """Create API connector from YAML configuration file."""
        with open(yaml_file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return self.create_from_config(config_data)
    
    def create_from_json(self, json_file_path: str) -> CustomAPIConnector:
        """Create API connector from JSON configuration file."""
        with open(json_file_path, 'r') as file:
            config_data = json.load(file)
        return self.create_from_config(config_data)
    
    def create_from_openapi(self, openapi_spec: Dict[str, Any]) -> CustomAPIConnector:
        """Create API connector from OpenAPI specification."""
        config_data = self._convert_openapi_to_config(openapi_spec)
        return self.create_from_config(config_data)
    
    def _build_api_spec_from_config(self, config: Dict[str, Any]) -> APISpec:
        """Build APISpec object from configuration dictionary."""
        
        # Parse authentication
        auth_data = config.get('authentication', {})
        auth_config = AuthConfig(
            auth_type=AuthType(auth_data.get('type', 'api_key')),
            credentials=auth_data.get('credentials', {}),
            token_url=auth_data.get('token_url'),
            refresh_url=auth_data.get('refresh_url'),
            scopes=auth_data.get('scopes', []),
            custom_headers=auth_data.get('custom_headers', {})
        )
        
        # Parse endpoints
        endpoints = []
        for endpoint_data in config.get('endpoints', []):
            endpoint = APIEndpoint(
                name=endpoint_data['name'],
                path=endpoint_data['path'],
                method=HTTPMethod(endpoint_data.get('method', 'GET')),
                description=endpoint_data.get('description', ''),
                parameters=endpoint_data.get('parameters', {}),
                required_params=endpoint_data.get('required_params', []),
                response_format=DataFormat(endpoint_data.get('response_format', 'json')),
                rate_limit=endpoint_data.get('rate_limit'),
                cache_ttl=endpoint_data.get('cache_ttl', 300),
                timeout=endpoint_data.get('timeout', 30)
            )
            endpoints.append(endpoint)
        
        # Build API spec
        return APISpec(
            platform_name=config['platform_name'],
            base_url=config['base_url'],
            version=config.get('version', '1.0'),
            auth_config=auth_config,
            endpoints=endpoints,
            global_headers=config.get('global_headers', {}),
            rate_limit_global=config.get('rate_limit_global'),
            retry_config=config.get('retry_config', {
                'max_retries': 3,
                'backoff_factor': 2,
                'retry_status_codes': [429, 500, 502, 503, 504]
            }),
            timeout_default=config.get('timeout_default', 30),
            ssl_verify=config.get('ssl_verify', True)
        )
    
    def _convert_openapi_to_config(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI specification to internal configuration format."""
        info = openapi_spec.get('info', {})
        servers = openapi_spec.get('servers', [])
        paths = openapi_spec.get('paths', {})
        
        base_url = servers[0]['url'] if servers else 'https://api.example.com'
        
        # Basic conversion - would need more sophisticated logic for full OpenAPI support
        config = {
            'platform_name': info.get('title', 'Custom API'),
            'base_url': base_url,
            'version': info.get('version', '1.0'),
            'authentication': {
                'type': 'api_key',  # Default, would parse from securitySchemes
                'credentials': {}
            },
            'endpoints': []
        }
        
        # Convert paths to endpoints
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() in [m.value for m in HTTPMethod]:
                    endpoint = {
                        'name': operation.get('operationId', f"{method}_{path.replace('/', '_')}"),
                        'path': path,
                        'method': method.upper(),
                        'description': operation.get('summary', ''),
                        'parameters': {},
                        'required_params': []
                    }
                    config['endpoints'].append(endpoint)
        
        return config
    
    def generate_config_template(self, platform_name: str, template_type: str = 'rest_api_basic') -> Dict[str, Any]:
        """Generate configuration template for a platform."""
        template = self.templates.get(template_type, self.templates['rest_api_basic'])
        
        config = {
            'platform_name': platform_name,
            'base_url': f'https://api.{platform_name.lower().replace(" ", "")}.com',
            'version': '1.0',
            'authentication': {
                'type': template['auth_type'].value,
                'credentials': {
                    'api_key': 'your_api_key_here'
                }
            },
            'global_headers': {
                'User-Agent': f'MarTech-Integration-Hub/{platform_name}',
                'Accept': 'application/json'
            },
            'endpoints': []
        }
        
        # Add common endpoints
        for endpoint_name in template['common_endpoints']:
            endpoint = {
                'name': endpoint_name,
                'path': f'/{endpoint_name}',
                'method': 'GET' if endpoint_name in ['list', 'get'] else 'POST',
                'description': f'{endpoint_name.title()} operation',
                'response_format': template['data_format'].value
            }
            config['endpoints'].append(endpoint)
        
        return config
    
    def save_config_template(self, config: Dict[str, Any], file_path: str):
        """Save configuration template to file."""
        path = Path(file_path)
        
        if path.suffix.lower() == '.yaml' or path.suffix.lower() == '.yml':
            with open(file_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, indent=2)
        else:
            with open(file_path, 'w') as file:
                json.dump(config, file, indent=2)
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        required_fields = ['platform_name', 'base_url', 'authentication', 'endpoints']
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")
        
        if 'authentication' in config:
            auth = config['authentication']
            if 'type' not in auth:
                issues.append("Authentication type not specified")
            elif auth['type'] not in [t.value for t in AuthType]:
                issues.append(f"Invalid authentication type: {auth['type']}")
        
        if 'endpoints' in config:
            for i, endpoint in enumerate(config['endpoints']):
                if 'name' not in endpoint:
                    issues.append(f"Endpoint {i}: Missing name")
                if 'path' not in endpoint:
                    issues.append(f"Endpoint {i}: Missing path")
        
        return issues


def create_sample_connector() -> CustomAPIConnector:
    """Create a sample API connector for demonstration."""
    
    config = {
        'platform_name': 'Sample Marketing API',
        'base_url': 'https://api.samplemarketing.com/v1',
        'version': '1.0',
        'authentication': {
            'type': 'api_key',
            'credentials': {
                'api_key': 'demo_api_key_12345',
                'location': 'header',
                'header_name': 'X-API-Key'
            }
        },
        'global_headers': {
            'User-Agent': 'MarTech-Integration-Hub/1.0',
            'Accept': 'application/json'
        },
        'endpoints': [
            {
                'name': 'get_campaigns',
                'path': '/campaigns',
                'method': 'GET',
                'description': 'Retrieve all marketing campaigns',
                'parameters': {
                    'status': 'string',
                    'limit': 'integer',
                    'offset': 'integer'
                },
                'response_format': 'json',
                'cache_ttl': 600
            },
            {
                'name': 'get_campaign',
                'path': '/campaigns/{campaign_id}',
                'method': 'GET',
                'description': 'Retrieve specific campaign',
                'parameters': {
                    'campaign_id': 'string'
                },
                'required_params': ['campaign_id'],
                'response_format': 'json'
            },
            {
                'name': 'create_campaign',
                'path': '/campaigns',
                'method': 'POST',
                'description': 'Create new campaign',
                'parameters': {
                    'name': 'string',
                    'budget': 'number',
                    'target_audience': 'object'
                },
                'required_params': ['name', 'budget'],
                'response_format': 'json'
            },
            {
                'name': 'get_analytics',
                'path': '/analytics/campaigns/{campaign_id}',
                'method': 'GET',
                'description': 'Get campaign analytics data',
                'parameters': {
                    'campaign_id': 'string',
                    'date_from': 'string',
                    'date_to': 'string',
                    'metrics': 'array'
                },
                'required_params': ['campaign_id'],
                'response_format': 'json',
                'rate_limit': {
                    'requests_per_minute': 30
                }
            }
        ],
        'retry_config': {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_status_codes': [429, 500, 502, 503, 504]
        }
    }
    
    builder = CustomAPIBuilder()
    return builder.create_from_config(config)


def run_custom_api_builder_demo():
    """
    Run the custom API builder demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🔧 Custom API Builder Demo")
    print("=" * 50)
    
    # Create builder instance
    print("🏗️  Initializing API builder...")
    builder = CustomAPIBuilder()
    
    # Generate template configuration
    print("📝 Generating configuration template...")
    template_config = builder.generate_config_template("Demo Marketing Platform", "oauth2_api")
    
    # Validate configuration
    print("✅ Validating configuration...")
    issues = builder.validate_config(template_config)
    if issues:
        print(f"⚠️  Configuration issues found: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration is valid")
    
    # Create sample connector
    print("🔌 Creating sample API connector...")
    connector = create_sample_connector()
    
    print(f"🎯 Successfully created connector for: {connector.api_spec.platform_name}")
    print(f"🌐 Base URL: {connector.api_spec.base_url}")
    print(f"🔐 Auth Type: {connector.api_spec.auth_config.auth_type.value}")
    print(f"📊 Available Endpoints: {len(connector.api_spec.endpoints)}")
    
    # Demonstrate endpoint calls (would work with real API)
    print("\n📋 Available Endpoints:")
    for endpoint in connector.api_spec.endpoints:
        print(f"  • {endpoint.name}: {endpoint.method.value} {endpoint.path}")
        print(f"    Description: {endpoint.description}")
    
    # Example configuration export
    print("\n💾 Exporting configuration template...")
    export_config = {
        'platform_name': 'Custom Marketing Platform',
        'base_url': 'https://api.custommarketing.com/v2',
        'authentication': {
            'type': 'bearer_token',
            'credentials': {
                'token': 'your_bearer_token_here'
            }
        },
        'endpoints': [
            {
                'name': 'get_metrics',
                'path': '/metrics',
                'method': 'GET',
                'description': 'Get marketing metrics',
                'response_format': 'json'
            }
        ]
    }
    
    # Save to file (demonstration)
    try:
        builder.save_config_template(export_config, '/tmp/custom_api_config.json')
        print("✅ Configuration saved to /tmp/custom_api_config.json")
    except Exception as e:
        print(f"ℹ️  Configuration export demo completed (file not saved: {e})")
    
    print("\n🌟 Key Features Demonstrated:")
    print("  • Dynamic API connector generation")
    print("  • Multiple authentication methods support")
    print("  • Rate limiting and retry logic")
    print("  • Configuration validation")
    print("  • Template-based connector creation")
    print("  • Response caching and error handling")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return connector


if __name__ == "__main__":
    run_custom_api_builder_demo()
