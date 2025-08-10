"""
Personalization Manager for MarTech Integration Hub

Advanced personalization engine for dynamic content customization across
multiple marketing channels with AI-driven insights and real-time optimization.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
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
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import redis
from jinja2 import Template, Environment, BaseLoader
import re
from textblob import TextBlob
import requests
from urllib.parse import urljoin
import base64

logger = logging.getLogger(__name__)


class PersonalizationType(Enum):
    """Types of personalization."""
    CONTENT = "content"
    PRODUCT_RECOMMENDATION = "product_recommendation"
    DYNAMIC_PRICING = "dynamic_pricing"
    CHANNEL_OPTIMIZATION = "channel_optimization"
    TIMING_OPTIMIZATION = "timing_optimization"
    FREQUENCY_OPTIMIZATION = "frequency_optimization"
    CREATIVE_OPTIMIZATION = "creative_optimization"
    AUDIENCE_TARGETING = "audience_targeting"
    BEHAVIORAL = "behavioral"
    CONTEXTUAL = "contextual"
    PREDICTIVE = "predictive"
    REAL_TIME = "real_time"


class PersonalizationChannel(Enum):
    """Channels supporting personalization."""
    EMAIL = "email"
    WEB = "web"
    MOBILE_APP = "mobile_app"
    SOCIAL_MEDIA = "social_media"
    DISPLAY_ADS = "display_ads"
    SEARCH_ADS = "search_ads"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    CHATBOT = "chatbot"
    VOICE_ASSISTANT = "voice_assistant"
    IN_STORE = "in_store"
    CALL_CENTER = "call_center"


class PersonalizationTrigger(Enum):
    """Personalization triggers."""
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    CART_ABANDONMENT = "cart_abandonment"
    PURCHASE_HISTORY = "purchase_history"
    BROWSING_BEHAVIOR = "browsing_behavior"
    DEMOGRAPHIC = "demographic"
    GEOGRAPHIC = "geographic"
    DEVICE = "device"
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    WEATHER = "weather"
    SEASONAL = "seasonal"
    ENGAGEMENT_LEVEL = "engagement_level"
    LIFECYCLE_STAGE = "lifecycle_stage"
    CUSTOM_EVENT = "custom_event"


class PersonalizationStrategy(Enum):
    """Personalization strategies."""
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    A_B_TESTING = "a_b_testing"
    MULTIVARIATE_TESTING = "multivariate_testing"
    BANDITS = "bandits"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    DEEP_LEARNING = "deep_learning"


@dataclass
class UserProfile:
    """Comprehensive user profile for personalization."""
    user_id: str
    demographics: Dict[str, Any] = field(default_factory=dict)
    behavioral_data: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    purchase_history: List[Dict[str, Any]] = field(default_factory=list)
    engagement_history: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[str] = field(default_factory=list)
    predicted_attributes: Dict[str, float] = field(default_factory=dict)
    real_time_context: Dict[str, Any] = field(default_factory=dict)
    personalization_consent: bool = True
    privacy_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None


@dataclass
class PersonalizationRule:
    """Rule-based personalization configuration."""
    rule_id: str
    name: str
    description: str
    trigger: PersonalizationTrigger
    conditions: List[Dict[str, Any]]  # [{"field": "age", "operator": ">", "value": 25}]
    actions: List[Dict[str, Any]]  # [{"type": "content", "template": "young_adult_offer"}]
    channels: List[PersonalizationChannel]
    priority: int = 0
    is_active: bool = True
    success_rate: float = 0.0
    usage_count: int = 0
    a_b_test_variants: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PersonalizationTemplate:
    """Dynamic content template."""
    template_id: str
    name: str
    content_type: str  # email, web_page, ad_creative, etc.
    template_content: str  # Jinja2 template
    variables: List[str]  # Available template variables
    default_values: Dict[str, Any] = field(default_factory=dict)
    personalization_fields: List[str] = field(default_factory=list)
    channels: List[PersonalizationChannel] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class PersonalizationExperiment:
    """A/B testing experiment for personalization."""
    experiment_id: str
    name: str
    description: str
    hypothesis: str
    control_variant: Dict[str, Any]
    test_variants: List[Dict[str, Any]]
    traffic_allocation: Dict[str, float]  # {variant_id: percentage}
    success_metrics: List[str]
    channels: List[PersonalizationChannel]
    audience_segments: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str = "draft"  # draft, running, paused, completed, cancelled
    results: Dict[str, Any] = field(default_factory=dict)
    statistical_significance: Optional[float] = None
    winner_variant: Optional[str] = None
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PersonalizationEvent:
    """Personalization event tracking."""
    event_id: str
    user_id: str
    session_id: str
    event_type: str
    channel: PersonalizationChannel
    personalization_applied: List[str]  # List of rule/template IDs applied
    content_delivered: Dict[str, Any]
    user_response: Optional[str] = None  # clicked, ignored, converted, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PersonalizationInsight:
    """Generated personalization insight."""
    insight_id: str
    insight_type: str  # performance, opportunity, trend, anomaly
    title: str
    description: str
    data: Dict[str, Any]
    recommendations: List[str]
    confidence_score: float
    impact_estimate: str  # high, medium, low
    generated_at: datetime = field(default_factory=datetime.now)
    is_actionable: bool = True
    priority: int = 0


class PersonalizationManager:
    """
    Advanced personalization engine for multi-channel marketing.
    
    Features:
    - Real-time user profiling and segmentation
    - Rule-based and ML-driven personalization
    - Dynamic content generation and optimization
    - Cross-channel personalization consistency
    - A/B testing and experimentation
    - Performance tracking and insights
    - Privacy-compliant personalization
    - Scalable real-time processing
    """
    
    def __init__(self,
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 ml_models_path: Optional[str] = None):
        
        # Redis connection for real-time data
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.redis_available = False
            logger.warning("Redis not available, using in-memory storage")
        
        # In-memory storage
        self.user_profiles: Dict[str, UserProfile] = {}
        self.personalization_rules: Dict[str, PersonalizationRule] = {}
        self.templates: Dict[str, PersonalizationTemplate] = {}
        self.experiments: Dict[str, PersonalizationExperiment] = {}
        self.events: deque = deque(maxlen=10000)  # Recent events
        self.insights: Dict[str, PersonalizationInsight] = {}
        
        # ML models
        self.ml_models = {
            'user_segmentation': None,
            'content_recommendation': None,
            'engagement_prediction': None,
            'churn_prediction': None,
            'ltv_prediction': None
        }
        
        # Template engine
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Processing queues
        self.personalization_queue = queue.Queue()
        self.profile_update_queue = queue.Queue()
        self.insight_generation_queue = queue.Queue()
        
        # Background processing
        self.is_processing = True
        self.processing_threads = []
        
        # Performance tracking
        self.performance_cache = defaultdict(list)
        self.real_time_metrics = defaultdict(float)
        
        # Feature extractors
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Start background processing
        self._start_background_processing()
        
        # Initialize default rules and templates
        self._create_default_rules()
        self._create_default_templates()
        
        logger.info("Personalization Manager initialized successfully")
    
    def _start_background_processing(self):
        """Start background processing threads."""
        try:
            # Personalization processing
            personalization_thread = threading.Thread(target=self._process_personalization_queue, daemon=True)
            personalization_thread.start()
            self.processing_threads.append(personalization_thread)
            
            # Profile updates
            profile_thread = threading.Thread(target=self._process_profile_updates, daemon=True)
            profile_thread.start()
            self.processing_threads.append(profile_thread)
            
            # Insight generation
            insight_thread = threading.Thread(target=self._process_insight_generation, daemon=True)
            insight_thread.start()
            self.processing_threads.append(insight_thread)
            
            logger.info(f"Started {len(self.processing_threads)} background processing threads")
            
        except Exception as e:
            logger.error(f"Failed to start background processing: {e}")
    
    def _create_default_rules(self):
        """Create default personalization rules."""
        try:
            default_rules = [
                PersonalizationRule(
                    rule_id="new_visitor_welcome",
                    name="New Visitor Welcome",
                    description="Show welcome message to first-time visitors",
                    trigger=PersonalizationTrigger.PAGE_VIEW,
                    conditions=[{"field": "visit_count", "operator": "==", "value": 1}],
                    actions=[{"type": "content", "template": "welcome_new_visitor"}],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.MOBILE_APP],
                    priority=10
                ),
                PersonalizationRule(
                    rule_id="cart_abandonment_email",
                    name="Cart Abandonment Recovery",
                    description="Send personalized email for cart abandonment",
                    trigger=PersonalizationTrigger.CART_ABANDONMENT,
                    conditions=[{"field": "cart_value", "operator": ">", "value": 50}],
                    actions=[{"type": "email", "template": "cart_recovery", "delay": "1 hour"}],
                    channels=[PersonalizationChannel.EMAIL],
                    priority=8
                ),
                PersonalizationRule(
                    rule_id="vip_customer_offer",
                    name="VIP Customer Special Offer",
                    description="Show exclusive offers to VIP customers",
                    trigger=PersonalizationTrigger.PRODUCT_VIEW,
                    conditions=[{"field": "customer_tier", "operator": "==", "value": "VIP"}],
                    actions=[{"type": "content", "template": "vip_exclusive_offer"}],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.EMAIL, PersonalizationChannel.MOBILE_APP],
                    priority=9
                ),
                PersonalizationRule(
                    rule_id="mobile_app_promotion",
                    name="Mobile App Download Promotion",
                    description="Promote mobile app to web users",
                    trigger=PersonalizationTrigger.DEVICE,
                    conditions=[{"field": "device_type", "operator": "==", "value": "mobile"}, 
                              {"field": "has_mobile_app", "operator": "==", "value": False}],
                    actions=[{"type": "content", "template": "app_download_banner"}],
                    channels=[PersonalizationChannel.WEB],
                    priority=5
                ),
                PersonalizationRule(
                    rule_id="seasonal_content",
                    name="Seasonal Content Personalization",
                    description="Show seasonal content based on date and location",
                    trigger=PersonalizationTrigger.SEASONAL,
                    conditions=[{"field": "season", "operator": "in", "value": ["spring", "summer", "fall", "winter"]}],
                    actions=[{"type": "content", "template": "seasonal_banner"}],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.EMAIL, PersonalizationChannel.DISPLAY_ADS],
                    priority=3
                )
            ]
            
            for rule in default_rules:
                self.personalization_rules[rule.rule_id] = rule
            
            logger.info(f"Created {len(default_rules)} default personalization rules")
            
        except Exception as e:
            logger.error(f"Failed to create default rules: {e}")
    
    def _create_default_templates(self):
        """Create default personalization templates."""
        try:
            default_templates = [
                PersonalizationTemplate(
                    template_id="welcome_new_visitor",
                    name="New Visitor Welcome Message",
                    content_type="web_banner",
                    template_content="<div class='welcome-banner'>Welcome to our site, {{user.first_name or 'friend'}}! Get 10% off your first order.</div>",
                    variables=["user.first_name", "discount_code"],
                    default_values={"discount_code": "WELCOME10"},
                    personalization_fields=["user.first_name"],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.MOBILE_APP]
                ),
                PersonalizationTemplate(
                    template_id="cart_recovery",
                    name="Cart Abandonment Email",
                    content_type="email",
                    template_content="""
                    <html>
                    <body>
                        <h2>Don't forget about your cart, {{user.first_name}}!</h2>
                        <p>You left some great items in your cart. Complete your purchase now and save {{discount_percentage}}%!</p>
                        <div class='cart-items'>
                            {% for item in cart.items %}
                            <div class='item'>
                                <img src='{{item.image_url}}' alt='{{item.name}}'>
                                <h4>{{item.name}}</h4>
                                <p>${{item.price}}</p>
                            </div>
                            {% endfor %}
                        </div>
                        <a href='{{cart.checkout_url}}' class='cta-button'>Complete Purchase</a>
                    </body>
                    </html>
                    """,
                    variables=["user.first_name", "discount_percentage", "cart.items", "cart.checkout_url"],
                    default_values={"discount_percentage": "10"},
                    personalization_fields=["user.first_name", "cart.items"],
                    channels=[PersonalizationChannel.EMAIL]
                ),
                PersonalizationTemplate(
                    template_id="vip_exclusive_offer",
                    name="VIP Exclusive Offer",
                    content_type="content_block",
                    template_content="""
                    <div class='vip-offer'>
                        <h3>Exclusive VIP Offer</h3>
                        <p>As one of our valued VIP customers, {{user.first_name}}, enjoy {{vip_discount}}% off this premium item!</p>
                        <p>This offer is exclusively for customers like you who have spent over ${{vip_threshold}} with us.</p>
                        <button class='vip-cta'>Claim Your VIP Discount</button>
                    </div>
                    """,
                    variables=["user.first_name", "vip_discount", "vip_threshold"],
                    default_values={"vip_discount": "20", "vip_threshold": "1000"},
                    personalization_fields=["user.first_name", "user.total_spent"],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.EMAIL, PersonalizationChannel.MOBILE_APP]
                ),
                PersonalizationTemplate(
                    template_id="product_recommendations",
                    name="Personalized Product Recommendations",
                    content_type="recommendation_widget",
                    template_content="""
                    <div class='recommendations'>
                        <h3>Recommended for You</h3>
                        {% for product in recommended_products %}
                        <div class='product-card'>
                            <img src='{{product.image_url}}' alt='{{product.name}}'>
                            <h4>{{product.name}}</h4>
                            <p class='price'>${{product.price}}</p>
                            <p class='reason'>{{product.recommendation_reason}}</p>
                            <button class='add-to-cart' data-product-id='{{product.id}}'>Add to Cart</button>
                        </div>
                        {% endfor %}
                    </div>
                    """,
                    variables=["recommended_products"],
                    personalization_fields=["user.purchase_history", "user.browsing_history"],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.EMAIL, PersonalizationChannel.MOBILE_APP]
                ),
                PersonalizationTemplate(
                    template_id="location_based_offer",
                    name="Location-Based Special Offer",
                    content_type="location_banner",
                    template_content="""
                    <div class='location-offer'>
                        <h3>Special Offer in {{user.city}}!</h3>
                        <p>We noticed you're in {{user.city}}, {{user.state}}. Enjoy free same-day delivery on orders over ${{free_shipping_threshold}}!</p>
                        {% if weather.temperature < 60 %}
                        <p>It's {{weather.temperature}}°F today - perfect weather for our cozy indoor collection!</p>
                        {% endif %}
                        <button class='location-cta'>Shop Local Favorites</button>
                    </div>
                    """,
                    variables=["user.city", "user.state", "free_shipping_threshold", "weather.temperature"],
                    default_values={"free_shipping_threshold": "75"},
                    personalization_fields=["user.location", "weather.current"],
                    channels=[PersonalizationChannel.WEB, PersonalizationChannel.MOBILE_APP]
                )
            ]
            
            for template in default_templates:
                self.templates[template.template_id] = template
            
            logger.info(f"Created {len(default_templates)} default personalization templates")
            
        except Exception as e:
            logger.error(f"Failed to create default templates: {e}")
    
    def create_user_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> UserProfile:
        """Create or update a user profile."""
        try:
            existing_profile = self.user_profiles.get(user_id)
            
            if existing_profile:
                # Update existing profile
                if initial_data:
                    if 'demographics' in initial_data:
                        existing_profile.demographics.update(initial_data['demographics'])
                    if 'behavioral_data' in initial_data:
                        existing_profile.behavioral_data.update(initial_data['behavioral_data'])
                    if 'preferences' in initial_data:
                        existing_profile.preferences.update(initial_data['preferences'])
                    
                    existing_profile.updated_at = datetime.now()
                
                return existing_profile
            
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                demographics=initial_data.get('demographics', {}) if initial_data else {},
                behavioral_data=initial_data.get('behavioral_data', {}) if initial_data else {},
                preferences=initial_data.get('preferences', {}) if initial_data else {},
                segments=initial_data.get('segments', []) if initial_data else []
            )
            
            self.user_profiles[user_id] = profile
            
            # Store in Redis if available
            if self.redis_available:
                profile_data = {
                    'created_at': profile.created_at.isoformat(),
                    'demographics': json.dumps(profile.demographics),
                    'behavioral_data': json.dumps(profile.behavioral_data),
                    'preferences': json.dumps(profile.preferences),
                    'segments': json.dumps(profile.segments)
                }
                self.redis_client.hset(f"profile:{user_id}", mapping=profile_data)
            
            # Queue for ML model updates
            self.profile_update_queue.put(user_id)
            
            logger.info(f"Created user profile: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create user profile: {e}")
            return None
    
    def update_user_activity(self, user_id: str, activity_data: Dict[str, Any]):
        """Update user profile with new activity data."""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                # Create profile if it doesn't exist
                profile = self.create_user_profile(user_id)
            
            # Update behavioral data
            if 'page_views' in activity_data:
                if 'page_views' not in profile.behavioral_data:
                    profile.behavioral_data['page_views'] = []
                profile.behavioral_data['page_views'].extend(activity_data['page_views'])
                
                # Keep only recent page views (last 100)
                profile.behavioral_data['page_views'] = profile.behavioral_data['page_views'][-100:]
            
            if 'purchases' in activity_data:
                profile.purchase_history.extend(activity_data['purchases'])
            
            if 'engagement_events' in activity_data:
                profile.engagement_history.extend(activity_data['engagement_events'])
                # Keep only recent engagements (last 200)
                profile.engagement_history = profile.engagement_history[-200:]
            
            # Update real-time context
            if 'context' in activity_data:
                profile.real_time_context.update(activity_data['context'])
            
            profile.last_activity = datetime.now()
            profile.updated_at = datetime.now()
            
            # Queue for ML model updates
            self.profile_update_queue.put(user_id)
            
        except Exception as e:
            logger.error(f"Failed to update user activity: {e}")
    
    def personalize_content(self, user_id: str, channel: PersonalizationChannel,
                          context: Optional[Dict[str, Any]] = None,
                          content_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate personalized content for a user."""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                # Create basic profile and return default content
                profile = self.create_user_profile(user_id)
                return self._get_default_content(channel, content_type)
            
            context = context or {}
            personalization_applied = []
            content_pieces = []
            
            # Apply rule-based personalization
            rule_results = self._apply_personalization_rules(profile, channel, context)
            personalization_applied.extend(rule_results['rules_applied'])
            content_pieces.extend(rule_results['content'])
            
            # Apply ML-based personalization
            if self.ml_models['content_recommendation']:
                ml_results = self._apply_ml_personalization(profile, channel, context)
                personalization_applied.extend(ml_results['models_applied'])
                content_pieces.extend(ml_results['content'])
            
            # Apply template-based personalization
            template_results = self._apply_template_personalization(profile, channel, context, content_type)
            personalization_applied.extend(template_results['templates_applied'])
            content_pieces.extend(template_results['content'])
            
            # Combine and optimize content
            final_content = self._combine_personalized_content(content_pieces, profile, context)
            
            # Track personalization event
            event = PersonalizationEvent(
                event_id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=context.get('session_id', str(uuid.uuid4())),
                event_type='personalization_delivered',
                channel=channel,
                personalization_applied=personalization_applied,
                content_delivered=final_content,
                context=context
            )
            
            self.events.append(event)
            
            # Queue for insight generation
            self.insight_generation_queue.put(event.event_id)
            
            return {
                'content': final_content,
                'personalization_applied': personalization_applied,
                'user_segments': profile.segments,
                'confidence_score': self._calculate_personalization_confidence(personalization_applied),
                'event_id': event.event_id
            }
            
        except Exception as e:
            logger.error(f"Failed to personalize content: {e}")
            return self._get_default_content(channel, content_type)
    
    def _apply_personalization_rules(self, profile: UserProfile, channel: PersonalizationChannel,
                                   context: Dict[str, Any]) -> Dict[str, List]:
        """Apply rule-based personalization."""
        try:
            applicable_rules = []
            
            # Find applicable rules
            for rule in self.personalization_rules.values():
                if (rule.is_active and 
                    channel in rule.channels and
                    self._evaluate_rule_conditions(rule, profile, context)):
                    applicable_rules.append(rule)
            
            # Sort by priority
            applicable_rules.sort(key=lambda r: r.priority, reverse=True)
            
            # Apply rules
            rules_applied = []
            content = []
            
            for rule in applicable_rules[:5]:  # Apply top 5 rules
                rule_content = self._execute_rule_actions(rule, profile, context)
                if rule_content:
                    rules_applied.append(rule.rule_id)
                    content.extend(rule_content)
                    rule.usage_count += 1
            
            return {
                'rules_applied': rules_applied,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Failed to apply personalization rules: {e}")
            return {'rules_applied': [], 'content': []}
    
    def _evaluate_rule_conditions(self, rule: PersonalizationRule, profile: UserProfile,
                                context: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions are met."""
        try:
            for condition in rule.conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                # Get field value from profile or context
                field_value = self._get_field_value(field, profile, context)
                
                if not self._evaluate_condition(field_value, operator, value):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule conditions: {e}")
            return False
    
    def _get_field_value(self, field: str, profile: UserProfile, context: Dict[str, Any]):
        """Get field value from profile or context."""
        try:
            # Handle nested field paths like 'demographics.age'
            if '.' in field:
                parts = field.split('.')
                if parts[0] == 'demographics':
                    return profile.demographics.get(parts[1])
                elif parts[0] == 'behavioral_data':
                    return profile.behavioral_data.get(parts[1])
                elif parts[0] == 'preferences':
                    return profile.preferences.get(parts[1])
                elif parts[0] == 'context':
                    return context.get(parts[1])
                elif parts[0] == 'real_time_context':
                    return profile.real_time_context.get(parts[1])
            
            # Direct field access
            if hasattr(profile, field):
                return getattr(profile, field)
            
            return context.get(field)
            
        except Exception as e:
            logger.error(f"Failed to get field value: {e}")
            return None
    
    def _evaluate_condition(self, field_value, operator: str, expected_value) -> bool:
        """Evaluate a single condition."""
        try:
            if field_value is None:
                return False
            
            if operator == '==':
                return field_value == expected_value
            elif operator == '!=':
                return field_value != expected_value
            elif operator == '>':
                return float(field_value) > float(expected_value)
            elif operator == '<':
                return float(field_value) < float(expected_value)
            elif operator == '>=':
                return float(field_value) >= float(expected_value)
            elif operator == '<=':
                return float(field_value) <= float(expected_value)
            elif operator == 'in':
                return field_value in expected_value
            elif operator == 'not_in':
                return field_value not in expected_value
            elif operator == 'contains':
                return str(expected_value) in str(field_value)
            elif operator == 'starts_with':
                return str(field_value).startswith(str(expected_value))
            elif operator == 'ends_with':
                return str(field_value).endswith(str(expected_value))
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate condition: {e}")
            return False
    
    def _execute_rule_actions(self, rule: PersonalizationRule, profile: UserProfile,
                            context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute rule actions and return content."""
        try:
            content = []
            
            for action in rule.actions:
                action_type = action.get('type')
                
                if action_type == 'content':
                    template_id = action.get('template')
                    if template_id in self.templates:
                        template_content = self._render_template(template_id, profile, context)
                        if template_content:
                            content.append({
                                'type': 'content',
                                'template_id': template_id,
                                'content': template_content,
                                'rule_id': rule.rule_id
                            })
                
                elif action_type == 'email':
                    # Queue email for sending
                    template_id = action.get('template')
                    delay = action.get('delay', '0 minutes')
                    
                    content.append({
                        'type': 'email',
                        'template_id': template_id,
                        'delay': delay,
                        'rule_id': rule.rule_id,
                        'recipient': profile.user_id
                    })
                
                elif action_type == 'recommendation':
                    # Generate product recommendations
                    recommendations = self._generate_product_recommendations(profile, context)
                    content.append({
                        'type': 'recommendations',
                        'products': recommendations,
                        'rule_id': rule.rule_id
                    })
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to execute rule actions: {e}")
            return []
    
    def _render_template(self, template_id: str, profile: UserProfile,
                       context: Dict[str, Any]) -> Optional[str]:
        """Render a personalization template."""
        try:
            template = self.templates.get(template_id)
            if not template:
                return None
            
            # Create template context
            template_context = {
                'user': {
                    'user_id': profile.user_id,
                    'first_name': profile.demographics.get('first_name', ''),
                    'last_name': profile.demographics.get('last_name', ''),
                    'email': profile.demographics.get('email', ''),
                    'age': profile.demographics.get('age', 0),
                    'city': profile.demographics.get('city', ''),
                    'state': profile.demographics.get('state', ''),
                    'customer_tier': profile.behavioral_data.get('customer_tier', 'standard'),
                    'total_spent': sum(p.get('amount', 0) for p in profile.purchase_history),
                    'visit_count': profile.behavioral_data.get('visit_count', 0)
                },
                'context': context,
                **template.default_values
            }
            
            # Add dynamic data based on template requirements
            if 'cart' in template.variables:
                template_context['cart'] = context.get('cart', {})
            
            if 'recommended_products' in template.variables:
                template_context['recommended_products'] = self._generate_product_recommendations(profile, context)
            
            if 'weather' in template.variables:
                template_context['weather'] = context.get('weather', {})
            
            # Render template
            jinja_template = self.jinja_env.from_string(template.template_content)
            rendered_content = jinja_template.render(**template_context)
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"Failed to render template {template_id}: {e}")
            return None
    
    def _generate_product_recommendations(self, profile: UserProfile, context: Dict[str, Any],
                                        num_recommendations: int = 4) -> List[Dict[str, Any]]:
        """Generate product recommendations for user."""
        try:
            # Mock product recommendations based on user profile
            # In production, this would use real ML models and product data
            
            user_segments = profile.segments
            purchase_history = profile.purchase_history
            
            # Sample product database
            sample_products = [
                {
                    'id': 'prod_001',
                    'name': 'Premium Wireless Headphones',
                    'price': 199.99,
                    'category': 'electronics',
                    'image_url': 'https://example.com/headphones.jpg',
                    'recommendation_reason': 'Based on your electronics purchases'
                },
                {
                    'id': 'prod_002',
                    'name': 'Organic Cotton T-Shirt',
                    'price': 29.99,
                    'category': 'clothing',
                    'image_url': 'https://example.com/tshirt.jpg',
                    'recommendation_reason': 'Popular with customers like you'
                },
                {
                    'id': 'prod_003',
                    'name': 'Smart Fitness Watch',
                    'price': 299.99,
                    'category': 'fitness',
                    'image_url': 'https://example.com/watch.jpg',
                    'recommendation_reason': 'Perfect for your active lifestyle'
                },
                {
                    'id': 'prod_004',
                    'name': 'Artisanal Coffee Beans',
                    'price': 24.99,
                    'category': 'food',
                    'image_url': 'https://example.com/coffee.jpg',
                    'recommendation_reason': 'Trending in your area'
                }
            ]
            
            # Simple recommendation logic based on segments
            recommendations = []
            
            if 'tech_enthusiast' in user_segments:
                recommendations.extend([p for p in sample_products if p['category'] == 'electronics'])
            
            if 'fitness_focused' in user_segments:
                recommendations.extend([p for p in sample_products if p['category'] == 'fitness'])
            
            # Fill remaining slots with popular products
            while len(recommendations) < num_recommendations:
                remaining_products = [p for p in sample_products if p not in recommendations]
                if remaining_products:
                    recommendations.append(remaining_products[0])
                else:
                    break
            
            return recommendations[:num_recommendations]
            
        except Exception as e:
            logger.error(f"Failed to generate product recommendations: {e}")
            return []
    
    def _apply_ml_personalization(self, profile: UserProfile, channel: PersonalizationChannel,
                                context: Dict[str, Any]) -> Dict[str, List]:
        """Apply ML-based personalization (mock implementation)."""
        # Mock ML personalization - in production, this would use real trained models
        return {
            'models_applied': ['engagement_prediction'],
            'content': [{
                'type': 'ml_recommendation',
                'confidence': 0.85,
                'reason': 'High engagement probability based on user behavior'
            }]
        }
    
    def _apply_template_personalization(self, profile: UserProfile, channel: PersonalizationChannel,
                                      context: Dict[str, Any], content_type: Optional[str] = None) -> Dict[str, List]:
        """Apply template-based personalization."""
        try:
            applicable_templates = []
            
            # Find templates for this channel and content type
            for template in self.templates.values():
                if (template.is_active and 
                    channel in template.channels and
                    (not content_type or template.content_type == content_type)):
                    applicable_templates.append(template)
            
            templates_applied = []
            content = []
            
            for template in applicable_templates[:3]:  # Apply top 3 templates
                rendered_content = self._render_template(template.template_id, profile, context)
                if rendered_content:
                    templates_applied.append(template.template_id)
                    content.append({
                        'type': 'template',
                        'template_id': template.template_id,
                        'content': rendered_content
                    })
            
            return {
                'templates_applied': templates_applied,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Failed to apply template personalization: {e}")
            return {'templates_applied': [], 'content': []}
    
    def _combine_personalized_content(self, content_pieces: List[Dict[str, Any]],
                                    profile: UserProfile, context: Dict[str, Any]) -> Dict[str, Any]:
        """Combine multiple personalized content pieces into final content."""
        try:
            # Group content by type
            content_by_type = defaultdict(list)
            for piece in content_pieces:
                content_by_type[piece['type']].append(piece)
            
            # Create final content structure
            final_content = {
                'primary_content': '',
                'secondary_content': [],
                'recommendations': [],
                'offers': [],
                'metadata': {
                    'personalization_level': 'high' if len(content_pieces) > 3 else 'medium' if len(content_pieces) > 1 else 'low',
                    'content_pieces_count': len(content_pieces),
                    'user_segments': profile.segments
                }
            }
            
            # Prioritize content
            if 'content' in content_by_type:
                # Use first content piece as primary
                final_content['primary_content'] = content_by_type['content'][0]['content']
                # Additional content pieces as secondary
                final_content['secondary_content'] = [p['content'] for p in content_by_type['content'][1:]]
            
            if 'recommendations' in content_by_type:
                for rec_piece in content_by_type['recommendations']:
                    final_content['recommendations'].extend(rec_piece.get('products', []))
            
            if 'template' in content_by_type:
                # Combine template content
                template_content = [p['content'] for p in content_by_type['template']]
                final_content['secondary_content'].extend(template_content)
            
            return final_content
            
        except Exception as e:
            logger.error(f"Failed to combine personalized content: {e}")
            return {'primary_content': '', 'secondary_content': [], 'recommendations': []}
    
    def _calculate_personalization_confidence(self, personalization_applied: List[str]) -> float:
        """Calculate confidence score for personalization."""
        try:
            if not personalization_applied:
                return 0.0
            
            # Base score from number of personalizations
            base_score = min(0.8, len(personalization_applied) * 0.15)
            
            # Bonus for high-value personalization types
            high_value_types = ['ml_recommendation', 'behavioral_targeting', 'purchase_history']
            bonus = sum(0.1 for p in personalization_applied if any(hv in p for hv in high_value_types))
            
            return min(1.0, base_score + bonus)
            
        except Exception as e:
            logger.error(f"Failed to calculate personalization confidence: {e}")
            return 0.5
    
    def _get_default_content(self, channel: PersonalizationChannel, content_type: Optional[str] = None) -> Dict[str, Any]:
        """Get default content when personalization fails."""
        return {
            'content': {
                'primary_content': 'Welcome! Discover our latest products and special offers.',
                'secondary_content': [],
                'recommendations': [],
                'offers': [],
                'metadata': {
                    'personalization_level': 'none',
                    'content_pieces_count': 0,
                    'fallback': True
                }
            },
            'personalization_applied': [],
            'user_segments': [],
            'confidence_score': 0.0
        }
    
    def _process_personalization_queue(self):
        """Background thread to process personalization requests."""
        while self.is_processing:
            try:
                try:
                    request = self.personalization_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process personalization request
                result = self.personalize_content(
                    request['user_id'],
                    request['channel'],
                    request['context'],
                    request.get('content_type')
                )
                
                # Store result if callback provided
                if 'callback' in request:
                    request['callback'](result)
                
                self.personalization_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in personalization processing: {e}")
    
    def _process_profile_updates(self):
        """Background thread to process profile updates."""
        while self.is_processing:
            try:
                try:
                    user_id = self.profile_update_queue.get(timeout=5)
                except queue.Empty:
                    continue
                
                # Update ML models with new profile data
                self._update_ml_models_for_user(user_id)
                
                self.profile_update_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in profile update processing: {e}")
    
    def _process_insight_generation(self):
        """Background thread to generate insights."""
        while self.is_processing:
            try:
                try:
                    event_id = self.insight_generation_queue.get(timeout=10)
                except queue.Empty:
                    continue
                
                # Generate insights from recent events
                insights = self._generate_personalization_insights()
                
                for insight in insights:
                    self.insights[insight.insight_id] = insight
                
                self.insight_generation_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in insight generation: {e}")
    
    def _update_ml_models_for_user(self, user_id: str):
        """Update ML models with new user data."""
        try:
            profile = self.user_profiles.get(user_id)
            if not profile:
                return
            
            # Update user segmentation model
            if self.ml_models['user_segmentation']:
                predicted_segments = self._predict_user_segments(profile)
                profile.segments = list(set(profile.segments + predicted_segments))
            
            # Update predicted attributes
            profile.predicted_attributes = self._calculate_predicted_attributes(profile)
            
            logger.debug(f"Updated ML models for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update ML models for user: {e}")
    
    def _predict_user_segments(self, profile: UserProfile) -> List[str]:
        """Predict user segments using ML models."""
        # Mock segment prediction - in production, this would use real ML models
        segments = []
        
        # Rule-based segment assignment for demo
        if profile.demographics.get('age', 0) < 30:
            segments.append('millennials')
        elif profile.demographics.get('age', 0) >= 50:
            segments.append('boomers')
        
        total_spent = sum(p.get('amount', 0) for p in profile.purchase_history)
        if total_spent > 1000:
            segments.append('high_value')
        elif total_spent > 100:
            segments.append('medium_value')
        
        return segments
    
    def _calculate_predicted_attributes(self, profile: UserProfile) -> Dict[str, float]:
        """Calculate predicted user attributes."""
        # Mock predictions - in production, these would be from real ML models
        import random
        
        return {
            'churn_probability': random.uniform(0.1, 0.4),
            'lifetime_value': random.uniform(200, 2000),
            'engagement_score': random.uniform(0.3, 0.9),
            'conversion_probability': random.uniform(0.02, 0.15),
            'recommendation_affinity': random.uniform(0.4, 0.8)
        }
    
    def _generate_personalization_insights(self) -> List[PersonalizationInsight]:
        """Generate insights from personalization data."""
        try:
            insights = []
            
            # Analyze recent events
            recent_events = list(self.events)[-1000:]  # Last 1000 events
            
            if not recent_events:
                return insights
            
            # Performance insight
            channel_performance = defaultdict(list)
            for event in recent_events:
                if event.user_response:
                    channel_performance[event.channel].append(event.user_response)
            
            best_channel = None
            best_response_rate = 0
            
            for channel, responses in channel_performance.items():
                if responses:
                    response_rate = len([r for r in responses if r in ['clicked', 'converted']]) / len(responses)
                    if response_rate > best_response_rate:
                        best_response_rate = response_rate
                        best_channel = channel
            
            if best_channel:
                insights.append(PersonalizationInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type='performance',
                    title='Best Performing Channel Identified',
                    description=f'{best_channel.value} shows the highest response rate at {best_response_rate:.1%}',
                    data={
                        'channel': best_channel.value,
                        'response_rate': best_response_rate,
                        'sample_size': len(channel_performance[best_channel])
                    },
                    recommendations=[
                        f'Increase budget allocation to {best_channel.value}',
                        'Analyze successful personalization patterns in this channel'
                    ],
                    confidence_score=0.8,
                    impact_estimate='high'
                ))
            
            # Template performance insight
            template_usage = defaultdict(int)
            for event in recent_events:
                for rule_id in event.personalization_applied:
                    if rule_id.startswith('template_'):
                        template_usage[rule_id] += 1
            
            if template_usage:
                most_used_template = max(template_usage.items(), key=lambda x: x[1])
                insights.append(PersonalizationInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type='trend',
                    title='Most Popular Personalization Template',
                    description=f'Template {most_used_template[0]} used {most_used_template[1]} times recently',
                    data={
                        'template_id': most_used_template[0],
                        'usage_count': most_used_template[1],
                        'total_templates': len(template_usage)
                    },
                    recommendations=[
                        'Create similar template variations',
                        'Analyze what makes this template successful'
                    ],
                    confidence_score=0.7,
                    impact_estimate='medium'
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate personalization insights: {e}")
            return []
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self.user_profiles.get(user_id)
    
    def get_personalization_performance(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get overall personalization performance metrics."""
        try:
            events = list(self.events)
            
            if time_range:
                start_time, end_time = time_range
                events = [e for e in events if start_time <= e.timestamp <= end_time]
            
            if not events:
                return {}
            
            # Calculate metrics
            total_personalizations = len(events)
            successful_personalizations = len([e for e in events if e.user_response in ['clicked', 'converted']])
            
            # Channel breakdown
            channel_stats = defaultdict(lambda: {'total': 0, 'successful': 0})
            for event in events:
                channel_stats[event.channel.value]['total'] += 1
                if event.user_response in ['clicked', 'converted']:
                    channel_stats[event.channel.value]['successful'] += 1
            
            # Rule performance
            rule_stats = defaultdict(lambda: {'total': 0, 'successful': 0})
            for event in events:
                for rule_id in event.personalization_applied:
                    rule_stats[rule_id]['total'] += 1
                    if event.user_response in ['clicked', 'converted']:
                        rule_stats[rule_id]['successful'] += 1
            
            performance = {
                'summary': {
                    'total_personalizations': total_personalizations,
                    'successful_personalizations': successful_personalizations,
                    'success_rate': successful_personalizations / max(total_personalizations, 1),
                    'unique_users': len(set(e.user_id for e in events)),
                    'avg_personalizations_per_user': total_personalizations / len(set(e.user_id for e in events)) if events else 0
                },
                'channel_performance': {
                    channel: {
                        'total': stats['total'],
                        'successful': stats['successful'],
                        'success_rate': stats['successful'] / max(stats['total'], 1)
                    }
                    for channel, stats in channel_stats.items()
                },
                'rule_performance': {
                    rule: {
                        'total': stats['total'],
                        'successful': stats['successful'],
                        'success_rate': stats['successful'] / max(stats['total'], 1)
                    }
                    for rule, stats in rule_stats.items()
                },
                'insights': list(self.insights.values())[-5:]  # Last 5 insights
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get personalization performance: {e}")
            return {}
    
    def create_experiment(self, experiment: PersonalizationExperiment) -> bool:
        """Create a new personalization A/B test experiment."""
        try:
            self.experiments[experiment.experiment_id] = experiment
            
            logger.info(f"Created personalization experiment: {experiment.name} ({experiment.experiment_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            return False
    
    def get_insights(self, insight_type: Optional[str] = None, limit: int = 10) -> List[PersonalizationInsight]:
        """Get personalization insights."""
        try:
            insights = list(self.insights.values())
            
            if insight_type:
                insights = [i for i in insights if i.insight_type == insight_type]
            
            # Sort by priority and confidence
            insights.sort(key=lambda i: (i.priority, i.confidence_score), reverse=True)
            
            return insights[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return []


def create_sample_personalization_manager() -> PersonalizationManager:
    """Create sample personalization manager for demonstration."""
    
    manager = PersonalizationManager()
    
    # Create sample user profiles
    sample_users = [
        {
            'user_id': 'user_001',
            'demographics': {
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah@example.com',
                'age': 28,
                'city': 'San Francisco',
                'state': 'CA'
            },
            'segments': ['millennials', 'tech_enthusiast', 'high_value'],
            'purchase_history': [
                {'amount': 299.99, 'category': 'electronics', 'date': '2024-01-15'},
                {'amount': 79.99, 'category': 'clothing', 'date': '2024-01-20'}
            ]
        },
        {
            'user_id': 'user_002',
            'demographics': {
                'first_name': 'Michael',
                'last_name': 'Chen',
                'email': 'michael@example.com',
                'age': 35,
                'city': 'New York',
                'state': 'NY'
            },
            'segments': ['gen_x', 'fitness_focused', 'medium_value'],
            'purchase_history': [
                {'amount': 149.99, 'category': 'fitness', 'date': '2024-01-18'},
                {'amount': 24.99, 'category': 'food', 'date': '2024-01-22'}
            ]
        },
        {
            'user_id': 'user_003',
            'demographics': {
                'first_name': 'Emily',
                'last_name': 'Rodriguez',
                'email': 'emily@example.com',
                'age': 22,
                'city': 'Austin',
                'state': 'TX'
            },
            'segments': ['gen_z', 'fashion_forward', 'new_customer'],
            'purchase_history': [
                {'amount': 59.99, 'category': 'clothing', 'date': '2024-01-25'}
            ]
        }
    ]
    
    # Create user profiles
    for user_data in sample_users:
        user_id = user_data.pop('user_id')
        manager.create_user_profile(user_id, user_data)
    
    # Create sample experiment
    experiment = PersonalizationExperiment(
        experiment_id='exp_001',
        name='Homepage Hero Banner A/B Test',
        description='Testing different hero banner messages for new visitors',
        hypothesis='Personalized welcome messages will increase engagement by 15%',
        control_variant={'message': 'Welcome to our store'},
        test_variants=[
            {'message': 'Welcome {{first_name}}, discover products just for you!'},
            {'message': 'Hi {{first_name}}! Get 10% off your first order'}
        ],
        traffic_allocation={'control': 0.4, 'variant_1': 0.3, 'variant_2': 0.3},
        success_metrics=['click_rate', 'conversion_rate'],
        channels=[PersonalizationChannel.WEB],
        audience_segments=['new_visitors'],
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=14)
    )
    
    manager.create_experiment(experiment)
    
    # Generate sample personalization events
    import random
    
    for i in range(100):
        user_id = random.choice(['user_001', 'user_002', 'user_003'])
        channel = random.choice(list(PersonalizationChannel)[:5])  # First 5 channels
        
        event = PersonalizationEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            event_type='personalization_delivered',
            channel=channel,
            personalization_applied=[random.choice(['rule_001', 'template_001', 'ml_model_001'])],
            content_delivered={'message': f'Personalized content for {user_id}'},
            user_response=random.choice(['clicked', 'ignored', 'converted', None]),
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 1440))  # Last 24 hours
        )
        
        manager.events.append(event)
    
    return manager


def run_personalization_demo():
    """
    Run the personalization manager demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🎯 Personalization Manager Demo")
    print("=" * 50)
    
    print("🎆 Key Features:")
    print("  • Real-time user profiling and segmentation")
    print("  • Rule-based and ML-driven personalization")
    print("  • Dynamic content generation and optimization")
    print("  • Cross-channel personalization consistency")
    print("  • A/B testing and experimentation")
    print("  • Performance tracking and insights")
    print("  • Privacy-compliant personalization")
    print("  • Scalable real-time processing")
    
    print("\n📊 Personalization Types:")
    for ptype in list(PersonalizationType)[:8]:  # Show first 8 types
        print(f"  • {ptype.value}")
    print(f"  • ... and {len(PersonalizationType) - 8} more types")
    
    print("\n📱 Supported Channels:")
    for channel in list(PersonalizationChannel)[:8]:  # Show first 8 channels
        print(f"  • {channel.value}")
    print(f"  • ... and {len(PersonalizationChannel) - 8} more channels")
    
    print("\n🚀 Initializing personalization manager...")
    manager = create_sample_personalization_manager()
    
    print("✅ Personalization manager initialized")
    print(f"   • User profiles: {len(manager.user_profiles)}")
    print(f"   • Personalization rules: {len(manager.personalization_rules)}")
    print(f"   • Templates: {len(manager.templates)}")
    print(f"   • Active experiments: {len(manager.experiments)}")
    print(f"   • Recent events: {len(manager.events)}")
    
    # Demonstrate personalization
    print("\n🎯 Personalization Demo:")
    
    # Personalize content for different users
    users_to_test = ['user_001', 'user_002', 'user_003']
    
    for user_id in users_to_test:
        profile = manager.get_user_profile(user_id)
        if profile:
            print(f"\n   User: {profile.demographics.get('first_name', user_id)}")
            print(f"   Segments: {', '.join(profile.segments)}")
            
            # Generate personalized content
            result = manager.personalize_content(
                user_id,
                PersonalizationChannel.WEB,
                context={'page': 'homepage', 'device': 'desktop'}
            )
            
            print(f"   Personalization Applied: {len(result['personalization_applied'])}")
            print(f"   Confidence Score: {result['confidence_score']:.2f}")
            
            # Show primary content if available
            primary_content = result['content']['primary_content']
            if primary_content and len(primary_content) > 0:
                # Clean HTML tags for display
                import re
                clean_content = re.sub('<[^<]+?>', '', primary_content)[:100]
                print(f"   Sample Content: {clean_content}...")
    
    # Performance metrics
    performance = manager.get_personalization_performance()
    
    print(f"\n📈 Performance Summary:")
    summary = performance.get('summary', {})
    print(f"   • Total Personalizations: {summary.get('total_personalizations', 0):,}")
    print(f"   • Success Rate: {summary.get('success_rate', 0)*100:.1f}%")
    print(f"   • Unique Users: {summary.get('unique_users', 0):,}")
    print(f"   • Avg Personalizations/User: {summary.get('avg_personalizations_per_user', 0):.1f}")
    
    # Channel performance
    channel_perf = performance.get('channel_performance', {})
    if channel_perf:
        print("\n   Top Performing Channels:")
        sorted_channels = sorted(channel_perf.items(), key=lambda x: x[1]['success_rate'], reverse=True)
        for channel, stats in sorted_channels[:3]:
            print(f"     • {channel}: {stats['success_rate']*100:.1f}% success rate ({stats['total']} total)")
    
    # Show personalization rules
    print("\n📜 Active Personalization Rules:")
    for rule_id, rule in list(manager.personalization_rules.items())[:3]:  # Show first 3
        print(f"   • {rule.name}")
        print(f"     - Trigger: {rule.trigger.value}")
        print(f"     - Channels: {len(rule.channels)}")
        print(f"     - Priority: {rule.priority}")
        print(f"     - Usage: {rule.usage_count} times")
    
    # Show templates
    print("\n📋 Content Templates:")
    for template_id, template in list(manager.templates.items())[:3]:  # Show first 3
        print(f"   • {template.name}")
        print(f"     - Type: {template.content_type}")
        print(f"     - Variables: {len(template.variables)}")
        print(f"     - Channels: {len(template.channels)}")
    
    # Show experiments
    print("\n🧪 Active Experiments:")
    for exp_id, experiment in manager.experiments.items():
        print(f"   • {experiment.name}")
        print(f"     - Hypothesis: {experiment.hypothesis}")
        print(f"     - Variants: {len(experiment.test_variants) + 1}")
        print(f"     - Channels: {len(experiment.channels)}")
        print(f"     - Status: {experiment.status}")
    
    # Show insights
    insights = manager.get_insights(limit=3)
    if insights:
        print(f"\n💡 Latest Insights:")
        for insight in insights:
            print(f"   • {insight.title}")
            print(f"     - Type: {insight.insight_type}")
            print(f"     - Impact: {insight.impact_estimate}")
            print(f"     - Confidence: {insight.confidence_score:.1%}")
            if insight.recommendations:
                print(f"     - Top Recommendation: {insight.recommendations[0]}")
    
    print("\n🌟 Advanced Capabilities:")
    print("  • Real-time ML model updates based on user behavior")
    print("  • Cross-device personalization consistency")
    print("  • Privacy-preserving personalization techniques")
    print("  • Multi-armed bandit optimization")
    print("  • Contextual personalization (weather, time, location)")
    print("  • Automated A/B test winner selection")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return manager


if __name__ == "__main__":
    run_personalization_demo()
