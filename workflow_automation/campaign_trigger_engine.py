#!/usr/bin/env python3
"""
Campaign Trigger Engine - Intelligent Marketing Automation

Automated campaign triggering based on customer behavior and events.

🎯 SMART CAMPAIGN TRIGGERS 🎯
Event-driven marketing automation with intelligent timing.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
"""

import json
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class TriggerType(Enum):
    """Campaign trigger types"""
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    SCORE_BASED = "score_based"
    EVENT_BASED = "event_based"


@dataclass
class CampaignTrigger:
    """Campaign trigger configuration"""
    trigger_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    trigger_type: TriggerType = TriggerType.BEHAVIORAL
    conditions: Dict[str, Any] = field(default_factory=dict)
    campaign_id: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class CampaignTriggerEngine:
    """
    Intelligent campaign triggering system.
    
    🎯 ENTERPRISE AUTOMATION:
    - Event-driven campaign launching
    - Behavioral trigger detection
    - Multi-channel coordination
    - Performance optimization
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.triggers: Dict[str, CampaignTrigger] = {}
        self.triggered_campaigns: List[Dict] = []
        
    def add_trigger(self, trigger: CampaignTrigger):
        """Add campaign trigger"""
        self.triggers[trigger.trigger_id] = trigger
        
    def evaluate_triggers(self, customer_data: Dict[str, Any]) -> List[str]:
        """Evaluate triggers for customer"""
        triggered_campaigns = []
        
        for trigger in self.triggers.values():
            if not trigger.enabled:
                continue
                
            if self._evaluate_trigger_conditions(trigger, customer_data):
                triggered_campaigns.append(trigger.campaign_id)
                self.triggered_campaigns.append({
                    'trigger_id': trigger.trigger_id,
                    'campaign_id': trigger.campaign_id,
                    'customer_id': customer_data.get('customer_id'),
                    'timestamp': datetime.now()
                })
                
        return triggered_campaigns
        
    def _evaluate_trigger_conditions(self, trigger: CampaignTrigger, data: Dict[str, Any]) -> bool:
        """Evaluate trigger conditions"""
        conditions = trigger.conditions
        
        if trigger.trigger_type == TriggerType.BEHAVIORAL:
            # Check behavioral conditions
            page_views = data.get('page_views', 0)
            if 'min_page_views' in conditions and page_views < conditions['min_page_views']:
                return False
                
        elif trigger.trigger_type == TriggerType.SCORE_BASED:
            # Check score conditions
            lead_score = data.get('lead_score', 0)
            if 'min_score' in conditions and lead_score < conditions['min_score']:
                return False
                
        elif trigger.trigger_type == TriggerType.EVENT_BASED:
            # Check event conditions
            events = data.get('recent_events', [])
            required_event = conditions.get('event_type')
            if required_event and required_event not in events:
                return False
                
        return True
        
    def get_trigger_stats(self) -> Dict[str, Any]:
        """Get trigger performance statistics"""
        return {
            'total_triggers': len(self.triggers),
            'active_triggers': sum(1 for t in self.triggers.values() if t.enabled),
            'triggered_campaigns': len(self.triggered_campaigns)
        }


def demo_campaign_triggers():
    """Demo campaign trigger engine"""
    print("🎯 CAMPAIGN TRIGGER ENGINE DEMO")
    
    engine = CampaignTriggerEngine()
    
    # Add sample trigger
    high_value_trigger = CampaignTrigger(
        name="High Value Lead Trigger",
        trigger_type=TriggerType.SCORE_BASED,
        conditions={'min_score': 80},
        campaign_id="CAMP_001"
    )
    engine.add_trigger(high_value_trigger)
    
    # Test trigger
    customer_data = {
        'customer_id': 'CUST_001',
        'lead_score': 85,
        'page_views': 10
    }
    
    triggered = engine.evaluate_triggers(customer_data)
    print(f"Triggered Campaigns: {len(triggered)}")
    
    stats = engine.get_trigger_stats()
    print(f"Active Triggers: {stats['active_triggers']}")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")


if __name__ == "__main__":
    demo_campaign_triggers()

