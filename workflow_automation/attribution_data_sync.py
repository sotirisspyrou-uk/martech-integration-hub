#!/usr/bin/env python3
"""
Attribution Data Sync - MarTech Integration Hub

Advanced multi-touch attribution data synchronization system.
Tracks customer journeys across channels and provides unified attribution insights.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
"""

import json
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

class TouchpointType(Enum):
    IMPRESSION = "impression"
    CLICK = "click"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    WEBSITE_VISIT = "website_visit"
    FORM_SUBMISSION = "form_submission"
    CONTENT_DOWNLOAD = "content_download"
    WEBINAR_ATTENDANCE = "webinar_attendance"
    SOCIAL_ENGAGEMENT = "social_engagement"
    CONVERSION = "conversion"

class AttributionModel(Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"

class Channel(Enum):
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"
    LINKEDIN_ADS = "linkedin_ads"
    EMAIL = "email"
    ORGANIC_SEARCH = "organic_search"
    DIRECT = "direct"
    REFERRAL = "referral"
    SOCIAL_ORGANIC = "social_organic"
    DISPLAY = "display"
    VIDEO = "video"

@dataclass
class Touchpoint:
    touchpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    session_id: str = ""
    touchpoint_type: TouchpointType = TouchpointType.IMPRESSION
    channel: Channel = Channel.DIRECT
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    keyword: Optional[str] = None
    content_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    value: float = 0.0
    conversion_value: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CustomerJourney:
    journey_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    touchpoints: List[Touchpoint] = field(default_factory=list)
    conversion_touchpoints: List[Touchpoint] = field(default_factory=list)
    first_touch: Optional[Touchpoint] = None
    last_touch: Optional[Touchpoint] = None
    journey_start: Optional[datetime] = None
    journey_end: Optional[datetime] = None
    total_touchpoints: int = 0
    total_conversion_value: float = 0.0
    journey_duration_hours: float = 0.0

@dataclass
class AttributionResult:
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    journey_id: str = ""
    attribution_model: AttributionModel = AttributionModel.LINEAR
    channel_attribution: Dict[str, float] = field(default_factory=dict)
    campaign_attribution: Dict[str, float] = field(default_factory=dict)
    touchpoint_attribution: Dict[str, float] = field(default_factory=dict)
    total_attributed_value: float = 0.0
    calculation_timestamp: datetime = field(default_factory=datetime.now)

class AttributionDataSync:
    """
    Advanced multi-touch attribution data synchronization system.
    
    🎯 ENTERPRISE CAPABILITIES:
    - Real-time attribution modeling
    - Cross-channel journey tracking
    - Multiple attribution algorithms
    - Advanced customer journey analytics
    - ROI optimization insights
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.touchpoints: Dict[str, Touchpoint] = {}
        self.customer_journeys: Dict[str, CustomerJourney] = {}
        self.attribution_results: Dict[str, AttributionResult] = {}
        self.channel_configs: Dict[str, Dict[str, Any]] = {}
        self.attribution_stats = {
            'touchpoints_tracked': 0,
            'journeys_analyzed': 0,
            'conversions_attributed': 0,
            'attribution_models_calculated': 0
        }
        self.journey_window_days = 30  # Attribution window
        self._initialize_channel_configs()
    
    def _initialize_channel_configs(self):
        """Initialize channel configuration for attribution."""
        self.channel_configs = {
            'google_ads': {
                'default_value_weight': 1.0,
                'decay_factor': 0.8,
                'attribution_priority': 'high',
                'conversion_types': ['purchase', 'lead', 'signup']
            },
            'facebook_ads': {
                'default_value_weight': 0.9,
                'decay_factor': 0.7,
                'attribution_priority': 'high',
                'conversion_types': ['purchase', 'lead', 'engagement']
            },
            'linkedin_ads': {
                'default_value_weight': 1.1,
                'decay_factor': 0.9,
                'attribution_priority': 'high',
                'conversion_types': ['lead', 'whitepaper_download', 'webinar']
            },
            'email': {
                'default_value_weight': 0.8,
                'decay_factor': 0.6,
                'attribution_priority': 'medium',
                'conversion_types': ['click', 'purchase', 'engagement']
            },
            'organic_search': {
                'default_value_weight': 1.2,
                'decay_factor': 0.9,
                'attribution_priority': 'high',
                'conversion_types': ['visit', 'purchase', 'lead']
            },
            'direct': {
                'default_value_weight': 1.0,
                'decay_factor': 1.0,
                'attribution_priority': 'medium',
                'conversion_types': ['purchase', 'visit']
            }
        }
    
    def add_touchpoint(self, customer_id: str, touchpoint_type: TouchpointType,
                      channel: Channel, **kwargs) -> str:
        """Add a new touchpoint to the attribution system."""
        touchpoint = Touchpoint(
            customer_id=customer_id,
            touchpoint_type=touchpoint_type,
            channel=channel,
            **kwargs
        )
        
        # Enrich touchpoint with channel-specific data
        touchpoint = self._enrich_touchpoint(touchpoint)
        
        self.touchpoints[touchpoint.touchpoint_id] = touchpoint
        self.attribution_stats['touchpoints_tracked'] += 1
        
        # Update or create customer journey
        self._update_customer_journey(touchpoint)
        
        return touchpoint.touchpoint_id
    
    def _enrich_touchpoint(self, touchpoint: Touchpoint) -> Touchpoint:
        """Enrich touchpoint with additional data and context."""
        channel_config = self.channel_configs.get(touchpoint.channel.value, {})
        
        # Set default value weight
        if touchpoint.value == 0.0:
            touchpoint.value = channel_config.get('default_value_weight', 1.0)
        
        # Add metadata
        touchpoint.metadata.update({
            'channel_priority': channel_config.get('attribution_priority', 'medium'),
            'decay_factor': channel_config.get('decay_factor', 0.8),
            'processed_at': datetime.now().isoformat()
        })
        
        # Detect conversion touchpoints
        if touchpoint.touchpoint_type in [TouchpointType.CONVERSION, TouchpointType.FORM_SUBMISSION]:
            touchpoint.conversion_value = touchpoint.value * 100  # Example conversion value
        
        return touchpoint
    
    def _update_customer_journey(self, touchpoint: Touchpoint):
        """Update or create customer journey with new touchpoint."""
        journey = None
        
        # Find existing journey for this customer
        for existing_journey in self.customer_journeys.values():
            if (existing_journey.customer_id == touchpoint.customer_id and
                existing_journey.journey_end and
                (touchpoint.timestamp - existing_journey.journey_end).days <= self.journey_window_days):
                journey = existing_journey
                break
        
        # Create new journey if none found
        if not journey:
            journey = CustomerJourney(
                customer_id=touchpoint.customer_id,
                journey_start=touchpoint.timestamp
            )
            self.customer_journeys[journey.journey_id] = journey
            self.attribution_stats['journeys_analyzed'] += 1
        
        # Add touchpoint to journey
        journey.touchpoints.append(touchpoint)
        journey.total_touchpoints = len(journey.touchpoints)
        journey.journey_end = touchpoint.timestamp
        
        # Update journey metadata
        if not journey.first_touch:
            journey.first_touch = touchpoint
        journey.last_touch = touchpoint
        
        # Track conversions
        if touchpoint.conversion_value > 0:
            journey.conversion_touchpoints.append(touchpoint)
            journey.total_conversion_value += touchpoint.conversion_value
            self.attribution_stats['conversions_attributed'] += 1
        
        # Calculate journey duration
        if journey.journey_start and journey.journey_end:
            duration = journey.journey_end - journey.journey_start
            journey.journey_duration_hours = duration.total_seconds() / 3600
    
    def calculate_attribution(self, journey_id: str, 
                            model: AttributionModel = AttributionModel.LINEAR) -> str:
        """Calculate attribution for a customer journey using specified model."""
        if journey_id not in self.customer_journeys:
            raise ValueError(f"Journey {journey_id} not found")
        
        journey = self.customer_journeys[journey_id]
        
        if not journey.conversion_touchpoints:
            # No conversions to attribute
            return ""
        
        attribution_result = AttributionResult(
            customer_id=journey.customer_id,
            journey_id=journey_id,
            attribution_model=model,
            total_attributed_value=journey.total_conversion_value
        )
        
        # Calculate attribution based on model
        if model == AttributionModel.FIRST_TOUCH:
            attribution_result = self._calculate_first_touch_attribution(journey, attribution_result)
        elif model == AttributionModel.LAST_TOUCH:
            attribution_result = self._calculate_last_touch_attribution(journey, attribution_result)
        elif model == AttributionModel.LINEAR:
            attribution_result = self._calculate_linear_attribution(journey, attribution_result)
        elif model == AttributionModel.TIME_DECAY:
            attribution_result = self._calculate_time_decay_attribution(journey, attribution_result)
        elif model == AttributionModel.POSITION_BASED:
            attribution_result = self._calculate_position_based_attribution(journey, attribution_result)
        elif model == AttributionModel.DATA_DRIVEN:
            attribution_result = self._calculate_data_driven_attribution(journey, attribution_result)
        
        self.attribution_results[attribution_result.result_id] = attribution_result
        self.attribution_stats['attribution_models_calculated'] += 1
        
        return attribution_result.result_id
    
    def _calculate_linear_attribution(self, journey: CustomerJourney, 
                                    result: AttributionResult) -> AttributionResult:
        """Calculate linear attribution (equal weight to all touchpoints)."""
        if not journey.touchpoints:
            return result
        
        touchpoint_count = len(journey.touchpoints)
        value_per_touchpoint = journey.total_conversion_value / touchpoint_count
        
        for touchpoint in journey.touchpoints:
            channel = touchpoint.channel.value
            
            # Channel attribution
            if channel not in result.channel_attribution:
                result.channel_attribution[channel] = 0
            result.channel_attribution[channel] += value_per_touchpoint
            
            # Touchpoint attribution
            result.touchpoint_attribution[touchpoint.touchpoint_id] = value_per_touchpoint
            
            # Campaign attribution
            if touchpoint.campaign_id:
                if touchpoint.campaign_id not in result.campaign_attribution:
                    result.campaign_attribution[touchpoint.campaign_id] = 0
                result.campaign_attribution[touchpoint.campaign_id] += value_per_touchpoint
        
        return result
    
    def _calculate_first_touch_attribution(self, journey: CustomerJourney, 
                                         result: AttributionResult) -> AttributionResult:
        """Calculate first-touch attribution."""
        if not journey.touchpoints:
            return result
        
        first_touchpoint = journey.touchpoints[0]
        channel = first_touchpoint.channel.value
        
        result.channel_attribution[channel] = journey.total_conversion_value
        result.touchpoint_attribution[first_touchpoint.touchpoint_id] = journey.total_conversion_value
        
        if first_touchpoint.campaign_id:
            result.campaign_attribution[first_touchpoint.campaign_id] = journey.total_conversion_value
        
        return result
    
    def _calculate_last_touch_attribution(self, journey: CustomerJourney, 
                                        result: AttributionResult) -> AttributionResult:
        """Calculate last-touch attribution."""
        if not journey.touchpoints:
            return result
        
        last_touchpoint = journey.touchpoints[-1]
        channel = last_touchpoint.channel.value
        
        result.channel_attribution[channel] = journey.total_conversion_value
        result.touchpoint_attribution[last_touchpoint.touchpoint_id] = journey.total_conversion_value
        
        if last_touchpoint.campaign_id:
            result.campaign_attribution[last_touchpoint.campaign_id] = journey.total_conversion_value
        
        return result
    
    def _calculate_time_decay_attribution(self, journey: CustomerJourney, 
                                        result: AttributionResult) -> AttributionResult:
        """Calculate time-decay attribution (more recent touchpoints get more credit)."""
        if not journey.touchpoints or not journey.journey_end:
            return result
        
        # Calculate decay weights
        total_weight = 0
        touchpoint_weights = []
        
        for touchpoint in journey.touchpoints:
            # Calculate days from conversion
            days_from_conversion = (journey.journey_end - touchpoint.timestamp).days
            
            # Apply exponential decay
            decay_factor = touchpoint.metadata.get('decay_factor', 0.8)
            weight = decay_factor ** days_from_conversion
            touchpoint_weights.append(weight)
            total_weight += weight
        
        # Distribute attribution based on weights
        for i, touchpoint in enumerate(journey.touchpoints):
            if total_weight > 0:
                attribution_value = (touchpoint_weights[i] / total_weight) * journey.total_conversion_value
                
                channel = touchpoint.channel.value
                if channel not in result.channel_attribution:
                    result.channel_attribution[channel] = 0
                result.channel_attribution[channel] += attribution_value
                
                result.touchpoint_attribution[touchpoint.touchpoint_id] = attribution_value
                
                if touchpoint.campaign_id:
                    if touchpoint.campaign_id not in result.campaign_attribution:
                        result.campaign_attribution[touchpoint.campaign_id] = 0
                    result.campaign_attribution[touchpoint.campaign_id] += attribution_value
        
        return result
    
    def _calculate_position_based_attribution(self, journey: CustomerJourney, 
                                            result: AttributionResult) -> AttributionResult:
        """Calculate position-based attribution (40% first, 40% last, 20% middle)."""
        if not journey.touchpoints:
            return result
        
        touchpoint_count = len(journey.touchpoints)
        total_value = journey.total_conversion_value
        
        if touchpoint_count == 1:
            # Single touchpoint gets all credit
            touchpoint = journey.touchpoints[0]
            channel = touchpoint.channel.value
            result.channel_attribution[channel] = total_value
            result.touchpoint_attribution[touchpoint.touchpoint_id] = total_value
        else:
            # Position-based model: 40% first, 40% last, 20% distributed among middle
            middle_count = touchpoint_count - 2
            middle_value_per_touchpoint = (total_value * 0.2) / middle_count if middle_count > 0 else 0
            
            for i, touchpoint in enumerate(journey.touchpoints):
                if i == 0:  # First touchpoint
                    value = total_value * 0.4
                elif i == touchpoint_count - 1:  # Last touchpoint
                    value = total_value * 0.4
                else:  # Middle touchpoints
                    value = middle_value_per_touchpoint
                
                channel = touchpoint.channel.value
                if channel not in result.channel_attribution:
                    result.channel_attribution[channel] = 0
                result.channel_attribution[channel] += value
                result.touchpoint_attribution[touchpoint.touchpoint_id] = value
                
                if touchpoint.campaign_id:
                    if touchpoint.campaign_id not in result.campaign_attribution:
                        result.campaign_attribution[touchpoint.campaign_id] = 0
                    result.campaign_attribution[touchpoint.campaign_id] += value
        
        return result
    
    def _calculate_data_driven_attribution(self, journey: CustomerJourney, 
                                         result: AttributionResult) -> AttributionResult:
        """Calculate data-driven attribution using machine learning-like approach."""
        # Simplified data-driven model using channel performance weights
        if not journey.touchpoints:
            return result
        
        # Calculate channel performance scores based on historical data
        channel_scores = defaultdict(float)
        for touchpoint in journey.touchpoints:
            channel = touchpoint.channel.value
            channel_config = self.channel_configs.get(channel, {})
            
            # Base score from configuration
            base_score = channel_config.get('default_value_weight', 1.0)
            
            # Adjust based on touchpoint type
            type_multiplier = {
                TouchpointType.CONVERSION: 2.0,
                TouchpointType.CLICK: 1.5,
                TouchpointType.FORM_SUBMISSION: 1.8,
                TouchpointType.EMAIL_CLICK: 1.3,
                TouchpointType.IMPRESSION: 0.8
            }.get(touchpoint.touchpoint_type, 1.0)
            
            channel_scores[channel] += base_score * type_multiplier
        
        # Normalize scores and distribute attribution
        total_score = sum(channel_scores.values()) if channel_scores else 1
        
        for touchpoint in journey.touchpoints:
            channel = touchpoint.channel.value
            channel_score = channel_scores[channel]
            
            # Calculate attribution value
            attribution_value = (channel_score / total_score) * journey.total_conversion_value
            
            if channel not in result.channel_attribution:
                result.channel_attribution[channel] = 0
            result.channel_attribution[channel] += attribution_value
            result.touchpoint_attribution[touchpoint.touchpoint_id] = attribution_value
            
            if touchpoint.campaign_id:
                if touchpoint.campaign_id not in result.campaign_attribution:
                    result.campaign_attribution[touchpoint.campaign_id] = 0
                result.campaign_attribution[touchpoint.campaign_id] += attribution_value
        
        return result
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics."""
        active_journeys = len([j for j in self.customer_journeys.values() 
                             if j.journey_end and (datetime.now() - j.journey_end).days <= 7])
        
        avg_journey_length = (
            sum(len(j.touchpoints) for j in self.customer_journeys.values()) / 
            max(len(self.customer_journeys), 1)
        )
        
        avg_conversion_value = (
            sum(j.total_conversion_value for j in self.customer_journeys.values()) / 
            max(len([j for j in self.customer_journeys.values() if j.total_conversion_value > 0]), 1)
        )
        
        return {
            'tracking_metrics': {
                'touchpoints_tracked': self.attribution_stats['touchpoints_tracked'],
                'journeys_analyzed': self.attribution_stats['journeys_analyzed'],
                'conversions_attributed': self.attribution_stats['conversions_attributed'],
                'attribution_models_calculated': self.attribution_stats['attribution_models_calculated']
            },
            'journey_insights': {
                'active_journeys_last_7_days': active_journeys,
                'avg_touchpoints_per_journey': round(avg_journey_length, 1),
                'avg_conversion_value': round(avg_conversion_value, 2),
                'attribution_window_days': self.journey_window_days
            }
        }

def demo_attribution_data_sync():
    """Demonstrate attribution data sync capabilities."""
    print("🚀 ATTRIBUTION DATA SYNC DEMO")
    
    attribution_system = AttributionDataSync()
    
    # Simulate customer journey with multiple touchpoints
    print("\n📊 Creating Customer Journey...")
    
    customer_id = "customer_123"
    
    # Day 1: First touchpoint - Google Ads impression
    attribution_system.add_touchpoint(
        customer_id, TouchpointType.IMPRESSION, Channel.GOOGLE_ADS,
        campaign_id="google_campaign_001", ad_group_id="adgroup_001",
        timestamp=datetime.now() - timedelta(days=7)
    )
    
    # Day 2: Click on Google Ad
    attribution_system.add_touchpoint(
        customer_id, TouchpointType.CLICK, Channel.GOOGLE_ADS,
        campaign_id="google_campaign_001", ad_group_id="adgroup_001",
        timestamp=datetime.now() - timedelta(days=6)
    )
    
    # Day 3: Email click
    attribution_system.add_touchpoint(
        customer_id, TouchpointType.EMAIL_CLICK, Channel.EMAIL,
        campaign_id="email_nurture_001",
        timestamp=datetime.now() - timedelta(days=5)
    )
    
    # Day 7: Direct conversion
    attribution_system.add_touchpoint(
        customer_id, TouchpointType.CONVERSION, Channel.DIRECT,
        conversion_value=500, value=500,
        timestamp=datetime.now() - timedelta(hours=2)
    )
    
    # Get journey information
    journey = list(attribution_system.customer_journeys.values())[0]
    print(f"Journey created with {journey.total_touchpoints} touchpoints")
    print(f"Total conversion value: ${journey.total_conversion_value}")
    print(f"Journey duration: {journey.journey_duration_hours:.1f} hours")
    
    # Calculate attribution using different models
    print("\n🔍 Calculating Attribution Models...")
    
    models_to_test = [
        AttributionModel.FIRST_TOUCH,
        AttributionModel.LAST_TOUCH,
        AttributionModel.LINEAR,
        AttributionModel.TIME_DECAY
    ]
    
    attribution_results = {}
    for model in models_to_test:
        result_id = attribution_system.calculate_attribution(journey.journey_id, model)
        attribution_results[model] = attribution_system.attribution_results[result_id]
    
    # Compare attribution models
    print(f"\n📈 Attribution Model Comparison:")
    for model, result in attribution_results.items():
        print(f"\n{model.value.replace('_', ' ').title()}:")
        for channel, value in result.channel_attribution.items():
            print(f"  {channel}: ${value:.2f}")
    
    # Get system metrics
    system_metrics = attribution_system.get_system_metrics()
    
    print(f"\n🎯 System Performance:")
    print(f"Touchpoints Tracked: {system_metrics['tracking_metrics']['touchpoints_tracked']}")
    print(f"Journeys Analyzed: {system_metrics['tracking_metrics']['journeys_analyzed']}")
    print(f"Conversions Attributed: {system_metrics['tracking_metrics']['conversions_attributed']}")
    print(f"Avg Journey Length: {system_metrics['journey_insights']['avg_touchpoints_per_journey']} touchpoints")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")

if __name__ == "__main__":
    demo_attribution_data_sync()