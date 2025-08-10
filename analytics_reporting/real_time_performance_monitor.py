"""
Real-Time Performance Monitor for MarTech Integration Hub

Live monitoring of marketing campaigns, KPIs, and performance metrics with
automated alerting and anomaly detection capabilities.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import asyncio
import threading
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, defaultdict
import queue

# Redis for real-time data (optional)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# WebSocket for real-time updates (optional)
try:
    import websockets
    import asyncio
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


class AlertType(Enum):
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    TREND = "trend"
    COMPARISON = "comparison"


@dataclass
class PerformanceMetric:
    """Real-time performance metric definition."""
    name: str
    value: Union[float, int]
    timestamp: datetime
    metric_type: MetricType
    tags: Dict[str, str]
    source: str
    unit: str = "count"
    description: str = ""


@dataclass
class PerformanceAlert:
    """Performance alert with details and severity."""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    alert_type: AlertType
    metric_name: str
    current_value: Union[float, int]
    threshold_value: Optional[Union[float, int]]
    timestamp: datetime
    source: str
    tags: Dict[str, str]
    actions_suggested: List[str]


@dataclass
class MonitoringRule:
    """Rule for monitoring specific metrics."""
    rule_id: str
    metric_name: str
    rule_type: AlertType
    condition: str  # e.g., "greater_than", "less_than", "anomaly"
    threshold: Optional[Union[float, int]]
    window_minutes: int = 5
    sensitivity: float = 0.8
    enabled: bool = True
    tags: Dict[str, str] = None


class RealTimePerformanceMonitor:
    """
    Real-time performance monitoring system for marketing operations.
    
    Provides live metrics tracking, alerting, anomaly detection, and
    performance dashboards for marketing campaigns and KPIs.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        enable_websocket: bool = False,
        websocket_port: int = 8765
    ):
        self.metrics_buffer = deque(maxlen=10000)
        self.alerts_buffer = deque(maxlen=1000)
        self.monitoring_rules = {}
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))
        self.subscribers = []
        self.alert_callbacks = []
        
        # Configuration
        self.monitoring_enabled = True
        self.alert_throttle = {}  # Prevent alert spam
        self.anomaly_models = {}
        
        # Threading for real-time processing
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # Redis setup (optional)
        self.redis_client = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Redis client initialized for real-time monitoring")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}")
        
        # WebSocket setup (optional)
        self.websocket_enabled = enable_websocket and WEBSOCKET_AVAILABLE
        self.websocket_port = websocket_port
        self.websocket_clients = set()
        
        # Default monitoring rules
        self._setup_default_rules()
        
        # Start monitoring
        self.start_monitoring()
    
    def _setup_default_rules(self):
        """Set up default monitoring rules for common marketing metrics."""
        
        default_rules = [
            MonitoringRule(
                rule_id="conversion_rate_low",
                metric_name="conversion_rate",
                rule_type=AlertType.THRESHOLD,
                condition="less_than",
                threshold=0.01,  # Less than 1%
                window_minutes=10,
                tags={"category": "conversions", "priority": "high"}
            ),
            MonitoringRule(
                rule_id="traffic_anomaly",
                metric_name="website_sessions",
                rule_type=AlertType.ANOMALY,
                condition="anomaly",
                threshold=None,
                window_minutes=5,
                sensitivity=0.9,
                tags={"category": "traffic", "priority": "medium"}
            ),
            MonitoringRule(
                rule_id="campaign_spend_high",
                metric_name="campaign_spend",
                rule_type=AlertType.THRESHOLD,
                condition="greater_than",
                threshold=10000,
                window_minutes=60,
                tags={"category": "budget", "priority": "high"}
            ),
            MonitoringRule(
                rule_id="revenue_drop",
                metric_name="revenue",
                rule_type=AlertType.TREND,
                condition="decreasing_trend",
                threshold=0.1,  # 10% decrease
                window_minutes=30,
                tags={"category": "revenue", "priority": "critical"}
            ),
            MonitoringRule(
                rule_id="bounce_rate_high",
                metric_name="bounce_rate",
                rule_type=AlertType.THRESHOLD,
                condition="greater_than",
                threshold=0.7,  # Greater than 70%
                window_minutes=15,
                tags={"category": "engagement", "priority": "medium"}
            )
        ]
        
        for rule in default_rules:
            self.monitoring_rules[rule.rule_id] = rule
    
    def start_monitoring(self):
        """Start the real-time monitoring thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            return
        
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self._monitoring_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Real-time performance monitoring started")
        
        # Start WebSocket server if enabled
        if self.websocket_enabled:
            asyncio.create_task(self._start_websocket_server())
    
    def stop_monitoring(self):
        """Stop the real-time monitoring."""
        self.stop_event.set()
        if self.processing_thread:
            self.processing_thread.join()
        
        logger.info("Real-time performance monitoring stopped")
    
    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        metric_type: MetricType = MetricType.GAUGE,
        source: str = "unknown",
        tags: Optional[Dict[str, str]] = None,
        unit: str = "count",
        description: str = ""
    ):
        """Record a new performance metric."""
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            metric_type=metric_type,
            tags=tags or {},
            source=source,
            unit=unit,
            description=description
        )
        
        # Add to buffer for processing
        self.metrics_buffer.append(metric)
        
        # Store in history
        self.metric_history[name].append(metric)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.lpush(
                    f"metric:{name}",
                    json.dumps(asdict(metric), default=str)
                )
                self.redis_client.expire(f"metric:{name}", 3600)  # 1 hour TTL
            except Exception as e:
                logger.error(f"Failed to store metric in Redis: {e}")
        
        logger.debug(f"Recorded metric: {name} = {value} ({metric_type.value})")
    
    def add_monitoring_rule(self, rule: MonitoringRule):
        """Add a new monitoring rule."""
        self.monitoring_rules[rule.rule_id] = rule
        logger.info(f"Added monitoring rule: {rule.rule_id}")
    
    def remove_monitoring_rule(self, rule_id: str):
        """Remove a monitoring rule."""
        if rule_id in self.monitoring_rules:
            del self.monitoring_rules[rule_id]
            logger.info(f"Removed monitoring rule: {rule_id}")
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add a callback function to be called when alerts are triggered."""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self, metric_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get current values for specified metrics."""
        
        current_metrics = {}
        
        # Get latest values from history
        for name, history in self.metric_history.items():
            if metric_names is None or name in metric_names:
                if history:
                    latest_metric = history[-1]
                    current_metrics[name] = {
                        'value': latest_metric.value,
                        'timestamp': latest_metric.timestamp.isoformat(),
                        'unit': latest_metric.unit,
                        'source': latest_metric.source,
                        'tags': latest_metric.tags
                    }
        
        return current_metrics
    
    def get_metric_history(
        self,
        metric_name: str,
        minutes_back: int = 60
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric."""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
        history = []
        
        if metric_name in self.metric_history:
            for metric in self.metric_history[metric_name]:
                if metric.timestamp >= cutoff_time:
                    history.append({
                        'timestamp': metric.timestamp.isoformat(),
                        'value': metric.value,
                        'tags': metric.tags,
                        'source': metric.source
                    })
        
        return sorted(history, key=lambda x: x['timestamp'])
    
    def get_recent_alerts(self, minutes_back: int = 60) -> List[Dict[str, Any]]:
        """Get recent alerts within specified time window."""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
        recent_alerts = []
        
        for alert in self.alerts_buffer:
            if alert.timestamp >= cutoff_time:
                alert_dict = asdict(alert)
                alert_dict['timestamp'] = alert.timestamp.isoformat()
                alert_dict['severity'] = alert.severity.value
                alert_dict['alert_type'] = alert.alert_type.value
                recent_alerts.append(alert_dict)
        
        return sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread."""
        
        logger.info("Starting real-time monitoring loop")
        
        while not self.stop_event.is_set():
            try:
                # Process metrics in buffer
                self._process_metrics_buffer()
                
                # Check monitoring rules
                self._check_monitoring_rules()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Send real-time updates to subscribers
                self._notify_subscribers()
                
                # Sleep briefly before next iteration
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_metrics_buffer(self):
        """Process metrics from the buffer."""
        
        # Process up to 100 metrics per iteration
        processed = 0
        while self.metrics_buffer and processed < 100:
            try:
                metric = self.metrics_buffer.popleft()
                self._process_single_metric(metric)
                processed += 1
            except IndexError:
                break
            except Exception as e:
                logger.error(f"Error processing metric: {e}")
    
    def _process_single_metric(self, metric: PerformanceMetric):
        """Process a single metric for analysis."""
        
        # Update anomaly detection models
        self._update_anomaly_model(metric)
        
        # Trigger real-time calculations
        self._calculate_derived_metrics(metric)
    
    def _update_anomaly_model(self, metric: PerformanceMetric):
        """Update anomaly detection model for the metric."""
        
        metric_name = metric.name
        
        if metric_name not in self.anomaly_models:
            self.anomaly_models[metric_name] = {
                'values': deque(maxlen=100),
                'mean': 0,
                'std': 1,
                'last_update': datetime.now()
            }
        
        model = self.anomaly_models[metric_name]
        model['values'].append(metric.value)
        model['last_update'] = datetime.now()
        
        # Update statistics if we have enough data
        if len(model['values']) >= 10:
            values_array = np.array(list(model['values']))
            model['mean'] = np.mean(values_array)
            model['std'] = np.std(values_array) or 1  # Avoid division by zero
    
    def _calculate_derived_metrics(self, metric: PerformanceMetric):
        """Calculate derived metrics based on incoming data."""
        
        # Example: Calculate rates and ratios
        if metric.name == "website_sessions":
            self._calculate_session_rate(metric)
        elif metric.name == "conversions":
            self._calculate_conversion_metrics(metric)
        elif metric.name == "campaign_spend":
            self._calculate_spend_metrics(metric)
    
    def _calculate_session_rate(self, metric: PerformanceMetric):
        """Calculate session rate from session data."""
        
        # Get last hour of sessions
        recent_sessions = [
            m for m in self.metric_history["website_sessions"]
            if m.timestamp >= datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_sessions) >= 2:
            session_rate = len(recent_sessions) / 60  # Sessions per minute
            
            self.record_metric(
                name="session_rate",
                value=session_rate,
                metric_type=MetricType.RATE,
                source="derived",
                unit="sessions/min",
                description="Website sessions per minute"
            )
    
    def _calculate_conversion_metrics(self, metric: PerformanceMetric):
        """Calculate conversion-related metrics."""
        
        # Calculate conversion rate if we have both conversions and sessions
        recent_conversions = sum(
            m.value for m in self.metric_history["conversions"]
            if m.timestamp >= datetime.now() - timedelta(minutes=30)
        )
        
        recent_sessions = sum(
            m.value for m in self.metric_history["website_sessions"]
            if m.timestamp >= datetime.now() - timedelta(minutes=30)
        )
        
        if recent_sessions > 0:
            conversion_rate = recent_conversions / recent_sessions
            
            self.record_metric(
                name="conversion_rate",
                value=conversion_rate,
                metric_type=MetricType.GAUGE,
                source="derived",
                unit="ratio",
                description="Conversion rate (conversions/sessions)"
            )
    
    def _calculate_spend_metrics(self, metric: PerformanceMetric):
        """Calculate spend-related metrics."""
        
        # Calculate daily spend rate
        today_spend = sum(
            m.value for m in self.metric_history["campaign_spend"]
            if m.timestamp.date() == datetime.now().date()
        )
        
        hours_elapsed = datetime.now().hour + 1
        daily_spend_rate = today_spend / max(hours_elapsed, 1) * 24
        
        self.record_metric(
            name="daily_spend_rate",
            value=daily_spend_rate,
            metric_type=MetricType.GAUGE,
            source="derived",
            unit="currency",
            description="Projected daily spend rate"
        )
    
    def _check_monitoring_rules(self):
        """Check all monitoring rules against current metrics."""
        
        for rule_id, rule in self.monitoring_rules.items():
            if not rule.enabled:
                continue
            
            try:
                alert = self._evaluate_rule(rule)
                if alert:
                    self._trigger_alert(alert)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {e}")
    
    def _evaluate_rule(self, rule: MonitoringRule) -> Optional[PerformanceAlert]:
        """Evaluate a single monitoring rule."""
        
        metric_name = rule.metric_name
        
        if metric_name not in self.metric_history:
            return None
        
        # Get recent data within the window
        window_start = datetime.now() - timedelta(minutes=rule.window_minutes)
        recent_metrics = [
            m for m in self.metric_history[metric_name]
            if m.timestamp >= window_start
        ]
        
        if not recent_metrics:
            return None
        
        # Evaluate based on rule type
        if rule.rule_type == AlertType.THRESHOLD:
            return self._evaluate_threshold_rule(rule, recent_metrics)
        elif rule.rule_type == AlertType.ANOMALY:
            return self._evaluate_anomaly_rule(rule, recent_metrics)
        elif rule.rule_type == AlertType.TREND:
            return self._evaluate_trend_rule(rule, recent_metrics)
        
        return None
    
    def _evaluate_threshold_rule(
        self,
        rule: MonitoringRule,
        recent_metrics: List[PerformanceMetric]
    ) -> Optional[PerformanceAlert]:
        """Evaluate threshold-based rule."""
        
        current_value = recent_metrics[-1].value
        
        # Check threshold condition
        alert_triggered = False
        if rule.condition == "greater_than" and current_value > rule.threshold:
            alert_triggered = True
        elif rule.condition == "less_than" and current_value < rule.threshold:
            alert_triggered = True
        elif rule.condition == "equals" and current_value == rule.threshold:
            alert_triggered = True
        
        if alert_triggered:
            severity = self._determine_severity(rule, current_value)
            
            return PerformanceAlert(
                alert_id=f"{rule.rule_id}_{int(datetime.now().timestamp())}",
                title=f"{rule.metric_name} threshold exceeded",
                description=f"{rule.metric_name} is {current_value} which is {rule.condition} {rule.threshold}",
                severity=severity,
                alert_type=rule.rule_type,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold_value=rule.threshold,
                timestamp=datetime.now(),
                source="monitoring_rule",
                tags=rule.tags or {},
                actions_suggested=self._suggest_actions(rule, current_value)
            )
        
        return None
    
    def _evaluate_anomaly_rule(
        self,
        rule: MonitoringRule,
        recent_metrics: List[PerformanceMetric]
    ) -> Optional[PerformanceAlert]:
        """Evaluate anomaly-based rule."""
        
        metric_name = rule.metric_name
        
        if metric_name not in self.anomaly_models:
            return None
        
        model = self.anomaly_models[metric_name]
        current_value = recent_metrics[-1].value
        
        # Calculate z-score
        if model['std'] > 0:
            z_score = abs(current_value - model['mean']) / model['std']
            
            # Threshold based on sensitivity
            anomaly_threshold = (1 - rule.sensitivity) * 3 + rule.sensitivity * 2
            
            if z_score > anomaly_threshold:
                severity = AlertSeverity.HIGH if z_score > 3 else AlertSeverity.MEDIUM
                
                return PerformanceAlert(
                    alert_id=f"{rule.rule_id}_{int(datetime.now().timestamp())}",
                    title=f"{rule.metric_name} anomaly detected",
                    description=f"{rule.metric_name} value {current_value} is {z_score:.2f} standard deviations from normal",
                    severity=severity,
                    alert_type=rule.rule_type,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold_value=None,
                    timestamp=datetime.now(),
                    source="anomaly_detection",
                    tags=rule.tags or {},
                    actions_suggested=self._suggest_anomaly_actions(rule, z_score)
                )
        
        return None
    
    def _evaluate_trend_rule(
        self,
        rule: MonitoringRule,
        recent_metrics: List[PerformanceMetric]
    ) -> Optional[PerformanceAlert]:
        """Evaluate trend-based rule."""
        
        if len(recent_metrics) < 5:  # Need minimum data points
            return None
        
        # Calculate trend
        values = [m.value for m in recent_metrics]
        x = np.arange(len(values))
        
        # Simple linear regression
        slope = np.polyfit(x, values, 1)[0]
        
        # Check for significant trend
        recent_avg = np.mean(values[-3:])
        earlier_avg = np.mean(values[:3])
        
        if earlier_avg > 0:
            trend_change = (recent_avg - earlier_avg) / earlier_avg
            
            alert_triggered = False
            if rule.condition == "decreasing_trend" and trend_change < -rule.threshold:
                alert_triggered = True
            elif rule.condition == "increasing_trend" and trend_change > rule.threshold:
                alert_triggered = True
            
            if alert_triggered:
                severity = AlertSeverity.HIGH if abs(trend_change) > 0.3 else AlertSeverity.MEDIUM
                
                return PerformanceAlert(
                    alert_id=f"{rule.rule_id}_{int(datetime.now().timestamp())}",
                    title=f"{rule.metric_name} trend alert",
                    description=f"{rule.metric_name} shows {trend_change:.1%} change over {rule.window_minutes} minutes",
                    severity=severity,
                    alert_type=rule.rule_type,
                    metric_name=rule.metric_name,
                    current_value=recent_metrics[-1].value,
                    threshold_value=rule.threshold,
                    timestamp=datetime.now(),
                    source="trend_analysis",
                    tags=rule.tags or {},
                    actions_suggested=self._suggest_trend_actions(rule, trend_change)
                )
        
        return None
    
    def _determine_severity(self, rule: MonitoringRule, current_value: float) -> AlertSeverity:
        """Determine alert severity based on threshold deviation."""
        
        if not rule.threshold:
            return AlertSeverity.MEDIUM
        
        deviation = abs(current_value - rule.threshold) / rule.threshold
        
        if deviation > 0.5:
            return AlertSeverity.CRITICAL
        elif deviation > 0.2:
            return AlertSeverity.HIGH
        elif deviation > 0.1:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _suggest_actions(self, rule: MonitoringRule, current_value: float) -> List[str]:
        """Suggest actions based on the triggered rule."""
        
        actions = []
        
        if rule.metric_name == "conversion_rate":
            if rule.condition == "less_than":
                actions = [
                    "Review landing page performance and user experience",
                    "Check if there are technical issues affecting conversions",
                    "Analyze traffic quality and source effectiveness",
                    "A/B test different call-to-action elements"
                ]
        elif rule.metric_name == "campaign_spend":
            if rule.condition == "greater_than":
                actions = [
                    "Review campaign budget settings and daily limits",
                    "Check for bid strategy issues or unexpected competition",
                    "Verify campaign targeting and audience settings",
                    "Consider pausing underperforming ad groups"
                ]
        elif rule.metric_name == "bounce_rate":
            if rule.condition == "greater_than":
                actions = [
                    "Improve page load speed and mobile responsiveness",
                    "Review content relevance to traffic sources",
                    "Optimize page layout and user experience",
                    "Check for broken links or technical issues"
                ]
        else:
            actions = [
                f"Investigate {rule.metric_name} performance",
                "Review recent changes that might have affected this metric",
                "Check data source integrity and accuracy"
            ]
        
        return actions
    
    def _suggest_anomaly_actions(self, rule: MonitoringRule, z_score: float) -> List[str]:
        """Suggest actions for anomaly alerts."""
        
        return [
            f"Investigate unusual {rule.metric_name} pattern (z-score: {z_score:.2f})",
            "Check for external factors or events affecting performance",
            "Verify data accuracy and collection processes",
            "Consider adjusting monitoring sensitivity if this is expected behavior"
        ]
    
    def _suggest_trend_actions(self, rule: MonitoringRule, trend_change: float) -> List[str]:
        """Suggest actions for trend alerts."""
        
        if trend_change < 0:
            return [
                f"Address declining {rule.metric_name} trend ({trend_change:.1%} decrease)",
                "Identify root causes for the negative trend",
                "Implement corrective measures to reverse the decline"
            ]
        else:
            return [
                f"Monitor positive {rule.metric_name} trend ({trend_change:.1%} increase)",
                "Identify factors contributing to positive trend",
                "Scale successful strategies to maintain growth"
            ]
    
    def _trigger_alert(self, alert: PerformanceAlert):
        """Trigger an alert and notify all subscribers."""
        
        # Check alert throttling to prevent spam
        throttle_key = f"{alert.metric_name}_{alert.alert_type.value}"
        last_alert_time = self.alert_throttle.get(throttle_key)
        
        if last_alert_time and datetime.now() - last_alert_time < timedelta(minutes=5):
            return  # Skip this alert due to throttling
        
        self.alert_throttle[throttle_key] = datetime.now()
        
        # Add to alerts buffer
        self.alerts_buffer.append(alert)
        
        # Call all alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        logger.warning(
            f"ALERT: {alert.title} - {alert.description} "
            f"(Severity: {alert.severity.value})"
        )
    
    def _cleanup_old_data(self):
        """Clean up old data to prevent memory issues."""
        
        # Clean up old alerts (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Remove old alerts
        while self.alerts_buffer and self.alerts_buffer[0].timestamp < cutoff_time:
            self.alerts_buffer.popleft()
        
        # Clean up alert throttle entries
        expired_throttles = [
            key for key, timestamp in self.alert_throttle.items()
            if datetime.now() - timestamp > timedelta(hours=1)
        ]
        for key in expired_throttles:
            del self.alert_throttle[key]
    
    def _notify_subscribers(self):
        """Send real-time updates to all subscribers."""
        
        if not self.subscribers and not self.websocket_clients:
            return
        
        # Prepare update payload
        update_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.get_current_metrics(),
            'recent_alerts': self.get_recent_alerts(minutes_back=5),
            'system_status': 'healthy' if self.monitoring_enabled else 'disabled'
        }
        
        # Notify WebSocket clients
        if self.websocket_clients:
            asyncio.create_task(self._broadcast_websocket_update(update_data))
        
        # Notify other subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(update_data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates."""
        
        if not WEBSOCKET_AVAILABLE:
            logger.warning("WebSocket not available, skipping server start")
            return
        
        async def handle_client(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"WebSocket client connected from {websocket.remote_address}")
            
            try:
                await websocket.wait_closed()
            finally:
                self.websocket_clients.remove(websocket)
                logger.info(f"WebSocket client disconnected from {websocket.remote_address}")
        
        try:
            server = await websockets.serve(handle_client, "localhost", self.websocket_port)
            logger.info(f"WebSocket server started on port {self.websocket_port}")
            await server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
    
    async def _broadcast_websocket_update(self, data: Dict[str, Any]):
        """Broadcast update to all WebSocket clients."""
        
        if not self.websocket_clients:
            return
        
        message = json.dumps(data)
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self.websocket_clients.copy():
            try:
                await client.send(message)
            except Exception:
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.websocket_clients.discard(client)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'active_rules': len([r for r in self.monitoring_rules.values() if r.enabled]),
            'total_rules': len(self.monitoring_rules),
            'metrics_tracked': len(self.metric_history),
            'alerts_in_buffer': len(self.alerts_buffer),
            'subscribers': len(self.subscribers),
            'websocket_clients': len(self.websocket_clients) if self.websocket_clients else 0,
            'redis_connected': self.redis_client is not None,
            'processing_thread_active': self.processing_thread and self.processing_thread.is_alive(),
            'last_cleanup': datetime.now().isoformat()
        }
    
    def generate_performance_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Generate performance summary for the specified time period."""
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        summary = {
            'period': f"Last {hours_back} hours",
            'generated_at': datetime.now().isoformat(),
            'metrics_summary': {},
            'alerts_summary': {},
            'top_issues': []
        }
        
        # Analyze metrics
        for metric_name, history in self.metric_history.items():
            recent_data = [m for m in history if m.timestamp >= cutoff_time]
            
            if recent_data:
                values = [m.value for m in recent_data]
                summary['metrics_summary'][metric_name] = {
                    'current_value': recent_data[-1].value,
                    'min_value': min(values),
                    'max_value': max(values),
                    'avg_value': np.mean(values),
                    'data_points': len(values),
                    'last_updated': recent_data[-1].timestamp.isoformat()
                }
        
        # Analyze alerts
        recent_alerts = [a for a in self.alerts_buffer if a.timestamp >= cutoff_time]
        
        if recent_alerts:
            alert_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for alert in recent_alerts:
                alert_counts[alert.metric_name] += 1
                severity_counts[alert.severity.value] += 1
            
            summary['alerts_summary'] = {
                'total_alerts': len(recent_alerts),
                'by_metric': dict(alert_counts),
                'by_severity': dict(severity_counts),
                'most_recent': asdict(recent_alerts[-1]) if recent_alerts else None
            }
            
            # Identify top issues
            summary['top_issues'] = [
                {'metric': metric, 'alert_count': count}
                for metric, count in sorted(alert_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        
        return summary


# Utility functions and example usage

def create_sample_alert_callback(name: str = "Default") -> Callable[[PerformanceAlert], None]:
    """Create a sample alert callback function."""
    
    def alert_callback(alert: PerformanceAlert):
        print(f"[{name}] ALERT: {alert.severity.value.upper()} - {alert.title}")
        print(f"  Metric: {alert.metric_name} = {alert.current_value}")
        print(f"  Time: {alert.timestamp}")
        print(f"  Actions: {', '.join(alert.actions_suggested[:2])}")
        print()
    
    return alert_callback


def simulate_marketing_metrics(monitor: RealTimePerformanceMonitor, duration_minutes: int = 5):
    """Simulate realistic marketing metrics for demonstration."""
    
    import random
    import time
    
    print(f"🎭 Simulating marketing metrics for {duration_minutes} minutes...")
    
    start_time = time.time()
    
    while time.time() - start_time < duration_minutes * 60:
        # Website sessions (varying throughout the day)
        base_sessions = 1000
        sessions = base_sessions + random.randint(-200, 400)
        monitor.record_metric(
            name="website_sessions",
            value=sessions,
            metric_type=MetricType.COUNTER,
            source="google_analytics",
            unit="count"
        )
        
        # Conversions (related to sessions)
        conversion_rate = random.uniform(0.01, 0.05)  # 1-5%
        conversions = int(sessions * conversion_rate)
        monitor.record_metric(
            name="conversions",
            value=conversions,
            metric_type=MetricType.COUNTER,
            source="google_analytics",
            unit="count"
        )
        
        # Campaign spend
        spend = random.uniform(500, 2000)
        monitor.record_metric(
            name="campaign_spend",
            value=spend,
            metric_type=MetricType.GAUGE,
            source="ad_platform",
            unit="currency"
        )
        
        # Bounce rate
        bounce_rate = random.uniform(0.3, 0.8)
        monitor.record_metric(
            name="bounce_rate",
            value=bounce_rate,
            metric_type=MetricType.GAUGE,
            source="google_analytics",
            unit="ratio"
        )
        
        # Revenue
        revenue = random.uniform(5000, 15000)
        monitor.record_metric(
            name="revenue",
            value=revenue,
            metric_type=MetricType.GAUGE,
            source="ecommerce_platform",
            unit="currency"
        )
        
        # Occasionally create anomalies for testing
        if random.random() < 0.1:  # 10% chance
            # Simulate conversion rate drop
            monitor.record_metric(
                name="conversion_rate",
                value=0.005,  # Very low conversion rate
                metric_type=MetricType.GAUGE,
                source="analytics",
                unit="ratio"
            )
        
        if random.random() < 0.05:  # 5% chance
            # Simulate high spend
            monitor.record_metric(
                name="campaign_spend",
                value=15000,  # High spend
                metric_type=MetricType.GAUGE,
                source="ad_platform",
                unit="currency"
            )
        
        time.sleep(10)  # Wait 10 seconds between metrics
    
    print("✅ Metric simulation completed")


def run_real_time_monitoring_demo():
    """
    Demonstration of real-time performance monitoring capabilities.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("📊 MarTech Real-Time Performance Monitor Demo")
    print("=" * 50)
    
    # Initialize monitor
    monitor = RealTimePerformanceMonitor()
    
    # Add alert callback
    alert_callback = create_sample_alert_callback("Demo Alert Handler")
    monitor.add_alert_callback(alert_callback)
    
    print("🚀 Real-time monitoring started")
    print("📋 Active monitoring rules:")
    for rule_id, rule in monitor.monitoring_rules.items():
        print(f"  - {rule_id}: {rule.metric_name} ({rule.rule_type.value})")
    
    print("\n📊 Starting metric simulation...")
    
    # Simulate metrics for 2 minutes
    simulate_marketing_metrics(monitor, duration_minutes=2)
    
    # Get current status
    print("\n📈 Monitoring Status:")
    status = monitor.get_monitoring_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Get performance summary
    print("\n📋 Performance Summary:")
    summary = monitor.generate_performance_summary(hours_back=1)
    print(f"  Total alerts: {summary['alerts_summary'].get('total_alerts', 0)}")
    print(f"  Metrics tracked: {len(summary['metrics_summary'])}")
    
    if summary['top_issues']:
        print("\n⚠️  Top Issues:")
        for issue in summary['top_issues']:
            print(f"    - {issue['metric']}: {issue['alert_count']} alerts")
    
    # Show recent metrics
    print("\n📊 Current Metrics:")
    current_metrics = monitor.get_current_metrics()
    for name, data in current_metrics.items():
        print(f"  {name}: {data['value']} {data['unit']} (from {data['source']})")
    
    # Show recent alerts
    print("\n🚨 Recent Alerts:")
    recent_alerts = monitor.get_recent_alerts(minutes_back=10)
    if recent_alerts:
        for alert in recent_alerts[-3:]:  # Show last 3 alerts
            print(f"  {alert['severity'].upper()}: {alert['title']}")
            print(f"    {alert['description']}")
    else:
        print("  No recent alerts")
    
    print("\n💼 Portfolio: https://verityai.co")
    print("🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("\n⏹️  Stopping monitor...")
    
    # Stop monitoring
    monitor.stop_monitoring()
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    run_real_time_monitoring_demo()