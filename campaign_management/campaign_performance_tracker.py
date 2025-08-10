"""
Campaign Performance Tracker for MarTech Integration Hub

Comprehensive real-time campaign performance monitoring and analytics system
for multi-channel marketing campaigns with advanced metrics tracking and optimization.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import redis
from collections import defaultdict, deque
import threading
import queue

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Campaign execution status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class CampaignChannel(Enum):
    """Supported campaign channels."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    SEARCH_ADS = "search_ads"
    DISPLAY_ADS = "display_ads"
    VIDEO_ADS = "video_ads"
    CONTENT_MARKETING = "content_marketing"
    WEBINAR = "webinar"
    SMS = "sms"
    PUSH_NOTIFICATION = "push_notification"
    AFFILIATE = "affiliate"
    INFLUENCER = "influencer"


class MetricType(Enum):
    """Campaign performance metric types."""
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    REVENUE = "revenue"
    COST = "cost"
    CTR = "ctr"
    CPC = "cpc"
    CPM = "cpm"
    CPA = "cpa"
    ROAS = "roas"
    ROI = "roi"
    ENGAGEMENT_RATE = "engagement_rate"
    BOUNCE_RATE = "bounce_rate"
    TIME_ON_SITE = "time_on_site"
    CONVERSION_RATE = "conversion_rate"
    LEAD_SCORE = "lead_score"
    LIFETIME_VALUE = "lifetime_value"


class AlertType(Enum):
    """Performance alert types."""
    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY_DETECTED = "anomaly_detected"
    BUDGET_EXCEEDED = "budget_exceeded"
    PERFORMANCE_DECLINE = "performance_decline"
    CONVERSION_DROP = "conversion_drop"
    COST_SPIKE = "cost_spike"
    CHANNEL_FAILURE = "channel_failure"
    GOAL_ACHIEVED = "goal_achieved"


@dataclass
class CampaignMetric:
    """Individual campaign performance metric."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    channel: CampaignChannel
    campaign_id: str
    segment: Optional[str] = None
    source: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignGoal:
    """Campaign performance goal definition."""
    goal_id: str
    campaign_id: str
    metric_type: MetricType
    target_value: float
    threshold_type: str = "minimum"  # minimum, maximum, exact
    deadline: Optional[datetime] = None
    priority: str = "medium"  # high, medium, low
    is_achieved: bool = False
    achieved_at: Optional[datetime] = None
    progress_percentage: float = 0.0


@dataclass
class PerformanceAlert:
    """Campaign performance alert."""
    alert_id: str
    campaign_id: str
    alert_type: AlertType
    message: str
    severity: str  # critical, warning, info
    metric_type: MetricType
    current_value: float
    threshold_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    is_acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


@dataclass
class CampaignSnapshot:
    """Campaign performance snapshot at a point in time."""
    campaign_id: str
    timestamp: datetime
    status: CampaignStatus
    metrics: Dict[MetricType, float]
    channel_metrics: Dict[CampaignChannel, Dict[MetricType, float]]
    goals_progress: List[CampaignGoal]
    alerts: List[PerformanceAlert]
    budget_spent: float
    budget_remaining: float
    estimated_completion: Optional[datetime] = None


@dataclass
class CampaignComparison:
    """Campaign performance comparison analysis."""
    primary_campaign_id: str
    comparison_campaign_id: str
    comparison_type: str  # period_over_period, campaign_vs_campaign, segment_comparison
    metrics_comparison: Dict[MetricType, Dict[str, float]]  # {metric: {primary: value, comparison: value, difference: value, percentage_change: value}}
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class CampaignPerformanceTracker:
    """
    Comprehensive campaign performance tracking and analytics system.
    
    Features:
    - Real-time performance monitoring
    - Multi-channel metric aggregation
    - Goal tracking and achievement monitoring
    - Anomaly detection and alerting
    - Performance trend analysis
    - Comparative campaign analysis
    - Predictive performance modeling
    - Automated optimization recommendations
    """
    
    def __init__(self, 
                 redis_host: str = 'localhost',
                 redis_port: int = 6379,
                 alert_thresholds: Optional[Dict[MetricType, Dict[str, float]]] = None):
        
        # Redis connection for real-time data
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()
            self.redis_available = True
        except:
            self.redis_available = False
            logger.warning("Redis not available, using in-memory storage")
        
        # In-memory data stores
        self.campaigns: Dict[str, Dict[str, Any]] = {}
        self.metrics_history: Dict[str, List[CampaignMetric]] = defaultdict(list)
        self.goals: Dict[str, List[CampaignGoal]] = defaultdict(list)
        self.alerts: Dict[str, List[PerformanceAlert]] = defaultdict(list)
        self.snapshots: Dict[str, List[CampaignSnapshot]] = defaultdict(list)
        
        # Alert thresholds configuration
        self.alert_thresholds = alert_thresholds or self._get_default_thresholds()
        
        # Performance tracking
        self.metric_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_detectors: Dict[str, Dict] = defaultdict(dict)
        
        # Threading for real-time processing
        self.processing_queue = queue.Queue()
        self.alert_queue = queue.Queue()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Performance models
        self.prediction_models: Dict[str, Dict] = defaultdict(dict)
        self.scaler = StandardScaler()
        
        logger.info("Campaign Performance Tracker initialized successfully")
    
    def _get_default_thresholds(self) -> Dict[MetricType, Dict[str, float]]:
        """Get default alert thresholds for metrics."""
        return {
            MetricType.CTR: {'min': 0.01, 'max': 0.15, 'anomaly_factor': 2.0},
            MetricType.CPC: {'min': 0.50, 'max': 10.00, 'anomaly_factor': 1.5},
            MetricType.CONVERSION_RATE: {'min': 0.005, 'max': 0.20, 'anomaly_factor': 2.0},
            MetricType.ROAS: {'min': 2.0, 'max': 20.0, 'anomaly_factor': 1.5},
            MetricType.ROI: {'min': 0.20, 'max': 5.0, 'anomaly_factor': 1.5},
            MetricType.BOUNCE_RATE: {'min': 0.20, 'max': 0.80, 'anomaly_factor': 1.5},
            MetricType.COST: {'max_daily_increase': 0.20, 'anomaly_factor': 2.0},
            MetricType.IMPRESSIONS: {'min_daily': 100, 'anomaly_factor': 2.0}
        }
    
    def register_campaign(self, 
                         campaign_id: str,
                         campaign_name: str,
                         channels: List[CampaignChannel],
                         start_date: datetime,
                         end_date: Optional[datetime] = None,
                         budget: float = 0.0,
                         goals: Optional[List[CampaignGoal]] = None) -> bool:
        """Register a new campaign for tracking."""
        try:
            campaign_config = {
                'campaign_id': campaign_id,
                'name': campaign_name,
                'channels': [ch.value for ch in channels],
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat() if end_date else None,
                'budget': budget,
                'status': CampaignStatus.DRAFT.value,
                'created_at': datetime.now().isoformat(),
                'total_spent': 0.0,
                'metrics_summary': {}
            }
            
            self.campaigns[campaign_id] = campaign_config
            
            # Store goals if provided
            if goals:
                self.goals[campaign_id] = goals
            
            # Initialize metric buffers
            for channel in channels:
                for metric_type in MetricType:
                    key = f"{campaign_id}_{channel.value}_{metric_type.value}"
                    self.metric_buffers[key] = deque(maxlen=1000)
            
            # Store in Redis if available
            if self.redis_available:
                self.redis_client.hset(
                    f"campaign:{campaign_id}",
                    mapping=campaign_config
                )
            
            logger.info(f"Registered campaign for tracking: {campaign_name} ({campaign_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register campaign: {e}")
            return False
    
    def record_metric(self, metric: CampaignMetric) -> bool:
        """Record a campaign performance metric."""
        try:
            # Store metric in history
            self.metrics_history[metric.campaign_id].append(metric)
            
            # Update metric buffer for real-time analysis
            buffer_key = f"{metric.campaign_id}_{metric.channel.value}_{metric.metric_type.value}"
            self.metric_buffers[buffer_key].append({
                'timestamp': metric.timestamp,
                'value': metric.value
            })
            
            # Update campaign summary
            if metric.campaign_id in self.campaigns:
                summary = self.campaigns[metric.campaign_id].get('metrics_summary', {})
                metric_key = f"{metric.channel.value}_{metric.metric_type.value}"
                summary[metric_key] = metric.value
                self.campaigns[metric.campaign_id]['metrics_summary'] = summary
            
            # Check for alerts
            self._check_metric_alerts(metric)
            
            # Update goals progress
            self._update_goals_progress(metric)
            
            # Store in Redis if available
            if self.redis_available:
                metric_data = {
                    'campaign_id': metric.campaign_id,
                    'metric_type': metric.metric_type.value,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'channel': metric.channel.value,
                    'segment': metric.segment or '',
                    'source': metric.source or ''
                }
                
                self.redis_client.lpush(
                    f"metrics:{metric.campaign_id}",
                    json.dumps(metric_data)
                )
                
                # Keep only recent metrics (last 10000)
                self.redis_client.ltrim(f"metrics:{metric.campaign_id}", 0, 9999)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            return False
    
    def _check_metric_alerts(self, metric: CampaignMetric):
        """Check if metric triggers any alerts."""
        try:
            thresholds = self.alert_thresholds.get(metric.metric_type, {})
            
            alerts_triggered = []
            
            # Threshold breach alerts
            if 'min' in thresholds and metric.value < thresholds['min']:
                alert = PerformanceAlert(
                    alert_id=f"alert_{metric.campaign_id}_{int(time.time())}",
                    campaign_id=metric.campaign_id,
                    alert_type=AlertType.THRESHOLD_BREACH,
                    message=f"{metric.metric_type.value} below minimum threshold: {metric.value:.4f} < {thresholds['min']:.4f}",
                    severity="warning",
                    metric_type=metric.metric_type,
                    current_value=metric.value,
                    threshold_value=thresholds['min']
                )
                alerts_triggered.append(alert)
            
            if 'max' in thresholds and metric.value > thresholds['max']:
                alert = PerformanceAlert(
                    alert_id=f"alert_{metric.campaign_id}_{int(time.time())}",
                    campaign_id=metric.campaign_id,
                    alert_type=AlertType.THRESHOLD_BREACH,
                    message=f"{metric.metric_type.value} above maximum threshold: {metric.value:.4f} > {thresholds['max']:.4f}",
                    severity="critical" if metric.metric_type == MetricType.COST else "warning",
                    metric_type=metric.metric_type,
                    current_value=metric.value,
                    threshold_value=thresholds['max']
                )
                alerts_triggered.append(alert)
            
            # Anomaly detection alerts
            if 'anomaly_factor' in thresholds:
                anomaly_alert = self._check_anomaly(metric, thresholds['anomaly_factor'])
                if anomaly_alert:
                    alerts_triggered.append(anomaly_alert)
            
            # Store alerts
            for alert in alerts_triggered:
                self.alerts[metric.campaign_id].append(alert)
            
        except Exception as e:
            logger.error(f"Failed to check metric alerts: {e}")
    
    def _check_anomaly(self, metric: CampaignMetric, anomaly_factor: float) -> Optional[PerformanceAlert]:
        """Detect anomalies in metric values using statistical analysis."""
        try:
            buffer_key = f"{metric.campaign_id}_{metric.channel.value}_{metric.metric_type.value}"
            buffer = self.metric_buffers[buffer_key]
            
            if len(buffer) < 10:  # Need at least 10 data points
                return None
            
            # Get recent values
            recent_values = [point['value'] for point in list(buffer)[-10:]]
            
            # Calculate statistics
            mean_value = statistics.mean(recent_values)
            std_value = statistics.stdev(recent_values) if len(recent_values) > 1 else 0
            
            # Check if current value is anomalous
            if std_value > 0:
                z_score = abs(metric.value - mean_value) / std_value
                
                if z_score > anomaly_factor:
                    return PerformanceAlert(
                        alert_id=f"anomaly_{metric.campaign_id}_{int(time.time())}",
                        campaign_id=metric.campaign_id,
                        alert_type=AlertType.ANOMALY_DETECTED,
                        message=f"Anomaly detected in {metric.metric_type.value}: {metric.value:.4f} (Z-score: {z_score:.2f})",
                        severity="warning",
                        metric_type=metric.metric_type,
                        current_value=metric.value,
                        threshold_value=mean_value
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check anomaly: {e}")
            return None
    
    def _update_goals_progress(self, metric: CampaignMetric):
        """Update campaign goals progress based on new metric."""
        try:
            campaign_goals = self.goals.get(metric.campaign_id, [])
            
            for goal in campaign_goals:
                if goal.metric_type == metric.metric_type and not goal.is_achieved:
                    
                    # Calculate progress
                    if goal.threshold_type == "minimum":
                        progress = min(100, (metric.value / goal.target_value) * 100)
                    elif goal.threshold_type == "maximum":
                        progress = min(100, ((goal.target_value - metric.value) / goal.target_value) * 100)
                    else:  # exact
                        progress = max(0, 100 - abs((metric.value - goal.target_value) / goal.target_value) * 100)
                    
                    goal.progress_percentage = max(0, progress)
                    
                    # Check if goal is achieved
                    achieved = False
                    if goal.threshold_type == "minimum" and metric.value >= goal.target_value:
                        achieved = True
                    elif goal.threshold_type == "maximum" and metric.value <= goal.target_value:
                        achieved = True
                    elif goal.threshold_type == "exact" and abs(metric.value - goal.target_value) / goal.target_value < 0.05:
                        achieved = True
                    
                    if achieved and not goal.is_achieved:
                        goal.is_achieved = True
                        goal.achieved_at = datetime.now()
                        
                        # Create achievement alert
                        achievement_alert = PerformanceAlert(
                            alert_id=f"goal_{goal.goal_id}_{int(time.time())}",
                            campaign_id=metric.campaign_id,
                            alert_type=AlertType.GOAL_ACHIEVED,
                            message=f"Goal achieved: {goal.metric_type.value} reached {metric.value:.4f} (target: {goal.target_value:.4f})",
                            severity="info",
                            metric_type=goal.metric_type,
                            current_value=metric.value,
                            threshold_value=goal.target_value
                        )
                        
                        self.alerts[metric.campaign_id].append(achievement_alert)
            
        except Exception as e:
            logger.error(f"Failed to update goals progress: {e}")
    
    def get_campaign_performance(self, 
                               campaign_id: str,
                               time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get comprehensive campaign performance data."""
        try:
            if campaign_id not in self.campaigns:
                return {}
            
            campaign_info = self.campaigns[campaign_id].copy()
            metrics = self.metrics_history.get(campaign_id, [])
            
            # Filter metrics by time range if specified
            if time_range:
                start_time, end_time = time_range
                metrics = [m for m in metrics if start_time <= m.timestamp <= end_time]
            
            # Aggregate metrics by type and channel
            metric_aggregations = defaultdict(lambda: defaultdict(list))
            
            for metric in metrics:
                metric_aggregations[metric.metric_type][metric.channel].append(metric.value)
            
            # Calculate aggregated statistics
            performance_data = {
                'campaign_info': campaign_info,
                'metrics_summary': {},
                'channel_performance': {},
                'time_series': {},
                'goals_status': [asdict(goal) for goal in self.goals.get(campaign_id, [])],
                'recent_alerts': [asdict(alert) for alert in self.alerts.get(campaign_id, [])[-10:]],
                'performance_trends': {},
                'recommendations': []
            }
            
            # Calculate metrics summary
            for metric_type, channels in metric_aggregations.items():
                total_values = []
                for channel, values in channels.items():
                    total_values.extend(values)
                
                if total_values:
                    performance_data['metrics_summary'][metric_type.value] = {
                        'current': total_values[-1] if total_values else 0,
                        'average': statistics.mean(total_values),
                        'min': min(total_values),
                        'max': max(total_values),
                        'trend': self._calculate_trend(total_values),
                        'total_records': len(total_values)
                    }
            
            # Channel performance breakdown
            for metric_type, channels in metric_aggregations.items():
                if metric_type.value not in performance_data['channel_performance']:
                    performance_data['channel_performance'][metric_type.value] = {}
                
                for channel, values in channels.items():
                    if values:
                        performance_data['channel_performance'][metric_type.value][channel.value] = {
                            'current': values[-1],
                            'average': statistics.mean(values),
                            'total': sum(values) if metric_type in [MetricType.CLICKS, MetricType.IMPRESSIONS, MetricType.CONVERSIONS, MetricType.REVENUE, MetricType.COST] else statistics.mean(values)
                        }
            
            # Generate recommendations
            performance_data['recommendations'] = self._generate_recommendations(campaign_id, metrics)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to get campaign performance: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return "stable"
        
        # Use linear regression to determine trend
        x = np.array(range(len(values))).reshape(-1, 1)
        y = np.array(values)
        
        model = LinearRegression().fit(x, y)
        slope = model.coef_[0]
        
        if slope > 0.05:
            return "increasing"
        elif slope < -0.05:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recommendations(self, campaign_id: str, metrics: List[CampaignMetric]) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []
        
        try:
            if not metrics:
                return ["Insufficient data for recommendations"]
            
            # Group metrics by type for analysis
            metric_groups = defaultdict(list)
            for metric in metrics[-100:]:  # Analyze last 100 metrics
                metric_groups[metric.metric_type].append(metric.value)
            
            # CTR analysis
            if MetricType.CTR in metric_groups:
                ctr_values = metric_groups[MetricType.CTR]
                avg_ctr = statistics.mean(ctr_values)
                if avg_ctr < 0.02:
                    recommendations.append("CTR is below industry average (2%). Consider improving ad copy, targeting, or creative elements.")
                elif avg_ctr > 0.08:
                    recommendations.append("Excellent CTR performance! Consider scaling this campaign or applying successful elements to other campaigns.")
            
            # Cost analysis
            if MetricType.CPC in metric_groups:
                cpc_values = metric_groups[MetricType.CPC]
                if len(cpc_values) > 1:
                    trend = self._calculate_trend(cpc_values)
                    if trend == "increasing":
                        recommendations.append("CPC is trending upward. Review keyword competition and consider bid adjustments.")
            
            # Conversion analysis
            if MetricType.CONVERSION_RATE in metric_groups:
                conv_values = metric_groups[MetricType.CONVERSION_RATE]
                avg_conv = statistics.mean(conv_values)
                if avg_conv < 0.01:
                    recommendations.append("Low conversion rate detected. Review landing page experience and funnel optimization.")
            
            # ROAS analysis
            if MetricType.ROAS in metric_groups:
                roas_values = metric_groups[MetricType.ROAS]
                avg_roas = statistics.mean(roas_values)
                if avg_roas < 3.0:
                    recommendations.append("ROAS below target (3.0x). Consider audience refinement or budget reallocation.")
                elif avg_roas > 6.0:
                    recommendations.append("Strong ROAS performance. Consider increasing budget allocation to this campaign.")
            
            # Goals analysis
            campaign_goals = self.goals.get(campaign_id, [])
            unachieved_goals = [g for g in campaign_goals if not g.is_achieved]
            
            if unachieved_goals:
                high_priority_goals = [g for g in unachieved_goals if g.priority == "high"]
                if high_priority_goals:
                    recommendations.append(f"Focus on {len(high_priority_goals)} high-priority unachieved goals. Consider strategy adjustments.")
            
            if not recommendations:
                recommendations.append("Campaign performance is within normal parameters. Continue monitoring for optimization opportunities.")
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error"]
    
    def compare_campaigns(self, 
                         primary_campaign_id: str,
                         comparison_campaign_id: str,
                         comparison_type: str = "campaign_vs_campaign",
                         time_range: Optional[Tuple[datetime, datetime]] = None) -> CampaignComparison:
        """Compare performance between two campaigns or time periods."""
        try:
            primary_performance = self.get_campaign_performance(primary_campaign_id, time_range)
            comparison_performance = self.get_campaign_performance(comparison_campaign_id, time_range)
            
            if not primary_performance or not comparison_performance:
                raise ValueError("Campaign data not found for comparison")
            
            # Compare metrics
            metrics_comparison = {}
            primary_metrics = primary_performance.get('metrics_summary', {})
            comparison_metrics = comparison_performance.get('metrics_summary', {})
            
            all_metrics = set(primary_metrics.keys()) | set(comparison_metrics.keys())
            
            for metric_name in all_metrics:
                primary_value = primary_metrics.get(metric_name, {}).get('current', 0)
                comparison_value = comparison_metrics.get(metric_name, {}).get('current', 0)
                
                difference = primary_value - comparison_value
                percentage_change = (difference / comparison_value * 100) if comparison_value != 0 else 0
                
                metrics_comparison[metric_name] = {
                    'primary': primary_value,
                    'comparison': comparison_value,
                    'difference': difference,
                    'percentage_change': percentage_change,
                    'better_performer': 'primary' if primary_value > comparison_value else 'comparison'
                }
            
            # Performance summary
            performance_summary = {
                'primary_campaign_name': primary_performance['campaign_info'].get('name', primary_campaign_id),
                'comparison_campaign_name': comparison_performance['campaign_info'].get('name', comparison_campaign_id),
                'metrics_compared': len(metrics_comparison),
                'primary_wins': sum(1 for m in metrics_comparison.values() if m['better_performer'] == 'primary'),
                'comparison_wins': sum(1 for m in metrics_comparison.values() if m['better_performer'] == 'comparison'),
                'significant_differences': len([m for m in metrics_comparison.values() if abs(m['percentage_change']) > 20])
            }
            
            # Generate comparison recommendations
            recommendations = []
            
            # Identify significant improvements
            improving_metrics = [name for name, data in metrics_comparison.items() 
                               if data['percentage_change'] > 20 and data['better_performer'] == 'primary']
            
            declining_metrics = [name for name, data in metrics_comparison.items() 
                               if data['percentage_change'] < -20 and data['better_performer'] == 'comparison']
            
            if improving_metrics:
                recommendations.append(f"Strong performance improvement in: {', '.join(improving_metrics)}")
            
            if declining_metrics:
                recommendations.append(f"Performance decline in: {', '.join(declining_metrics)}. Consider optimization.")
            
            if not improving_metrics and not declining_metrics:
                recommendations.append("Performance is relatively stable between campaigns.")
            
            return CampaignComparison(
                primary_campaign_id=primary_campaign_id,
                comparison_campaign_id=comparison_campaign_id,
                comparison_type=comparison_type,
                metrics_comparison=metrics_comparison,
                performance_summary=performance_summary,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to compare campaigns: {e}")
            return None
    
    def create_performance_snapshot(self, campaign_id: str) -> CampaignSnapshot:
        """Create a performance snapshot for a campaign at current time."""
        try:
            if campaign_id not in self.campaigns:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            campaign_info = self.campaigns[campaign_id]
            performance_data = self.get_campaign_performance(campaign_id)
            
            # Extract current metrics
            current_metrics = {}
            channel_metrics = defaultdict(dict)
            
            metrics_summary = performance_data.get('metrics_summary', {})
            channel_performance = performance_data.get('channel_performance', {})
            
            for metric_name, metric_data in metrics_summary.items():
                try:
                    metric_type = MetricType(metric_name)
                    current_metrics[metric_type] = metric_data.get('current', 0)
                except ValueError:
                    continue  # Skip unknown metric types
            
            for metric_name, channels in channel_performance.items():
                try:
                    metric_type = MetricType(metric_name)
                    for channel_name, channel_data in channels.items():
                        try:
                            channel = CampaignChannel(channel_name)
                            channel_metrics[channel][metric_type] = channel_data.get('current', 0)
                        except ValueError:
                            continue
                except ValueError:
                    continue
            
            # Get current goals and alerts
            current_goals = self.goals.get(campaign_id, [])
            current_alerts = [alert for alert in self.alerts.get(campaign_id, []) 
                            if not alert.is_acknowledged]
            
            # Calculate budget information
            total_budget = float(campaign_info.get('budget', 0))
            total_spent = float(campaign_info.get('total_spent', 0))
            budget_remaining = max(0, total_budget - total_spent)
            
            # Create snapshot
            snapshot = CampaignSnapshot(
                campaign_id=campaign_id,
                timestamp=datetime.now(),
                status=CampaignStatus(campaign_info.get('status', 'active')),
                metrics=current_metrics,
                channel_metrics=dict(channel_metrics),
                goals_progress=current_goals.copy(),
                alerts=current_alerts.copy(),
                budget_spent=total_spent,
                budget_remaining=budget_remaining
            )
            
            # Store snapshot
            self.snapshots[campaign_id].append(snapshot)
            
            # Keep only last 100 snapshots per campaign
            if len(self.snapshots[campaign_id]) > 100:
                self.snapshots[campaign_id] = self.snapshots[campaign_id][-100:]
            
            logger.info(f"Created performance snapshot for campaign {campaign_id}")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to create performance snapshot: {e}")
            return None
    
    def get_active_alerts(self, campaign_id: Optional[str] = None) -> List[PerformanceAlert]:
        """Get active (unacknowledged) alerts."""
        try:
            active_alerts = []
            
            if campaign_id:
                campaign_alerts = self.alerts.get(campaign_id, [])
                active_alerts.extend([alert for alert in campaign_alerts if not alert.is_acknowledged])
            else:
                for alerts_list in self.alerts.values():
                    active_alerts.extend([alert for alert in alerts_list if not alert.is_acknowledged])
            
            # Sort by severity and timestamp
            severity_order = {'critical': 0, 'warning': 1, 'info': 2}
            active_alerts.sort(key=lambda x: (severity_order.get(x.severity, 3), x.timestamp), reverse=True)
            
            return active_alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge a performance alert."""
        try:
            for campaign_alerts in self.alerts.values():
                for alert in campaign_alerts:
                    if alert.alert_id == alert_id:
                        alert.is_acknowledged = True
                        alert.acknowledged_at = datetime.now()
                        alert.acknowledged_by = acknowledged_by
                        logger.info(f"Acknowledged alert {alert_id}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def get_performance_dashboard_data(self, campaign_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data for multiple campaigns."""
        try:
            target_campaigns = campaign_ids or list(self.campaigns.keys())
            
            dashboard_data = {
                'summary': {
                    'total_campaigns': len(target_campaigns),
                    'active_campaigns': 0,
                    'total_alerts': 0,
                    'critical_alerts': 0,
                    'total_budget': 0,
                    'total_spent': 0
                },
                'campaigns': {},
                'alerts': self.get_active_alerts(),
                'top_performers': [],
                'underperformers': [],
                'trends': {},
                'generated_at': datetime.now().isoformat()
            }
            
            campaign_performances = []
            
            for campaign_id in target_campaigns:
                if campaign_id in self.campaigns:
                    campaign_info = self.campaigns[campaign_id]
                    performance = self.get_campaign_performance(campaign_id)
                    
                    dashboard_data['campaigns'][campaign_id] = {
                        'info': campaign_info,
                        'performance': performance
                    }
                    
                    # Update summary statistics
                    if campaign_info.get('status') == 'active':
                        dashboard_data['summary']['active_campaigns'] += 1
                    
                    dashboard_data['summary']['total_budget'] += float(campaign_info.get('budget', 0))
                    dashboard_data['summary']['total_spent'] += float(campaign_info.get('total_spent', 0))
                    
                    # Collect for performance ranking
                    roas = performance.get('metrics_summary', {}).get(MetricType.ROAS.value, {}).get('current', 0)
                    campaign_performances.append((campaign_id, campaign_info.get('name', campaign_id), roas))
            
            # Count alerts
            dashboard_data['summary']['total_alerts'] = len(dashboard_data['alerts'])
            dashboard_data['summary']['critical_alerts'] = len([a for a in dashboard_data['alerts'] if a.severity == 'critical'])
            
            # Identify top performers and underperformers
            campaign_performances.sort(key=lambda x: x[2], reverse=True)
            
            dashboard_data['top_performers'] = [{
                'campaign_id': cp[0],
                'name': cp[1],
                'roas': cp[2]
            } for cp in campaign_performances[:3]]
            
            dashboard_data['underperformers'] = [{
                'campaign_id': cp[0],
                'name': cp[1],
                'roas': cp[2]
            } for cp in campaign_performances[-3:] if cp[2] < 2.0]  # ROAS below 2.0
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {}


def create_sample_performance_tracker() -> CampaignPerformanceTracker:
    """Create sample campaign performance tracker for demonstration."""
    
    tracker = CampaignPerformanceTracker()
    
    # Create sample campaigns
    sample_campaigns = [
        {
            'id': 'campaign_001',
            'name': 'Digital Marketing Mastery Q1',
            'channels': [CampaignChannel.EMAIL, CampaignChannel.SOCIAL_MEDIA, CampaignChannel.SEARCH_ADS],
            'budget': 50000.0
        },
        {
            'id': 'campaign_002',
            'name': 'SEO Content Strategy Campaign',
            'channels': [CampaignChannel.CONTENT_MARKETING, CampaignChannel.SEARCH_ADS],
            'budget': 30000.0
        },
        {
            'id': 'campaign_003',
            'name': 'Social Media Brand Awareness',
            'channels': [CampaignChannel.SOCIAL_MEDIA, CampaignChannel.DISPLAY_ADS, CampaignChannel.INFLUENCER],
            'budget': 40000.0
        }
    ]
    
    # Register campaigns
    for campaign in sample_campaigns:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() + timedelta(days=30)
        
        # Create sample goals
        goals = [
            CampaignGoal(
                goal_id=f"goal_{campaign['id']}_roas",
                campaign_id=campaign['id'],
                metric_type=MetricType.ROAS,
                target_value=4.0,
                priority="high"
            ),
            CampaignGoal(
                goal_id=f"goal_{campaign['id']}_conv",
                campaign_id=campaign['id'],
                metric_type=MetricType.CONVERSION_RATE,
                target_value=0.05,
                priority="medium"
            )
        ]
        
        tracker.register_campaign(
            campaign['id'],
            campaign['name'],
            campaign['channels'],
            start_date,
            end_date,
            campaign['budget'],
            goals
        )
    
    # Generate sample metrics
    base_time = datetime.now() - timedelta(hours=24)
    
    for campaign in sample_campaigns:
        campaign_id = campaign['id']
        
        for hour in range(24):
            timestamp = base_time + timedelta(hours=hour)
            
            for channel in campaign['channels']:
                # Generate realistic sample metrics with some randomness
                import random
                
                # Base metrics that vary by campaign
                base_multipliers = {
                    'campaign_001': 1.2,  # Higher performing
                    'campaign_002': 1.0,  # Average performing
                    'campaign_003': 0.8   # Lower performing
                }
                
                multiplier = base_multipliers.get(campaign_id, 1.0)
                
                metrics = [
                    CampaignMetric(
                        MetricType.IMPRESSIONS,
                        random.randint(800, 1500) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.CLICKS,
                        random.randint(40, 120) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.CTR,
                        random.uniform(0.03, 0.08) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.CONVERSIONS,
                        random.randint(2, 8) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.CONVERSION_RATE,
                        random.uniform(0.02, 0.06) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.CPC,
                        random.uniform(1.50, 4.00) / multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.ROAS,
                        random.uniform(2.5, 6.0) * multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    ),
                    CampaignMetric(
                        MetricType.COST,
                        random.uniform(200, 500) / multiplier,
                        timestamp,
                        channel,
                        campaign_id
                    )
                ]
                
                for metric in metrics:
                    tracker.record_metric(metric)
    
    return tracker


def run_campaign_performance_demo():
    """
    Run the campaign performance tracker demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("📊 Campaign Performance Tracker Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Real-time performance monitoring")
    print("  • Multi-channel metric aggregation")
    print("  • Goal tracking and achievement monitoring")
    print("  • Anomaly detection and alerting")
    print("  • Performance trend analysis")
    print("  • Comparative campaign analysis")
    print("  • Predictive performance modeling")
    print("  • Automated optimization recommendations")
    
    print("\n📈 Supported Metrics:")
    for metric in list(MetricType)[:8]:  # Show first 8 metrics
        print(f"  • {metric.value}")
    print(f"  • ... and {len(MetricType) - 8} more metrics")
    
    print("\n🚀 Initializing performance tracker...")
    tracker = create_sample_performance_tracker()
    
    print("✅ Tracker initialized with sample data")
    print(f"   • Campaigns registered: {len(tracker.campaigns)}")
    print(f"   • Total metrics recorded: {sum(len(metrics) for metrics in tracker.metrics_history.values())}")
    
    # Display campaign summaries
    print("\n📋 Campaign Performance Summary:")
    for campaign_id, campaign_info in tracker.campaigns.items():
        performance = tracker.get_campaign_performance(campaign_id)
        metrics_summary = performance.get('metrics_summary', {})
        
        roas = metrics_summary.get(MetricType.ROAS.value, {}).get('current', 0)
        ctr = metrics_summary.get(MetricType.CTR.value, {}).get('current', 0)
        conv_rate = metrics_summary.get(MetricType.CONVERSION_RATE.value, {}).get('current', 0)
        
        print(f"\n   📈 {campaign_info['name']}:")
        print(f"      • ROAS: {roas:.2f}x")
        print(f"      • CTR: {ctr*100:.2f}%")
        print(f"      • Conversion Rate: {conv_rate*100:.2f}%")
        print(f"      • Channels: {len(campaign_info['channels'])}")
        
        # Show goals progress
        goals = tracker.goals.get(campaign_id, [])
        achieved_goals = len([g for g in goals if g.is_achieved])
        print(f"      • Goals: {achieved_goals}/{len(goals)} achieved")
    
    # Show active alerts
    active_alerts = tracker.get_active_alerts()
    print(f"\n🚨 Active Alerts: {len(active_alerts)}")
    
    for alert in active_alerts[:3]:  # Show top 3 alerts
        print(f"   • {alert.severity.upper()}: {alert.message}")
    
    # Campaign comparison demo
    if len(tracker.campaigns) >= 2:
        campaign_ids = list(tracker.campaigns.keys())
        comparison = tracker.compare_campaigns(campaign_ids[0], campaign_ids[1])
        
        if comparison:
            print(f"\n📊 Campaign Comparison: {comparison.primary_campaign_id} vs {comparison.comparison_campaign_id}")
            print(f"   • Metrics compared: {comparison.performance_summary['metrics_compared']}")
            print(f"   • Primary wins: {comparison.performance_summary['primary_wins']}")
            print(f"   • Comparison wins: {comparison.performance_summary['comparison_wins']}")
            
            print("   • Top recommendation:")
            for rec in comparison.recommendations[:1]:
                print(f"     - {rec}")
    
    # Dashboard data demo
    dashboard = tracker.get_performance_dashboard_data()
    print(f"\n🎛️  Dashboard Summary:")
    print(f"   • Total campaigns: {dashboard['summary']['total_campaigns']}")
    print(f"   • Active campaigns: {dashboard['summary']['active_campaigns']}")
    print(f"   • Total budget: ${dashboard['summary']['total_budget']:,.2f}")
    print(f"   • Budget utilization: ${dashboard['summary']['total_spent']:,.2f}")
    
    if dashboard['top_performers']:
        print(f"   • Top performer: {dashboard['top_performers'][0]['name']} (ROAS: {dashboard['top_performers'][0]['roas']:.2f}x)")
    
    # Performance snapshot demo
    first_campaign = list(tracker.campaigns.keys())[0]
    snapshot = tracker.create_performance_snapshot(first_campaign)
    
    if snapshot:
        print(f"\n📸 Performance Snapshot ({snapshot.campaign_id}):")
        print(f"   • Timestamp: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   • Status: {snapshot.status.value}")
        print(f"   • Active metrics: {len(snapshot.metrics)}")
        print(f"   • Budget remaining: ${snapshot.budget_remaining:,.2f}")
        print(f"   • Active alerts: {len(snapshot.alerts)}")
    
    print("\n🌟 Advanced Capabilities:")
    print("  • Real-time anomaly detection using statistical analysis")
    print("  • Multi-dimensional performance correlation analysis")
    print("  • Predictive performance modeling and forecasting")
    print("  • Automated optimization recommendations")
    print("  • Cross-campaign performance benchmarking")
    print("  • Goal-oriented performance tracking")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return tracker


if __name__ == "__main__":
    run_campaign_performance_demo()

