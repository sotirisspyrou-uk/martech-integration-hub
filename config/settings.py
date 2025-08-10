import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="postgresql://user:password@localhost/martech_hub")
    redis_url: str = Field(default="redis://localhost:6379")
    
    # Application
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    secret_key: str = Field(default="martech-hub-secret-key-change-in-production")
    api_rate_limit: int = Field(default=1000)
    sync_interval: int = Field(default=300)
    
    # Google Analytics
    google_analytics_credentials_path: Optional[str] = Field(default=None)
    
    # Salesforce
    salesforce_client_id: Optional[str] = Field(default=None)
    salesforce_client_secret: Optional[str] = Field(default=None)
    salesforce_username: Optional[str] = Field(default=None)
    salesforce_password: Optional[str] = Field(default=None)
    salesforce_security_token: Optional[str] = Field(default=None)
    
    # HubSpot
    hubspot_api_key: Optional[str] = Field(default=None)
    
    # Facebook
    facebook_app_id: Optional[str] = Field(default=None)
    facebook_app_secret: Optional[str] = Field(default=None)
    facebook_access_token: Optional[str] = Field(default=None)
    
    # Google Ads
    google_ads_client_id: Optional[str] = Field(default=None)
    google_ads_client_secret: Optional[str] = Field(default=None)
    google_ads_refresh_token: Optional[str] = Field(default=None)
    google_ads_developer_token: Optional[str] = Field(default=None)
    
    # Twitter
    twitter_api_key: Optional[str] = Field(default=None)
    twitter_api_secret: Optional[str] = Field(default=None)
    twitter_access_token: Optional[str] = Field(default=None)
    twitter_access_token_secret: Optional[str] = Field(default=None)
    
    # LinkedIn
    linkedin_client_id: Optional[str] = Field(default=None)
    linkedin_client_secret: Optional[str] = Field(default=None)
    
    # Mailchimp
    mailchimp_api_key: Optional[str] = Field(default=None)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()