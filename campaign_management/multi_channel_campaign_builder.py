"""
Multi-Channel Campaign Builder for MarTech Integration Hub

Comprehensive campaign creation and orchestration system for coordinated
multi-channel marketing campaigns with intelligent automation and optimization.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import threading
import queue
import time
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import redis
from jinja2 import Template
import requests
from urllib.parse import urljoin
import copy

logger = logging.getLogger(__name__)


class CampaignType(Enum):
    """Campaign types."""
    BRAND_AWARENESS = "brand_awareness"
    LEAD_GENERATION = "lead_generation"
    CUSTOMER_ACQUISITION = "customer_acquisition"
    CUSTOMER_RETENTION = "customer_retention"
    PRODUCT_LAUNCH = "product_launch"
    SEASONAL_PROMOTION = "seasonal_promotion"
    EVENT_PROMOTION = "event_promotion"
    REMARKETING = "remarketing"
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"


class CampaignStatus(Enum):
    """Campaign execution status."""
    DRAFT = "draft"
    PLANNING = "planning"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    LAUNCHING = "launching"
    ACTIVE = "active"
    PAUSED = "paused"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignChannel(Enum):
    """Marketing channels."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    SEARCH_ADS = "search_ads"
    DISPLAY_ADS = "display_ads"
    VIDEO_ADS = "video_ads"
    NATIVE_ADS = "native_ads"
    CONTENT_MARKETING = "content_marketing"
    INFLUENCER = "influencer"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    DIRECT_MAIL = "direct_mail"
    WEBINAR = "webinar"
    PODCAST = "podcast"
    AFFILIATE = "affiliate"
    PR = "pr"
    OUT_OF_HOME = "out_of_home"


class CampaignObjective(Enum):
    """Campaign objectives."""
    TRAFFIC = "traffic"
    CONVERSIONS = "conversions"
    AWARENESS = "awareness"
    ENGAGEMENT = "engagement"
    APP_INSTALLS = "app_installs"
    VIDEO_VIEWS = "video_views"
    LEAD_GENERATION = "lead_generation"
    CATALOG_SALES = "catalog_sales"
    STORE_VISITS = "store_visits"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    BRAND_CONSIDERATION = "brand_consideration"


class TriggerType(Enum):
    """Campaign trigger types."""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"
    ENGAGEMENT = "engagement"
    LIFECYCLE = "lifecycle"
    CUSTOM_EVENT = "custom_event"
    WEATHER = "weather"
    INVENTORY = "inventory"
    COMPETITOR = "competitor"


class OptimizationStrategy(Enum):
    """Campaign optimization strategies."""
    MANUAL = "manual"
    AUTO_BID = "auto_bid"
    AUTO_BUDGET = "auto_budget"
    AUTO_AUDIENCE = "auto_audience"
    AUTO_CREATIVE = "auto_creative"
    AUTO_PLACEMENT = "auto_placement"
    MACHINE_LEARNING = "machine_learning"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


@dataclass
class CampaignBudget:
    """Campaign budget configuration."""
    total_budget: float
    daily_budget: Optional[float] = None
    channel_allocation: Dict[CampaignChannel, float] = field(default_factory=dict)
    currency: str = "USD"
    budget_type: str = "lifetime"  # lifetime, daily, weekly, monthly
    auto_allocation: bool = False
    min_channel_budget: float = 100.0
    max_channel_budget: Optional[float] = None
    pacing_strategy: str = "even"  # even, accelerated, front_loaded, back_loaded


@dataclass
class CampaignTiming:
    """Campaign timing configuration."""
    start_date: datetime
    end_date: Optional[datetime] = None
    timezone: str = "UTC"
    dayparting: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)  # day: [(start_hour, end_hour)]
    frequency_cap: Optional[Dict[str, int]] = None  # {"daily": 3, "weekly": 10}
    launch_sequence: List[Dict[str, Any]] = field(default_factory=list)
    optimization_schedule: Optional[Dict[str, Any]] = None


@dataclass
class CampaignAudience:
    """Campaign audience configuration."""
    primary_segments: List[str]
    lookalike_segments: List[str] = field(default_factory=list)
    exclusion_segments: List[str] = field(default_factory=list)
    demographic_filters: Dict[str, Any] = field(default_factory=dict)
    behavioral_filters: Dict[str, Any] = field(default_factory=dict)
    geographic_filters: Dict[str, Any] = field(default_factory=dict)
    custom_audiences: List[str] = field(default_factory=list)
    audience_size_estimate: Optional[int] = None
    audience_overlap_analysis: Dict[str, float] = field(default_factory=dict)


@dataclass
class CampaignCreative:
    """Campaign creative assets configuration."""
    primary_assets: List[str]  # Asset IDs
    variant_assets: List[str] = field(default_factory=list)
    dynamic_creative: bool = False
    personalization_rules: List[Dict[str, Any]] = field(default_factory=list)
    ab_test_config: Optional[Dict[str, Any]] = None
    creative_rotation: str = "optimize"  # optimize, rotate_evenly
    asset_performance_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChannelConfiguration:
    """Configuration for a specific channel in the campaign."""
    channel: CampaignChannel
    is_enabled: bool = True
    budget_allocation: float = 0.0
    targeting: Dict[str, Any] = field(default_factory=dict)
    creative_assets: List[str] = field(default_factory=list)
    placement_preferences: List[str] = field(default_factory=list)
    bid_strategy: str = "auto"
    optimization_goal: Optional[CampaignObjective] = None
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    launch_delay_hours: int = 0
    performance_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class CampaignTrigger:
    """Campaign launch trigger configuration."""
    trigger_id: str
    trigger_type: TriggerType
    conditions: Dict[str, Any]
    channels: List[CampaignChannel] = field(default_factory=list)  # Empty means all channels
    is_active: bool = True
    priority: int = 0
    cooldown_period: timedelta = field(default_factory=lambda: timedelta(hours=1))
    max_triggers_per_day: Optional[int] = None
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None


@dataclass
class CampaignGoal:
    """Campaign performance goal."""
    goal_id: str
    name: str
    metric: str
    target_value: float
    target_type: str = "minimum"  # minimum, maximum, exact
    priority: str = "medium"  # high, medium, low
    deadline: Optional[datetime] = None
    current_value: float = 0.0
    progress_percentage: float = 0.0
    is_achieved: bool = False
    achieved_at: Optional[datetime] = None


@dataclass
class Campaign:
    """Comprehensive campaign definition."""
    campaign_id: str
    name: str
    description: str
    campaign_type: CampaignType
    status: CampaignStatus
    objectives: List[CampaignObjective]
    budget: CampaignBudget
    timing: CampaignTiming
    audience: CampaignAudience
    creative: CampaignCreative
    channels: List[ChannelConfiguration]
    triggers: List[CampaignTrigger] = field(default_factory=list)
    goals: List[CampaignGoal] = field(default_factory=list)
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.AUTO_BID
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    launched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CampaignTemplate:
    """Reusable campaign template."""
    template_id: str
    name: str
    description: str
    campaign_type: CampaignType
    template_data: Dict[str, Any]  # JSON template structure
    default_channels: List[CampaignChannel]
    required_fields: List[str]
    optional_fields: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: float = 0.0
    is_active: bool = True


class MultiChannelCampaignBuilder:
    """
    Comprehensive multi-channel campaign creation and management system.
    
    Features:
    - Unified campaign creation across multiple channels
    - Intelligent budget allocation and optimization
    - Automated audience segmentation and targeting
    - Dynamic creative asset assignment
    - Cross-channel performance tracking
    - Real-time campaign optimization
    - Template-based campaign generation
    - Trigger-based campaign automation
    """
    
    def __init__(self,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 api_credentials: Optional[Dict[str, Dict[str, str]]] = None):
        
        # Redis connection for campaign data
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.redis_available = False
            logger.warning("Redis not available, using in-memory storage")
        
        # API credentials for different platforms
        self.api_credentials = api_credentials or {}
        
        # In-memory storage
        self.campaigns: Dict[str, Campaign] = {}
        self.templates: Dict[str, CampaignTemplate] = {}
        self.active_triggers: Dict[str, CampaignTrigger] = {}
        
        # Campaign processing queues
        self.launch_queue = queue.Queue()
        self.optimization_queue = queue.Queue()
        self.trigger_queue = queue.Queue()
        
        # Background processing
        self.is_processing = True
        self.processing_threads = []
        
        # ML models for optimization
        self.budget_optimizer = None
        self.audience_predictor = None
        self.performance_predictor = None
        
        # Performance tracking
        self.channel_performance_history = defaultdict(list)
        self.optimization_results = defaultdict(list)
        
        # Start background processing
        self._start_background_processing()
        
        # Create default templates
        self._create_default_templates()
        
        logger.info("Multi-Channel Campaign Builder initialized successfully")
    
    def _start_background_processing(self):
        """Start background processing threads."""
        try:
            # Campaign launch processing
            launch_thread = threading.Thread(target=self._process_launch_queue, daemon=True)
            launch_thread.start()
            self.processing_threads.append(launch_thread)
            
            # Campaign optimization processing
            optimization_thread = threading.Thread(target=self._process_optimization_queue, daemon=True)
            optimization_thread.start()
            self.processing_threads.append(optimization_thread)
            
            # Trigger monitoring
            trigger_thread = threading.Thread(target=self._process_trigger_queue, daemon=True)
            trigger_thread.start()
            self.processing_threads.append(trigger_thread)
            
            logger.info(f"Started {len(self.processing_threads)} background processing threads")
            
        except Exception as e:
            logger.error(f"Failed to start background processing: {e}")
    
    def _create_default_templates(self):
        """Create default campaign templates."""
        try:
            default_templates = [
                {
                    'id': 'lead_generation_standard',
                    'name': 'Standard Lead Generation Campaign',
                    'type': CampaignType.LEAD_GENERATION,
                    'channels': [CampaignChannel.SEARCH_ADS, CampaignChannel.SOCIAL_MEDIA, CampaignChannel.EMAIL],
                    'objectives': [CampaignObjective.LEAD_GENERATION, CampaignObjective.CONVERSIONS]
                },
                {
                    'id': 'brand_awareness_omnichannel',
                    'name': 'Omnichannel Brand Awareness',
                    'type': CampaignType.BRAND_AWARENESS,
                    'channels': [CampaignChannel.DISPLAY_ADS, CampaignChannel.VIDEO_ADS, CampaignChannel.SOCIAL_MEDIA, CampaignChannel.CONTENT_MARKETING],
                    'objectives': [CampaignObjective.AWARENESS, CampaignObjective.REACH, CampaignObjective.IMPRESSIONS]
                },
                {
                    'id': 'product_launch_integrated',
                    'name': 'Integrated Product Launch Campaign',
                    'type': CampaignType.PRODUCT_LAUNCH,
                    'channels': [CampaignChannel.EMAIL, CampaignChannel.SOCIAL_MEDIA, CampaignChannel.CONTENT_MARKETING, CampaignChannel.PR, CampaignChannel.INFLUENCER],
                    'objectives': [CampaignObjective.AWARENESS, CampaignObjective.ENGAGEMENT, CampaignObjective.CONVERSIONS]
                },
                {
                    'id': 'customer_retention_lifecycle',
                    'name': 'Customer Retention Lifecycle Campaign',
                    'type': CampaignType.CUSTOMER_RETENTION,
                    'channels': [CampaignChannel.EMAIL, CampaignChannel.SMS, CampaignChannel.PUSH_NOTIFICATION],
                    'objectives': [CampaignObjective.ENGAGEMENT, CampaignObjective.CONVERSIONS]
                }
            ]
            
            for template_config in default_templates:
                template = CampaignTemplate(
                    template_id=template_config['id'],
                    name=template_config['name'],
                    description=f"Default template for {template_config['name'].lower()}",
                    campaign_type=template_config['type'],
                    template_data={
                        'objectives': [obj.value for obj in template_config['objectives']],
                        'recommended_budget_split': self._calculate_default_budget_split(template_config['channels']),
                        'default_timing': {
                            'duration_days': 30,
                            'optimization_frequency': 'daily'
                        },
                        'success_metrics': self._get_default_success_metrics(template_config['type'])
                    },
                    default_channels=template_config['channels'],
                    required_fields=['name', 'budget', 'start_date', 'audience'],
                    optional_fields=['end_date', 'custom_objectives', 'advanced_targeting'],
                    created_by="system"
                )
                
                self.templates[template.template_id] = template
            
            logger.info(f"Created {len(default_templates)} default campaign templates")
            
        except Exception as e:
            logger.error(f"Failed to create default templates: {e}")
    
    def _calculate_default_budget_split(self, channels: List[CampaignChannel]) -> Dict[str, float]:
        """Calculate default budget allocation for channels."""
        # Simple even split with adjustments based on channel characteristics
        channel_weights = {
            CampaignChannel.SEARCH_ADS: 1.2,  # Higher intent, higher allocation
            CampaignChannel.SOCIAL_MEDIA: 1.0,
            CampaignChannel.EMAIL: 0.3,  # Lower cost, lower allocation
            CampaignChannel.DISPLAY_ADS: 1.0,
            CampaignChannel.VIDEO_ADS: 1.1,
            CampaignChannel.CONTENT_MARKETING: 0.8,
            CampaignChannel.INFLUENCER: 0.9,
            CampaignChannel.SMS: 0.2,
            CampaignChannel.PUSH_NOTIFICATION: 0.1
        }
        
        total_weight = sum(channel_weights.get(ch, 1.0) for ch in channels)
        
        return {
            ch.value: channel_weights.get(ch, 1.0) / total_weight
            for ch in channels
        }
    
    def _get_default_success_metrics(self, campaign_type: CampaignType) -> List[str]:
        """Get default success metrics for campaign type."""
        metrics_map = {
            CampaignType.LEAD_GENERATION: ['leads_generated', 'cost_per_lead', 'conversion_rate'],
            CampaignType.BRAND_AWARENESS: ['reach', 'impressions', 'brand_lift', 'aided_awareness'],
            CampaignType.CUSTOMER_ACQUISITION: ['new_customers', 'customer_acquisition_cost', 'roas'],
            CampaignType.CUSTOMER_RETENTION: ['retention_rate', 'customer_lifetime_value', 'repeat_purchases'],
            CampaignType.PRODUCT_LAUNCH: ['awareness', 'consideration', 'purchase_intent', 'initial_sales']
        }
        
        return metrics_map.get(campaign_type, ['impressions', 'clicks', 'conversions', 'roas'])
    
    def create_campaign(self,
                       name: str,
                       campaign_type: CampaignType,
                       objectives: List[CampaignObjective],
                       budget: CampaignBudget,
                       timing: CampaignTiming,
                       audience: CampaignAudience,
                       creative: CampaignCreative,
                       channels: List[ChannelConfiguration],
                       description: str = "",
                       goals: Optional[List[CampaignGoal]] = None,
                       triggers: Optional[List[CampaignTrigger]] = None,
                       created_by: str = "system") -> Optional[str]:
        """Create a new multi-channel campaign."""
        try:
            campaign_id = str(uuid.uuid4())
            
            # Validate campaign configuration
            validation_result = self._validate_campaign_config(
                budget, timing, audience, creative, channels
            )
            
            if not validation_result['is_valid']:
                logger.error(f"Campaign validation failed: {validation_result['errors']}")
                return None
            
            # Optimize budget allocation if auto-allocation is enabled
            if budget.auto_allocation:
                optimized_budget = self._optimize_budget_allocation(budget, channels, audience)
                budget.channel_allocation = optimized_budget
            
            # Create campaign
            campaign = Campaign(
                campaign_id=campaign_id,
                name=name,
                description=description,
                campaign_type=campaign_type,
                status=CampaignStatus.DRAFT,
                objectives=objectives,
                budget=budget,
                timing=timing,
                audience=audience,
                creative=creative,
                channels=channels,
                goals=goals or [],
                triggers=triggers or [],
                created_by=created_by
            )
            
            # Store campaign
            self.campaigns[campaign_id] = campaign
            
            # Store in Redis if available
            if self.redis_available:
                campaign_data = {
                    'name': campaign.name,
                    'type': campaign.campaign_type.value,
                    'status': campaign.status.value,
                    'created_at': campaign.created_at.isoformat(),
                    'budget': campaign.budget.total_budget,
                    'channels': len(campaign.channels)
                }
                
                self.redis_client.hset(f"campaign:{campaign_id}", mapping=campaign_data)
            
            # Register triggers
            for trigger in campaign.triggers:
                self.active_triggers[trigger.trigger_id] = trigger
            
            logger.info(f"Created campaign: {name} ({campaign_id})")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return None
    
    def _validate_campaign_config(self, budget: CampaignBudget, timing: CampaignTiming,
                                 audience: CampaignAudience, creative: CampaignCreative,
                                 channels: List[ChannelConfiguration]) -> Dict[str, Any]:
        """Validate campaign configuration."""
        errors = []
        warnings = []
        
        # Budget validation
        if budget.total_budget <= 0:
            errors.append("Total budget must be greater than 0")
        
        if budget.daily_budget and budget.daily_budget > budget.total_budget:
            errors.append("Daily budget cannot exceed total budget")
        
        # Check channel budget allocation
        total_allocation = sum(budget.channel_allocation.values())
        if total_allocation > 1.1:  # Allow 10% tolerance
            errors.append(f"Channel budget allocation exceeds 100% ({total_allocation*100:.1f}%)")
        elif total_allocation < 0.9:
            warnings.append(f"Channel budget allocation is less than 90% ({total_allocation*100:.1f}%)")
        
        # Timing validation
        if timing.end_date and timing.start_date >= timing.end_date:
            errors.append("Campaign end date must be after start date")
        
        if timing.start_date < datetime.now() - timedelta(hours=1):
            warnings.append("Campaign start date is in the past")
        
        # Audience validation
        if not audience.primary_segments:
            errors.append("At least one primary audience segment must be specified")
        
        if audience.audience_size_estimate and audience.audience_size_estimate < 1000:
            warnings.append("Small audience size may limit campaign effectiveness")
        
        # Creative validation
        if not creative.primary_assets:
            errors.append("At least one primary creative asset must be specified")
        
        # Channel validation
        if not channels:
            errors.append("At least one channel must be configured")
        
        enabled_channels = [ch for ch in channels if ch.is_enabled]
        if not enabled_channels:
            errors.append("At least one channel must be enabled")
        
        # Check for conflicting channel configurations
        channel_types = [ch.channel for ch in enabled_channels]
        if len(set(channel_types)) != len(channel_types):
            errors.append("Duplicate channels found in configuration")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _optimize_budget_allocation(self, budget: CampaignBudget, 
                                  channels: List[ChannelConfiguration],
                                  audience: CampaignAudience) -> Dict[CampaignChannel, float]:
        """Optimize budget allocation across channels using ML."""
        try:
            # Simple optimization based on historical performance and channel characteristics
            channel_scores = {}
            
            for channel_config in channels:
                if not channel_config.is_enabled:
                    continue
                
                channel = channel_config.channel
                
                # Base score from historical performance
                historical_performance = self._get_channel_historical_performance(channel)
                base_score = historical_performance.get('avg_roas', 3.0)
                
                # Adjust for audience fit
                audience_fit = self._calculate_audience_channel_fit(audience, channel)
                
                # Adjust for competition and saturation
                saturation_factor = self._estimate_channel_saturation(channel, budget.total_budget)
                
                # Combine factors
                final_score = base_score * audience_fit * saturation_factor
                channel_scores[channel] = final_score
            
            # Normalize scores to allocation percentages
            total_score = sum(channel_scores.values())
            
            if total_score == 0:
                # Fallback to even distribution
                return {ch: 1.0 / len(channels) for ch in channel_scores.keys()}
            
            # Apply minimum budget constraints
            allocation = {}
            for channel, score in channel_scores.items():
                base_allocation = score / total_score
                min_allocation = budget.min_channel_budget / budget.total_budget
                allocation[channel] = max(base_allocation, min_allocation)
            
            # Renormalize to ensure total is 1.0
            total_allocation = sum(allocation.values())
            allocation = {ch: alloc / total_allocation for ch, alloc in allocation.items()}
            
            return allocation
            
        except Exception as e:
            logger.error(f"Failed to optimize budget allocation: {e}")
            # Return even distribution as fallback
            enabled_channels = [ch.channel for ch in channels if ch.is_enabled]
            return {ch: 1.0 / len(enabled_channels) for ch in enabled_channels}
    
    def _get_channel_historical_performance(self, channel: CampaignChannel) -> Dict[str, float]:
        """Get historical performance data for a channel."""
        # Mock historical data - in production, this would query actual performance data
        performance_data = {
            CampaignChannel.SEARCH_ADS: {'avg_roas': 4.2, 'avg_ctr': 0.035, 'avg_cpc': 2.1},
            CampaignChannel.SOCIAL_MEDIA: {'avg_roas': 3.8, 'avg_ctr': 0.028, 'avg_cpc': 1.5},
            CampaignChannel.EMAIL: {'avg_roas': 5.5, 'avg_ctr': 0.045, 'avg_cpc': 0.1},
            CampaignChannel.DISPLAY_ADS: {'avg_roas': 2.8, 'avg_ctr': 0.015, 'avg_cpc': 1.2},
            CampaignChannel.VIDEO_ADS: {'avg_roas': 3.5, 'avg_ctr': 0.025, 'avg_cpc': 2.8}
        }
        
        return performance_data.get(channel, {'avg_roas': 3.0, 'avg_ctr': 0.025, 'avg_cpc': 2.0})
    
    def _calculate_audience_channel_fit(self, audience: CampaignAudience, channel: CampaignChannel) -> float:
        """Calculate how well an audience fits a particular channel."""
        # Simplified audience-channel fit calculation
        fit_scores = {
            CampaignChannel.SEARCH_ADS: 1.0,  # Universal fit
            CampaignChannel.SOCIAL_MEDIA: 0.9,  # High engagement audiences
            CampaignChannel.EMAIL: 1.1,  # Existing customers
            CampaignChannel.DISPLAY_ADS: 0.8,  # Broader audiences
            CampaignChannel.VIDEO_ADS: 0.9   # Engaging content
        }
        
        base_fit = fit_scores.get(channel, 0.8)
        
        # Adjust based on audience characteristics
        if audience.demographic_filters.get('age_min', 0) < 25:
            # Younger audiences prefer social and video
            if channel in [CampaignChannel.SOCIAL_MEDIA, CampaignChannel.VIDEO_ADS]:
                base_fit *= 1.2
        
        if len(audience.behavioral_filters) > 0:
            # Behavioral targeting works well with search and social
            if channel in [CampaignChannel.SEARCH_ADS, CampaignChannel.SOCIAL_MEDIA]:
                base_fit *= 1.1
        
        return min(base_fit, 1.5)  # Cap at 1.5x
    
    def _estimate_channel_saturation(self, channel: CampaignChannel, budget: float) -> float:
        """Estimate saturation factor for a channel based on budget."""
        # Mock saturation curves - in production, this would be more sophisticated
        saturation_curves = {
            CampaignChannel.SEARCH_ADS: {'threshold': 50000, 'decay_rate': 0.1},
            CampaignChannel.SOCIAL_MEDIA: {'threshold': 30000, 'decay_rate': 0.15},
            CampaignChannel.EMAIL: {'threshold': 10000, 'decay_rate': 0.05},
            CampaignChannel.DISPLAY_ADS: {'threshold': 40000, 'decay_rate': 0.12},
            CampaignChannel.VIDEO_ADS: {'threshold': 60000, 'decay_rate': 0.08}
        }
        
        curve = saturation_curves.get(channel, {'threshold': 30000, 'decay_rate': 0.1})
        
        if budget <= curve['threshold']:
            return 1.0
        else:
            excess = budget - curve['threshold']
            decay_factor = np.exp(-curve['decay_rate'] * (excess / curve['threshold']))
            return decay_factor
    
    def create_from_template(self, template_id: str, campaign_name: str,
                           customizations: Dict[str, Any],
                           created_by: str = "system") -> Optional[str]:
        """Create campaign from template."""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Start with template data
            template_data = copy.deepcopy(template.template_data)
            
            # Apply customizations
            for key, value in customizations.items():
                if key in template.required_fields and not value:
                    raise ValueError(f"Required field '{key}' cannot be empty")
                template_data[key] = value
            
            # Build campaign components from template
            objectives = [CampaignObjective(obj) for obj in template_data.get('objectives', [])]
            
            # Budget configuration
            budget_config = customizations.get('budget', {})
            budget_split = template_data.get('recommended_budget_split', {})
            
            budget = CampaignBudget(
                total_budget=budget_config.get('total', 10000),
                daily_budget=budget_config.get('daily'),
                channel_allocation={CampaignChannel(ch): allocation for ch, allocation in budget_split.items()},
                auto_allocation=budget_config.get('auto_allocation', True)
            )
            
            # Timing configuration
            timing_config = customizations.get('timing', {})
            default_timing = template_data.get('default_timing', {})
            
            start_date = timing_config.get('start_date', datetime.now() + timedelta(days=1))
            duration_days = timing_config.get('duration_days', default_timing.get('duration_days', 30))
            
            timing = CampaignTiming(
                start_date=start_date,
                end_date=start_date + timedelta(days=duration_days)
            )
            
            # Audience configuration
            audience_config = customizations.get('audience', {})
            audience = CampaignAudience(
                primary_segments=audience_config.get('primary_segments', ['general']),
                demographic_filters=audience_config.get('demographic_filters', {}),
                behavioral_filters=audience_config.get('behavioral_filters', {})
            )
            
            # Creative configuration
            creative_config = customizations.get('creative', {})
            creative = CampaignCreative(
                primary_assets=creative_config.get('primary_assets', []),
                dynamic_creative=creative_config.get('dynamic_creative', False)
            )
            
            # Channel configurations
            channels = []
            for channel in template.default_channels:
                channel_config = ChannelConfiguration(
                    channel=channel,
                    budget_allocation=budget_split.get(channel.value, 0),
                    optimization_goal=objectives[0] if objectives else CampaignObjective.CONVERSIONS
                )
                channels.append(channel_config)
            
            # Create campaign
            campaign_id = self.create_campaign(
                name=campaign_name,
                campaign_type=template.campaign_type,
                objectives=objectives,
                budget=budget,
                timing=timing,
                audience=audience,
                creative=creative,
                channels=channels,
                description=f"Created from template: {template.name}",
                created_by=created_by
            )
            
            if campaign_id:
                template.usage_count += 1
                logger.info(f"Created campaign from template {template_id}: {campaign_name}")
            
            return campaign_id
            
        except Exception as e:
            logger.error(f"Failed to create campaign from template: {e}")
            return None
    
    def launch_campaign(self, campaign_id: str, launch_immediately: bool = False) -> bool:
        """Launch a campaign across all configured channels."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.APPROVED, CampaignStatus.SCHEDULED]:
                raise ValueError(f"Campaign cannot be launched from status: {campaign.status}")
            
            # Update campaign status
            campaign.status = CampaignStatus.LAUNCHING
            campaign.updated_at = datetime.now()
            
            if launch_immediately:
                # Launch immediately
                self._execute_campaign_launch(campaign_id)
            else:
                # Queue for scheduled launch
                self.launch_queue.put({
                    'campaign_id': campaign_id,
                    'launch_time': campaign.timing.start_date
                })
            
            logger.info(f"Initiated launch for campaign: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch campaign {campaign_id}: {e}")
            return False
    
    def _process_launch_queue(self):
        """Background thread to process campaign launches."""
        while self.is_processing:
            try:
                try:
                    launch_item = self.launch_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                campaign_id = launch_item['campaign_id']
                launch_time = launch_item['launch_time']
                
                # Wait until launch time
                if launch_time > datetime.now():
                    wait_seconds = (launch_time - datetime.now()).total_seconds()
                    if wait_seconds > 0:
                        time.sleep(min(wait_seconds, 60))  # Sleep in chunks of max 1 minute
                        
                        # Re-queue if still not time
                        if launch_time > datetime.now():
                            self.launch_queue.put(launch_item)
                            continue
                
                # Execute launch
                self._execute_campaign_launch(campaign_id)
                self.launch_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in launch processing: {e}")
    
    def _execute_campaign_launch(self, campaign_id: str):
        """Execute campaign launch across all channels."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return
            
            campaign.launched_at = datetime.now()
            launch_results = {}
            
            # Launch on each channel
            for channel_config in campaign.channels:
                if not channel_config.is_enabled:
                    continue
                
                # Add launch delay if specified
                if channel_config.launch_delay_hours > 0:
                    delay_until = campaign.launched_at + timedelta(hours=channel_config.launch_delay_hours)
                    if delay_until > datetime.now():
                        # Schedule delayed launch
                        self.launch_queue.put({
                            'campaign_id': campaign_id,
                            'channel': channel_config.channel,
                            'launch_time': delay_until
                        })
                        continue
                
                # Launch on channel
                result = self._launch_on_channel(campaign, channel_config)
                launch_results[channel_config.channel.value] = result
            
            # Update campaign status based on results
            if any(result['success'] for result in launch_results.values()):
                campaign.status = CampaignStatus.ACTIVE
            else:
                campaign.status = CampaignStatus.FAILED
            
            campaign.metadata['launch_results'] = launch_results
            campaign.updated_at = datetime.now()
            
            logger.info(f"Campaign launch completed: {campaign_id} - {len(launch_results)} channels")
            
        except Exception as e:
            logger.error(f"Failed to execute campaign launch: {e}")
            if campaign_id in self.campaigns:
                self.campaigns[campaign_id].status = CampaignStatus.FAILED
    
    def _launch_on_channel(self, campaign: Campaign, channel_config: ChannelConfiguration) -> Dict[str, Any]:
        """Launch campaign on a specific channel."""
        try:
            # This would integrate with actual platform APIs
            # For demo purposes, we'll simulate the launch
            
            channel = channel_config.channel
            
            # Simulate API call based on channel
            if channel == CampaignChannel.SEARCH_ADS:
                result = self._launch_search_ads(campaign, channel_config)
            elif channel == CampaignChannel.SOCIAL_MEDIA:
                result = self._launch_social_media(campaign, channel_config)
            elif channel == CampaignChannel.EMAIL:
                result = self._launch_email_campaign(campaign, channel_config)
            elif channel == CampaignChannel.DISPLAY_ADS:
                result = self._launch_display_ads(campaign, channel_config)
            else:
                # Generic launch
                result = {
                    'success': True,
                    'platform_campaign_id': f"demo_{channel.value}_{campaign.campaign_id[:8]}",
                    'message': f"Successfully launched on {channel.value}"
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to launch on channel {channel_config.channel}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to launch on {channel_config.channel.value}"
            }
    
    def _launch_search_ads(self, campaign: Campaign, channel_config: ChannelConfiguration) -> Dict[str, Any]:
        """Simulate Google Ads campaign launch."""
        # Mock Google Ads API integration
        return {
            'success': True,
            'platform_campaign_id': f"gads_{campaign.campaign_id[:8]}",
            'message': 'Successfully created Google Ads campaign',
            'estimated_impressions': 25000,
            'estimated_clicks': 1250,
            'estimated_cost': channel_config.budget_allocation * campaign.budget.total_budget
        }
    
    def _launch_social_media(self, campaign: Campaign, channel_config: ChannelConfiguration) -> Dict[str, Any]:
        """Simulate social media campaign launch."""
        # Mock Facebook/Meta Ads API integration
        return {
            'success': True,
            'platform_campaign_id': f"fb_{campaign.campaign_id[:8]}",
            'message': 'Successfully created Facebook campaign',
            'estimated_reach': 50000,
            'estimated_engagement': 2500,
            'estimated_cost': channel_config.budget_allocation * campaign.budget.total_budget
        }
    
    def _launch_email_campaign(self, campaign: Campaign, channel_config: ChannelConfiguration) -> Dict[str, Any]:
        """Simulate email campaign launch."""
        # Mock email platform integration (Mailchimp, SendGrid, etc.)
        return {
            'success': True,
            'platform_campaign_id': f"email_{campaign.campaign_id[:8]}",
            'message': 'Successfully created email campaign',
            'recipient_count': len(campaign.audience.primary_segments) * 1000,
            'estimated_opens': 2500,
            'estimated_clicks': 375
        }
    
    def _launch_display_ads(self, campaign: Campaign, channel_config: ChannelConfiguration) -> Dict[str, Any]:
        """Simulate display advertising campaign launch."""
        # Mock programmatic advertising platform integration
        return {
            'success': True,
            'platform_campaign_id': f"dsp_{campaign.campaign_id[:8]}",
            'message': 'Successfully created display campaign',
            'estimated_impressions': 100000,
            'estimated_clicks': 1500,
            'estimated_cost': channel_config.budget_allocation * campaign.budget.total_budget
        }
    
    def _process_optimization_queue(self):
        """Background thread to process campaign optimizations."""
        while self.is_processing:
            try:
                try:
                    campaign_id = self.optimization_queue.get(timeout=5)
                except queue.Empty:
                    continue
                
                self._optimize_campaign(campaign_id)
                self.optimization_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in optimization processing: {e}")
    
    def _optimize_campaign(self, campaign_id: str):
        """Perform campaign optimization."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign or campaign.status != CampaignStatus.ACTIVE:
                return
            
            optimization_results = []
            
            # Budget reallocation optimization
            if campaign.optimization_strategy in [OptimizationStrategy.AUTO_BUDGET, OptimizationStrategy.HYBRID]:
                budget_result = self._optimize_budget_reallocation(campaign)
                optimization_results.append(budget_result)
            
            # Bid optimization
            if campaign.optimization_strategy in [OptimizationStrategy.AUTO_BID, OptimizationStrategy.HYBRID]:
                bid_result = self._optimize_channel_bids(campaign)
                optimization_results.append(bid_result)
            
            # Audience optimization
            if campaign.optimization_strategy in [OptimizationStrategy.AUTO_AUDIENCE, OptimizationStrategy.HYBRID]:
                audience_result = self._optimize_audience_targeting(campaign)
                optimization_results.append(audience_result)
            
            # Creative optimization
            if campaign.optimization_strategy in [OptimizationStrategy.AUTO_CREATIVE, OptimizationStrategy.HYBRID]:
                creative_result = self._optimize_creative_rotation(campaign)
                optimization_results.append(creative_result)
            
            # Store optimization results
            campaign.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'results': optimization_results,
                'strategy': campaign.optimization_strategy.value
            })
            
            campaign.updated_at = datetime.now()
            
            logger.debug(f"Optimization completed for campaign: {campaign_id}")
            
        except Exception as e:
            logger.error(f"Failed to optimize campaign {campaign_id}: {e}")
    
    def _optimize_budget_reallocation(self, campaign: Campaign) -> Dict[str, Any]:
        """Optimize budget allocation across channels."""
        try:
            # Get current performance data
            channel_performance = {}
            for channel_config in campaign.channels:
                if channel_config.is_enabled:
                    # Mock performance data
                    channel_performance[channel_config.channel] = {
                        'roas': np.random.uniform(2.0, 6.0),
                        'cpa': np.random.uniform(15, 45),
                        'conversion_rate': np.random.uniform(0.02, 0.08)
                    }
            
            # Calculate optimal reallocation
            total_performance_score = 0
            channel_scores = {}
            
            for channel, performance in channel_performance.items():
                # Simple scoring based on ROAS and conversion rate
                score = performance['roas'] * performance['conversion_rate'] * 100
                channel_scores[channel] = score
                total_performance_score += score
            
            # Reallocate budget based on performance
            new_allocation = {}
            changes_made = []
            
            for channel, score in channel_scores.items():
                new_allocation_pct = score / total_performance_score if total_performance_score > 0 else 0
                current_allocation = campaign.budget.channel_allocation.get(channel, 0)
                
                if abs(new_allocation_pct - current_allocation) > 0.05:  # 5% threshold
                    campaign.budget.channel_allocation[channel] = new_allocation_pct
                    changes_made.append(f"{channel.value}: {current_allocation:.2%} -> {new_allocation_pct:.2%}")
            
            return {
                'optimization_type': 'budget_reallocation',
                'changes_made': len(changes_made),
                'details': changes_made,
                'performance_improvement': 'estimated 5-15% ROAS improvement'
            }
            
        except Exception as e:
            logger.error(f"Budget reallocation optimization failed: {e}")
            return {'optimization_type': 'budget_reallocation', 'error': str(e)}
    
    def _optimize_channel_bids(self, campaign: Campaign) -> Dict[str, Any]:
        """Optimize bidding strategies for channels."""
        # Mock bid optimization
        return {
            'optimization_type': 'bid_optimization',
            'changes_made': len(campaign.channels),
            'details': ['Adjusted target CPA for search campaigns', 'Updated ROAS target for social campaigns'],
            'performance_improvement': 'estimated 10-20% cost efficiency improvement'
        }
    
    def _optimize_audience_targeting(self, campaign: Campaign) -> Dict[str, Any]:
        """Optimize audience targeting."""
        # Mock audience optimization
        return {
            'optimization_type': 'audience_optimization',
            'changes_made': 2,
            'details': ['Added high-converting lookalike segment', 'Excluded low-performing demographic'],
            'performance_improvement': 'estimated 8-12% conversion rate improvement'
        }
    
    def _optimize_creative_rotation(self, campaign: Campaign) -> Dict[str, Any]:
        """Optimize creative asset rotation."""
        # Mock creative optimization
        return {
            'optimization_type': 'creative_optimization',
            'changes_made': 1,
            'details': ['Paused underperforming creative variant', 'Increased allocation to top performer'],
            'performance_improvement': 'estimated 15-25% CTR improvement'
        }
    
    def _process_trigger_queue(self):
        """Background thread to monitor campaign triggers."""
        while self.is_processing:
            try:
                # Check all active triggers periodically
                for trigger_id, trigger in self.active_triggers.items():
                    if trigger.is_active and self._should_evaluate_trigger(trigger):
                        if self._evaluate_trigger_conditions(trigger):
                            self._execute_trigger(trigger)
                
                time.sleep(10)  # Check triggers every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in trigger processing: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _should_evaluate_trigger(self, trigger: CampaignTrigger) -> bool:
        """Check if a trigger should be evaluated now."""
        if trigger.last_triggered:
            time_since_last = datetime.now() - trigger.last_triggered
            if time_since_last < trigger.cooldown_period:
                return False
        
        if trigger.max_triggers_per_day:
            # Check daily trigger count (simplified)
            if trigger.trigger_count >= trigger.max_triggers_per_day:
                return False
        
        return True
    
    def _evaluate_trigger_conditions(self, trigger: CampaignTrigger) -> bool:
        """Evaluate if trigger conditions are met."""
        # Mock trigger evaluation - in production, this would check real conditions
        import random
        
        if trigger.trigger_type == TriggerType.BEHAVIORAL:
            return random.random() > 0.7  # 30% chance of behavioral trigger
        elif trigger.trigger_type == TriggerType.ENGAGEMENT:
            return random.random() > 0.8  # 20% chance of engagement trigger
        elif trigger.trigger_type == TriggerType.CUSTOM_EVENT:
            return random.random() > 0.9  # 10% chance of custom event trigger
        
        return False
    
    def _execute_trigger(self, trigger: CampaignTrigger):
        """Execute a campaign trigger."""
        try:
            trigger.last_triggered = datetime.now()
            trigger.trigger_count += 1
            
            # Find campaigns that use this trigger
            triggered_campaigns = []
            for campaign in self.campaigns.values():
                if any(t.trigger_id == trigger.trigger_id for t in campaign.triggers):
                    triggered_campaigns.append(campaign)
            
            # Execute trigger actions
            for campaign in triggered_campaigns:
                self._execute_trigger_action(campaign, trigger)
            
            logger.info(f"Executed trigger: {trigger.trigger_id} for {len(triggered_campaigns)} campaigns")
            
        except Exception as e:
            logger.error(f"Failed to execute trigger {trigger.trigger_id}: {e}")
    
    def _execute_trigger_action(self, campaign: Campaign, trigger: CampaignTrigger):
        """Execute trigger action for a specific campaign."""
        # Mock trigger actions - in production, these would be real actions
        actions = {
            TriggerType.BEHAVIORAL: "Increased budget for high-intent users",
            TriggerType.ENGAGEMENT: "Launched follow-up engagement campaign",
            TriggerType.CUSTOM_EVENT: "Executed custom automation sequence"
        }
        
        action_description = actions.get(trigger.trigger_type, "Executed trigger action")
        
        # Add to campaign metadata
        if 'triggered_actions' not in campaign.metadata:
            campaign.metadata['triggered_actions'] = []
        
        campaign.metadata['triggered_actions'].append({
            'trigger_id': trigger.trigger_id,
            'action': action_description,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        return self.campaigns.get(campaign_id)
    
    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive campaign performance data."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return {}
            
            # Mock performance data - in production, this would aggregate real data
            performance = {
                'campaign_info': {
                    'name': campaign.name,
                    'type': campaign.campaign_type.value,
                    'status': campaign.status.value,
                    'budget': campaign.budget.total_budget,
                    'start_date': campaign.timing.start_date.isoformat(),
                    'days_running': (datetime.now() - (campaign.launched_at or campaign.created_at)).days
                },
                'overall_metrics': {
                    'total_spent': campaign.budget.total_budget * 0.75,  # Mock spend
                    'impressions': 250000,
                    'clicks': 12500,
                    'conversions': 625,
                    'ctr': 0.05,
                    'conversion_rate': 0.05,
                    'cpa': 24.0,
                    'roas': 4.2
                },
                'channel_performance': {},
                'goal_progress': [],
                'optimization_summary': {
                    'optimizations_applied': len(campaign.optimization_history),
                    'last_optimization': campaign.optimization_history[-1]['timestamp'] if campaign.optimization_history else None,
                    'performance_trend': 'improving'
                }
            }
            
            # Channel-specific performance
            for channel_config in campaign.channels:
                if channel_config.is_enabled:
                    channel_perf = self._get_channel_performance_mock(channel_config.channel)
                    performance['channel_performance'][channel_config.channel.value] = channel_perf
            
            # Goal progress
            for goal in campaign.goals:
                progress = {
                    'goal_name': goal.name,
                    'target': goal.target_value,
                    'current': goal.current_value,
                    'progress': goal.progress_percentage,
                    'achieved': goal.is_achieved
                }
                performance['goal_progress'].append(progress)
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get campaign performance: {e}")
            return {}
    
    def _get_channel_performance_mock(self, channel: CampaignChannel) -> Dict[str, Any]:
        """Generate mock performance data for a channel."""
        import random
        
        base_performance = {
            CampaignChannel.SEARCH_ADS: {'impressions': 80000, 'clicks': 4000, 'conversions': 200, 'spend': 8000},
            CampaignChannel.SOCIAL_MEDIA: {'impressions': 120000, 'clicks': 3600, 'conversions': 180, 'spend': 5400},
            CampaignChannel.EMAIL: {'impressions': 25000, 'clicks': 1250, 'conversions': 125, 'spend': 250},
            CampaignChannel.DISPLAY_ADS: {'impressions': 200000, 'clicks': 3000, 'conversions': 120, 'spend': 3600}
        }
        
        perf = base_performance.get(channel, {'impressions': 50000, 'clicks': 2000, 'conversions': 100, 'spend': 2000})
        
        # Add calculated metrics
        perf['ctr'] = perf['clicks'] / max(perf['impressions'], 1)
        perf['conversion_rate'] = perf['conversions'] / max(perf['clicks'], 1)
        perf['cpa'] = perf['spend'] / max(perf['conversions'], 1)
        perf['roas'] = (perf['conversions'] * 50) / max(perf['spend'], 1)  # Assume $50 AOV
        
        return perf
    
    def pause_campaign(self, campaign_id: str) -> bool:
        """Pause an active campaign."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return False
            
            if campaign.status != CampaignStatus.ACTIVE:
                logger.warning(f"Cannot pause campaign in status: {campaign.status}")
                return False
            
            campaign.status = CampaignStatus.PAUSED
            campaign.updated_at = datetime.now()
            
            # In production, this would pause campaigns on all platforms
            logger.info(f"Paused campaign: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause campaign: {e}")
            return False
    
    def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return False
            
            if campaign.status != CampaignStatus.PAUSED:
                logger.warning(f"Cannot resume campaign in status: {campaign.status}")
                return False
            
            campaign.status = CampaignStatus.ACTIVE
            campaign.updated_at = datetime.now()
            
            # Queue for optimization check
            self.optimization_queue.put(campaign_id)
            
            logger.info(f"Resumed campaign: {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume campaign: {e}")
            return False
    
    def get_campaign_insights(self, campaign_id: str) -> Dict[str, Any]:
        """Get AI-powered insights for a campaign."""
        try:
            campaign = self.campaigns.get(campaign_id)
            if not campaign:
                return {}
            
            performance = self.get_campaign_performance(campaign_id)
            
            insights = {
                'performance_summary': {
                    'overall_health': 'good',
                    'trend': 'improving',
                    'key_strengths': [],
                    'areas_for_improvement': [],
                    'risk_factors': []
                },
                'recommendations': [],
                'predicted_outcomes': {},
                'competitive_analysis': {},
                'optimization_opportunities': []
            }
            
            # Analyze performance metrics
            metrics = performance.get('overall_metrics', {})
            
            # Performance analysis
            if metrics.get('roas', 0) > 4.0:
                insights['performance_summary']['key_strengths'].append('High ROAS performance')
            elif metrics.get('roas', 0) < 2.0:
                insights['performance_summary']['areas_for_improvement'].append('ROAS below target')
                insights['recommendations'].append('Consider adjusting targeting or creative to improve ROAS')
            
            if metrics.get('ctr', 0) > 0.04:
                insights['performance_summary']['key_strengths'].append('Strong click-through rate')
            elif metrics.get('ctr', 0) < 0.02:
                insights['performance_summary']['areas_for_improvement'].append('Low click-through rate')
                insights['recommendations'].append('Test new creative variations to improve engagement')
            
            if metrics.get('conversion_rate', 0) > 0.05:
                insights['performance_summary']['key_strengths'].append('High conversion rate')
            elif metrics.get('conversion_rate', 0) < 0.02:
                insights['performance_summary']['areas_for_improvement'].append('Low conversion rate')
                insights['recommendations'].append('Review landing page experience and conversion funnel')
            
            # Budget utilization analysis
            spend_rate = metrics.get('total_spent', 0) / campaign.budget.total_budget
            days_running = performance['campaign_info'].get('days_running', 1)
            
            if spend_rate > 0.8 and days_running < 20:
                insights['performance_summary']['risk_factors'].append('High budget burn rate')
                insights['recommendations'].append('Consider reducing daily budget or improving cost efficiency')
            
            # Channel performance analysis
            channel_performance = performance.get('channel_performance', {})
            if channel_performance:
                best_channel = max(channel_performance.items(), key=lambda x: x[1].get('roas', 0))
                worst_channel = min(channel_performance.items(), key=lambda x: x[1].get('roas', 0))
                
                insights['optimization_opportunities'].append(
                    f"Consider reallocating budget from {worst_channel[0]} (ROAS: {worst_channel[1].get('roas', 0):.2f}) "
                    f"to {best_channel[0]} (ROAS: {best_channel[1].get('roas', 0):.2f})"
                )
            
            # Predicted outcomes
            if metrics.get('roas', 0) > 3.0:
                insights['predicted_outcomes']['30_day_projection'] = {
                    'estimated_conversions': int(metrics.get('conversions', 0) * 1.5),
                    'estimated_revenue': metrics.get('conversions', 0) * 1.5 * 50,  # Assume $50 AOV
                    'confidence': 'high'
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate campaign insights: {e}")
            return {}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of all campaigns in the portfolio."""
        try:
            summary = {
                'total_campaigns': len(self.campaigns),
                'campaigns_by_status': defaultdict(int),
                'campaigns_by_type': defaultdict(int),
                'total_budget': 0,
                'total_spend': 0,
                'active_channels': set(),
                'performance_summary': {
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_conversions': 0,
                    'average_roas': 0,
                    'average_ctr': 0
                },
                'top_performers': [],
                'underperformers': [],
                'optimization_summary': {
                    'total_optimizations': 0,
                    'campaigns_optimized': 0
                }
            }
            
            campaign_performances = []
            
            for campaign in self.campaigns.values():
                # Count by status and type
                summary['campaigns_by_status'][campaign.status.value] += 1
                summary['campaigns_by_type'][campaign.campaign_type.value] += 1
                
                # Budget totals
                summary['total_budget'] += campaign.budget.total_budget
                
                # Active channels
                for channel_config in campaign.channels:
                    if channel_config.is_enabled:
                        summary['active_channels'].add(channel_config.channel.value)
                
                # Performance data
                performance = self.get_campaign_performance(campaign.campaign_id)
                metrics = performance.get('overall_metrics', {})
                
                if metrics:
                    summary['performance_summary']['total_impressions'] += metrics.get('impressions', 0)
                    summary['performance_summary']['total_clicks'] += metrics.get('clicks', 0)
                    summary['performance_summary']['total_conversions'] += metrics.get('conversions', 0)
                    summary['total_spend'] += metrics.get('total_spent', 0)
                    
                    # Collect for ranking
                    campaign_performances.append({
                        'campaign_id': campaign.campaign_id,
                        'name': campaign.name,
                        'roas': metrics.get('roas', 0),
                        'conversions': metrics.get('conversions', 0)
                    })
                
                # Optimization data
                summary['optimization_summary']['total_optimizations'] += len(campaign.optimization_history)
                if campaign.optimization_history:
                    summary['optimization_summary']['campaigns_optimized'] += 1
            
            # Calculate averages
            if summary['total_campaigns'] > 0:
                total_impressions = summary['performance_summary']['total_impressions']
                total_clicks = summary['performance_summary']['total_clicks']
                
                if total_impressions > 0:
                    summary['performance_summary']['average_ctr'] = total_clicks / total_impressions
                
                if campaign_performances:
                    summary['performance_summary']['average_roas'] = np.mean([cp['roas'] for cp in campaign_performances])
            
            # Top and underperformers
            if campaign_performances:
                sorted_by_roas = sorted(campaign_performances, key=lambda x: x['roas'], reverse=True)
                summary['top_performers'] = sorted_by_roas[:3]
                summary['underperformers'] = [cp for cp in sorted_by_roas if cp['roas'] < 2.0][-3:]
            
            summary['active_channels'] = list(summary['active_channels'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate portfolio summary: {e}")
            return {}


def create_sample_campaign_builder() -> MultiChannelCampaignBuilder:
    """Create sample multi-channel campaign builder for demonstration."""
    
    builder = MultiChannelCampaignBuilder()
    
    # Create sample campaigns
    sample_campaigns = [
        {
            'name': 'Q1 Digital Marketing Campaign',
            'type': CampaignType.LEAD_GENERATION,
            'budget': 50000,
            'channels': [CampaignChannel.SEARCH_ADS, CampaignChannel.SOCIAL_MEDIA, CampaignChannel.EMAIL]
        },
        {
            'name': 'Brand Awareness Spring Campaign',
            'type': CampaignType.BRAND_AWARENESS,
            'budget': 75000,
            'channels': [CampaignChannel.DISPLAY_ADS, CampaignChannel.VIDEO_ADS, CampaignChannel.SOCIAL_MEDIA]
        },
        {
            'name': 'Product Launch Integrated Campaign',
            'type': CampaignType.PRODUCT_LAUNCH,
            'budget': 60000,
            'channels': [CampaignChannel.EMAIL, CampaignChannel.CONTENT_MARKETING, CampaignChannel.PR, CampaignChannel.INFLUENCER]
        }
    ]
    
    # Create campaigns
    for i, campaign_config in enumerate(sample_campaigns, 1):
        # Budget configuration
        budget = CampaignBudget(
            total_budget=campaign_config['budget'],
            daily_budget=campaign_config['budget'] / 30,
            auto_allocation=True
        )
        
        # Timing configuration
        timing = CampaignTiming(
            start_date=datetime.now() + timedelta(days=i),
            end_date=datetime.now() + timedelta(days=30+i)
        )
        
        # Audience configuration
        audience = CampaignAudience(
            primary_segments=['target_segment_' + str(i)],
            demographic_filters={'age_min': 25, 'age_max': 54},
            audience_size_estimate=100000
        )
        
        # Creative configuration
        creative = CampaignCreative(
            primary_assets=[f'asset_{i}_primary'],
            variant_assets=[f'asset_{i}_variant_1', f'asset_{i}_variant_2'],
            dynamic_creative=True
        )
        
        # Channel configurations
        channels = []
        for channel in campaign_config['channels']:
            channel_config = ChannelConfiguration(
                channel=channel,
                budget_allocation=1.0 / len(campaign_config['channels']),
                optimization_goal=CampaignObjective.CONVERSIONS
            )
            channels.append(channel_config)
        
        # Goals
        goals = [
            CampaignGoal(
                goal_id=f'goal_{i}_conversions',
                name='Conversion Goal',
                metric='conversions',
                target_value=500,
                priority='high'
            ),
            CampaignGoal(
                goal_id=f'goal_{i}_roas',
                name='ROAS Goal',
                metric='roas',
                target_value=4.0,
                priority='medium'
            )
        ]
        
        # Create campaign
        campaign_id = builder.create_campaign(
            name=campaign_config['name'],
            campaign_type=campaign_config['type'],
            objectives=[CampaignObjective.CONVERSIONS, CampaignObjective.TRAFFIC],
            budget=budget,
            timing=timing,
            audience=audience,
            creative=creative,
            channels=channels,
            goals=goals,
            created_by="demo_user"
        )
        
        if campaign_id:
            # Simulate some campaigns as launched
            if i <= 2:
                builder.launch_campaign(campaign_id, launch_immediately=True)
    
    return builder


def run_campaign_builder_demo():
    """
    Run the multi-channel campaign builder demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🚀 Multi-Channel Campaign Builder Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Unified campaign creation across multiple channels")
    print("  • Intelligent budget allocation and optimization")
    print("  • Automated audience segmentation and targeting")
    print("  • Dynamic creative asset assignment")
    print("  • Cross-channel performance tracking")
    print("  • Real-time campaign optimization")
    print("  • Template-based campaign generation")
    print("  • Trigger-based campaign automation")
    
    print("\n📊 Supported Channels:")
    for channel in list(CampaignChannel)[:8]:  # Show first 8 channels
        print(f"  • {channel.value}")
    print(f"  • ... and {len(CampaignChannel) - 8} more channels")
    
    print("\n📈 Campaign Types:")
    for campaign_type in list(CampaignType)[:6]:  # Show first 6 types
        print(f"  • {campaign_type.value}")
    print(f"  • ... and {len(CampaignType) - 6} more campaign types")
    
    print("\n🚀 Initializing campaign builder...")
    builder = create_sample_campaign_builder()
    
    print("✅ Campaign builder initialized")
    print(f"   • Campaigns created: {len(builder.campaigns)}")
    print(f"   • Templates available: {len(builder.templates)}")
    print(f"   • Active triggers: {len(builder.active_triggers)}")
    
    # Portfolio summary
    portfolio = builder.get_portfolio_summary()
    
    print("\n📁 Campaign Portfolio Summary:")
    print(f"   • Total Campaigns: {portfolio['total_campaigns']}")
    print(f"   • Total Budget: ${portfolio['total_budget']:,.0f}")
    print(f"   • Total Spend: ${portfolio['total_spend']:,.0f}")
    print(f"   • Active Channels: {len(portfolio['active_channels'])}")
    
    print("\n   By Status:")
    for status, count in portfolio['campaigns_by_status'].items():
        print(f"     • {status}: {count}")
    
    print("\n   By Type:")
    for campaign_type, count in portfolio['campaigns_by_type'].items():
        print(f"     • {campaign_type}: {count}")
    
    # Performance overview
    perf_summary = portfolio['performance_summary']
    print(f"\n📊 Overall Performance:")
    print(f"   • Total Impressions: {perf_summary['total_impressions']:,}")
    print(f"   • Total Clicks: {perf_summary['total_clicks']:,}")
    print(f"   • Total Conversions: {perf_summary['total_conversions']:,}")
    print(f"   • Average CTR: {perf_summary['average_ctr']*100:.2f}%")
    print(f"   • Average ROAS: {perf_summary['average_roas']:.2f}x")
    
    # Top performers
    if portfolio['top_performers']:
        print("\n🏆 Top Performing Campaigns:")
        for i, campaign in enumerate(portfolio['top_performers'][:3], 1):
            print(f"   {i}. {campaign['name']} - ROAS: {campaign['roas']:.2f}x, Conversions: {campaign['conversions']:,}")
    
    # Templates
    print("\n📋 Available Templates:")
    for template_id, template in list(builder.templates.items())[:3]:  # Show first 3
        print(f"   • {template.name}")
        print(f"     - Type: {template.campaign_type.value}")
        print(f"     - Channels: {len(template.default_channels)}")
        print(f"     - Usage: {template.usage_count} times")
    
    # Campaign details for first campaign
    if builder.campaigns:
        first_campaign_id = list(builder.campaigns.keys())[0]
        campaign = builder.campaigns[first_campaign_id]
        performance = builder.get_campaign_performance(first_campaign_id)
        
        print(f"\n🔍 Campaign Details - {campaign.name}:")
        print(f"   • Type: {campaign.campaign_type.value}")
        print(f"   • Status: {campaign.status.value}")
        print(f"   • Budget: ${campaign.budget.total_budget:,.0f}")
        print(f"   • Channels: {len([ch for ch in campaign.channels if ch.is_enabled])}")
        print(f"   • Goals: {len(campaign.goals)}")
        
        if performance.get('overall_metrics'):
            metrics = performance['overall_metrics']
            print(f"   • ROAS: {metrics['roas']:.2f}x")
            print(f"   • Conversions: {metrics['conversions']:,}")
            print(f"   • Spend: ${metrics['total_spent']:,.0f}")
        
        # Show insights
        insights = builder.get_campaign_insights(first_campaign_id)
        if insights.get('recommendations'):
            print(f"   • Top Recommendation: {insights['recommendations'][0]}")
    
    # Optimization summary
    opt_summary = portfolio['optimization_summary']
    print(f"\n⚡ Optimization Summary:")
    print(f"   • Total Optimizations Applied: {opt_summary['total_optimizations']}")
    print(f"   • Campaigns Optimized: {opt_summary['campaigns_optimized']}/{portfolio['total_campaigns']}")
    
    print("\n🌟 Advanced Capabilities:")
    print("  • AI-powered budget optimization across channels")
    print("  • Real-time performance monitoring and alerts")
    print("  • Automated bid and audience optimization")
    print("  • Cross-campaign performance benchmarking")
    print("  • Predictive campaign outcome modeling")
    print("  • Dynamic creative rotation and testing")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return builder


if __name__ == "__main__":
    run_campaign_builder_demo()

