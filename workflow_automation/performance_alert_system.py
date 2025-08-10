#!/usr/bin/env python3
"""
Performance Alert System - MarTech Integration Hub

Real-time performance monitoring and alerting system for marketing campaigns.
Provides intelligent alerts, anomaly detection, and automated response capabilities.

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
from typing import Any, Callable, Dict, List, Optional

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    PERFORMANCE_DROP = "performance_drop"
    BUDGET_THRESHOLD = "budget_threshold"
    CONVERSION_ANOMALY = "conversion_anomaly"
    TRAFFIC_SPIKE = "traffic_spike"
    COST_INCREASE = "cost_increase"
    QUALITY_SCORE_DROP = "quality_score_drop"
    CAMPAIGN_FAILURE = "campaign_failure"

class MetricType(Enum):
    CTR = "click_through_rate"
    CONVERSION_RATE = "conversion_rate"
    CPC = "cost_per_click"
    CPL = "cost_per_lead"
    ROAS = "return_on_ad_spend"
    BUDGET_SPEND = "budget_spend"
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"

@dataclass
class Alert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType = AlertType.PERFORMANCE_DROP
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    message: str = ""
    metric: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    campaign_id: Optional[str] = None
    platform: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AlertRule:
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    metric_type: MetricType = MetricType.CTR
    condition: str = "less_than"  # less_than, greater_than, change_percent
    threshold: float = 0.0
    time_window_minutes: int = 60
    alert_type: AlertType = AlertType.PERFORMANCE_DROP
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    platforms: List[str] = field(default_factory=list)
    campaigns: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class PerformanceAlertSystem:
    """
    Advanced performance alert system for MarTech campaigns.
    
    🎯 ENTERPRISE CAPABILITIES:
    - Real-time performance monitoring
    - Intelligent anomaly detection
    - Multi-platform campaign alerting
    - Automated response workflows
    - Executive escalation protocols
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1440))  # 24 hours of minutes
        self.notification_handlers: Dict[str, Callable] = {}
        self.performance_stats = {
            'alerts_triggered': 0,
            'alerts_resolved': 0,
            'false_positives': 0,
            'campaign_issues_detected': 0
        }
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules."""
        default_rules = [
            {
                'name': 'Low CTR Alert',
                'metric_type': MetricType.CTR,
                'condition': 'less_than',
                'threshold': 1.0,
                'alert_type': AlertType.PERFORMANCE_DROP,
                'severity': AlertSeverity.MEDIUM
            },
            {
                'name': 'High CPC Alert',
                'metric_type': MetricType.CPC,
                'condition': 'greater_than',
                'threshold': 5.0,
                'alert_type': AlertType.COST_INCREASE,
                'severity': AlertSeverity.HIGH
            },
            {
                'name': 'Budget Threshold Alert',
                'metric_type': MetricType.BUDGET_SPEND,
                'condition': 'greater_than',
                'threshold': 80.0,  # 80% of budget
                'alert_type': AlertType.BUDGET_THRESHOLD,
                'severity': AlertSeverity.HIGH
            },
            {
                'name': 'Low Conversion Rate',
                'metric_type': MetricType.CONVERSION_RATE,
                'condition': 'less_than',
                'threshold': 2.0,
                'alert_type': AlertType.CONVERSION_ANOMALY,
                'severity': AlertSeverity.MEDIUM
            }
        ]
        
        for rule_config in default_rules:
            self.create_alert_rule(**rule_config)
    
    def create_alert_rule(self, name: str, metric_type: MetricType, condition: str,
                         threshold: float, alert_type: AlertType, 
                         severity: AlertSeverity, **kwargs) -> str:
        """Create a new alert rule."""
        rule = AlertRule(
            name=name,
            metric_type=metric_type,
            condition=condition,
            threshold=threshold,
            alert_type=alert_type,
            severity=severity,
            **kwargs
        )
        
        self.alert_rules[rule.rule_id] = rule
        return rule.rule_id
    
    def update_metric(self, metric_key: str, value: float, 
                     platform: str = None, campaign_id: str = None):
        """Update a metric value and check for alerts."""
        timestamp = datetime.now()
        
        # Store metric in history
        metric_data = {
            'timestamp': timestamp,
            'value': value,
            'platform': platform,
            'campaign_id': campaign_id
        }
        self.metrics_history[metric_key].append(metric_data)
        
        # Check alert rules
        self._evaluate_alert_rules(metric_key, value, platform, campaign_id)
    
    def _evaluate_alert_rules(self, metric_key: str, current_value: float,
                             platform: str = None, campaign_id: str = None):
        """Evaluate all alert rules against current metric."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this metric, platform, or campaign
            metric_matches = rule.metric_type.value in metric_key.lower()
            platform_matches = not rule.platforms or platform in rule.platforms
            campaign_matches = not rule.campaigns or campaign_id in rule.campaigns
            
            if not (metric_matches and platform_matches and campaign_matches):
                continue
            
            # Evaluate condition
            should_alert = False
            if rule.condition == 'less_than' and current_value < rule.threshold:
                should_alert = True
            elif rule.condition == 'greater_than' and current_value > rule.threshold:
                should_alert = True
            elif rule.condition == 'change_percent':
                # Check for percentage change over time window
                historical_avg = self._get_historical_average(metric_key, rule.time_window_minutes)
                if historical_avg > 0:
                    change_percent = ((current_value - historical_avg) / historical_avg) * 100
                    if abs(change_percent) > rule.threshold:
                        should_alert = True
            
            if should_alert:
                self._create_alert(rule, metric_key, current_value, platform, campaign_id)
    
    def _get_historical_average(self, metric_key: str, window_minutes: int) -> float:
        """Calculate historical average for a metric over time window."""
        if metric_key not in self.metrics_history:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        relevant_data = [
            entry['value'] for entry in self.metrics_history[metric_key]
            if entry['timestamp'] > cutoff_time
        ]
        
        return sum(relevant_data) / len(relevant_data) if relevant_data else 0.0
    
    def _create_alert(self, rule: AlertRule, metric: str, current_value: float,
                     platform: str = None, campaign_id: str = None):
        """Create a new alert based on rule violation."""
        # Check for duplicate alerts (within last hour)
        recent_alerts = [
            alert for alert in self.alerts.values()
            if (alert.alert_type == rule.alert_type and 
                alert.campaign_id == campaign_id and
                alert.platform == platform and
                (datetime.now() - alert.created_at).seconds < 3600)
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alerts
        
        alert = Alert(
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=f"{rule.name}: {platform or 'Unknown Platform'}",
            message=self._generate_alert_message(rule, metric, current_value, platform, campaign_id),
            metric=metric,
            current_value=current_value,
            threshold_value=rule.threshold,
            campaign_id=campaign_id,
            platform=platform,
            metadata={
                'rule_id': rule.rule_id,
                'condition': rule.condition
            }
        )
        
        self.alerts[alert.alert_id] = alert
        self.performance_stats['alerts_triggered'] += 1
        
        # Trigger notifications
        self._send_notifications(alert)
    
    def _generate_alert_message(self, rule: AlertRule, metric: str, current_value: float,
                               platform: str = None, campaign_id: str = None) -> str:
        """Generate descriptive alert message."""
        base_msg = f"Alert triggered for {rule.name}"
        
        if campaign_id:
            base_msg += f" in campaign {campaign_id}"
        if platform:
            base_msg += f" on {platform}"
        
        condition_text = {
            'less_than': f"dropped below {rule.threshold}",
            'greater_than': f"exceeded {rule.threshold}",
            'change_percent': f"changed by more than {rule.threshold}%"
        }.get(rule.condition, "met alert condition")
        
        base_msg += f". {metric.replace('_', ' ').title()} {condition_text} (current: {current_value:.2f})"
        
        # Add recommendations based on alert type
        recommendations = {
            AlertType.PERFORMANCE_DROP: "Consider reviewing ad creative, targeting, or bidding strategy.",
            AlertType.BUDGET_THRESHOLD: "Budget limit approaching. Consider increasing budget or optimizing spend allocation.",
            AlertType.COST_INCREASE: "Costs are increasing. Review bidding strategy and keyword relevance.",
            AlertType.CONVERSION_ANOMALY: "Conversion rate deviation detected. Check landing page and tracking setup."
        }
        
        if rule.alert_type in recommendations:
            base_msg += f" Recommendation: {recommendations[rule.alert_type]}"
        
        return base_msg
    
    def register_notification_handler(self, handler_name: str, handler_func: Callable):
        """Register a notification handler (email, Slack, etc.)."""
        self.notification_handlers[handler_name] = handler_func
    
    def _send_notifications(self, alert: Alert):
        """Send notifications through registered handlers."""
        for handler_name, handler_func in self.notification_handlers.items():
            try:
                handler_func(alert)
            except Exception as e:
                print(f"Failed to send notification via {handler_name}: {e}")
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            self.alerts[alert_id].metadata['acknowledged_by'] = user
            self.alerts[alert_id].metadata['acknowledged_at'] = datetime.now().isoformat()
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = "system", resolution_notes: str = "") -> bool:
        """Resolve an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].metadata['resolved_by'] = user
            self.alerts[alert_id].metadata['resolved_at'] = datetime.now().isoformat()
            if resolution_notes:
                self.alerts[alert_id].metadata['resolution_notes'] = resolution_notes
            self.performance_stats['alerts_resolved'] += 1
            return True
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None, 
                         platform: str = None) -> List[Alert]:
        """Get active (unresolved) alerts."""
        active_alerts = [
            alert for alert in self.alerts.values()
            if not alert.resolved
        ]
        
        if severity:
            active_alerts = [a for a in active_alerts if a.severity == severity]
        if platform:
            active_alerts = [a for a in active_alerts if a.platform == platform]
        
        # Sort by severity and creation time
        severity_order = {AlertSeverity.CRITICAL: 4, AlertSeverity.HIGH: 3, 
                         AlertSeverity.MEDIUM: 2, AlertSeverity.LOW: 1}
        
        return sorted(active_alerts, 
                     key=lambda x: (severity_order[x.severity], x.created_at), 
                     reverse=True)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert system performance."""
        active_alerts = self.get_active_alerts()
        severity_counts = defaultdict(int)
        
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_alerts': len(self.alerts),
            'active_alerts': len(active_alerts),
            'resolved_alerts': self.performance_stats['alerts_resolved'],
            'alerts_by_severity': dict(severity_counts),
            'alert_rules_configured': len(self.alert_rules),
            'monitoring_metrics': len(self.metrics_history),
            'system_uptime_hours': 24,  # Simulated
            'false_positive_rate': (
                self.performance_stats['false_positives'] / 
                max(self.performance_stats['alerts_triggered'], 1)
            ) * 100
        }

def sample_email_handler(alert: Alert):
    """Sample email notification handler."""
    print(f"EMAIL NOTIFICATION: {alert.severity.value.upper()} - {alert.title}")
    print(f"Message: {alert.message}")

def demo_performance_alert_system():
    """Demonstrate performance alert system capabilities."""
    print("🚀 PERFORMANCE ALERT SYSTEM DEMO")
    
    alert_system = PerformanceAlertSystem()
    
    # Register notification handler
    alert_system.register_notification_handler("email", sample_email_handler)
    
    # Simulate metric updates that should trigger alerts
    print("\n📊 Simulating Campaign Metrics...")
    
    # Low CTR scenario
    alert_system.update_metric("google_ads_ctr", 0.8, "Google Ads", "campaign_123")
    
    # High CPC scenario
    alert_system.update_metric("facebook_ads_cpc", 6.5, "Facebook Ads", "campaign_456")
    
    # Budget threshold scenario
    alert_system.update_metric("campaign_budget_spend", 85.0, "Google Ads", "campaign_789")
    
    # Normal metrics (should not trigger alerts)
    alert_system.update_metric("linkedin_ads_ctr", 2.5, "LinkedIn Ads", "campaign_abc")
    alert_system.update_metric("twitter_ads_conversion_rate", 3.2, "Twitter Ads", "campaign_def")
    
    # Get alert summary
    summary = alert_system.get_alert_summary()
    active_alerts = alert_system.get_active_alerts()
    
    print(f"\n🚨 Alert Summary:")
    print(f"Active Alerts: {summary['active_alerts']}")
    print(f"Total Alerts Generated: {summary['total_alerts']}")
    print(f"Alert Rules Configured: {summary['alert_rules_configured']}")
    
    print(f"\n🔥 Active High Priority Alerts:")
    high_priority_alerts = [a for a in active_alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]
    for alert in high_priority_alerts[:3]:  # Show top 3
        print(f"- {alert.title}: {alert.message[:80]}...")
    
    # Demonstrate alert resolution
    if active_alerts:
        first_alert = active_alerts[0]
        alert_system.acknowledge_alert(first_alert.alert_id, "marketing_manager")
        alert_system.resolve_alert(first_alert.alert_id, "marketing_manager", "Adjusted bidding strategy")
        print(f"\n✅ Resolved Alert: {first_alert.title}")
    
    updated_summary = alert_system.get_alert_summary()
    print(f"\nUpdated Active Alerts: {updated_summary['active_alerts']}")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")

if __name__ == "__main__":
    demo_performance_alert_system()