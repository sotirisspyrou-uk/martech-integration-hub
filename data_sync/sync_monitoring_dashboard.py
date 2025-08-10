#!/usr/bin/env python3
"""
Sync Monitoring Dashboard - Real-time MarTech Integration Visibility

Comprehensive monitoring and visualization for marketing technology data synchronization.

📊 REAL-TIME SYNC MONITORING 📊
Complete visibility into data flow, performance, and system health.

Author: Sotirios Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

🚀 THE RARE TECHNICAL MARKETING LEADER 🚀
Combining C-suite strategy with hands-on AI implementation.

DISCLAIMER: This is demonstration code showcasing technical capabilities.
"""

import json
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd


class SyncStatus(Enum):
    """Synchronization status"""
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    PAUSED = "paused"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SyncMetrics:
    """Synchronization metrics"""
    source: str = ""
    destination: str = ""
    records_synced: int = 0
    records_failed: int = 0
    sync_rate: float = 0.0
    last_sync: Optional[datetime] = None
    status: SyncStatus = SyncStatus.IDLE
    error_count: int = 0
    data_quality_score: float = 100.0


@dataclass
class SystemAlert:
    """System alert"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    severity: AlertSeverity = AlertSeverity.INFO
    source: str = ""
    message: str = ""
    resolved: bool = False


class SyncMonitoringDashboard:
    """
    Real-time synchronization monitoring and alerting dashboard.
    
    🎯 ENTERPRISE MONITORING:
    - Real-time sync status tracking
    - Performance metrics and KPIs
    - Automated alerting and notifications
    - Historical trend analysis
    - System health monitoring
    
    🔗 Learn more: https://verityai.co
    💼 Connect: https://www.linkedin.com/in/sspyrou/
    """
    
    def __init__(self):
        self.sync_metrics: Dict[str, SyncMetrics] = {}
        self.alerts: List[SystemAlert] = []
        self.performance_history: deque = deque(maxlen=1000)
        self.alert_thresholds = {
            'sync_rate_low': 0.8,
            'error_rate_high': 0.05,
            'data_quality_low': 90.0
        }
    
    def update_sync_metrics(self, source: str, destination: str, 
                           records_synced: int, records_failed: int = 0):
        """Update synchronization metrics"""
        sync_key = f"{source}->{destination}"
        
        if sync_key not in self.sync_metrics:
            self.sync_metrics[sync_key] = SyncMetrics(
                source=source,
                destination=destination
            )
        
        metrics = self.sync_metrics[sync_key]
        metrics.records_synced += records_synced
        metrics.records_failed += records_failed
        metrics.last_sync = datetime.now()
        metrics.sync_rate = records_synced / (records_synced + records_failed) if (records_synced + records_failed) > 0 else 0
        metrics.status = SyncStatus.ACTIVE if records_synced > 0 else SyncStatus.ERROR
        
        # Check for alerts
        self._check_thresholds(sync_key, metrics)
        
        # Record performance
        self.performance_history.append({
            'timestamp': datetime.now(),
            'sync_key': sync_key,
            'records_synced': records_synced,
            'sync_rate': metrics.sync_rate
        })
    
    def _check_thresholds(self, sync_key: str, metrics: SyncMetrics):
        """Check alert thresholds"""
        if metrics.sync_rate < self.alert_thresholds['sync_rate_low']:
            self._create_alert(
                AlertSeverity.WARNING,
                sync_key,
                f"Low sync rate: {metrics.sync_rate:.2%}"
            )
        
        error_rate = metrics.records_failed / max(metrics.records_synced + metrics.records_failed, 1)
        if error_rate > self.alert_thresholds['error_rate_high']:
            self._create_alert(
                AlertSeverity.ERROR,
                sync_key,
                f"High error rate: {error_rate:.2%}"
            )
    
    def _create_alert(self, severity: AlertSeverity, source: str, message: str):
        """Create system alert"""
        alert = SystemAlert(
            severity=severity,
            source=source,
            message=message
        )
        self.alerts.append(alert)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data"""
        total_synced = sum(m.records_synced for m in self.sync_metrics.values())
        total_failed = sum(m.records_failed for m in self.sync_metrics.values())
        active_syncs = sum(1 for m in self.sync_metrics.values() if m.status == SyncStatus.ACTIVE)
        
        recent_alerts = [a for a in self.alerts if not a.resolved and 
                        (datetime.now() - a.timestamp).total_seconds() < 3600]
        
        return {
            'overview': {
                'total_synced': total_synced,
                'total_failed': total_failed,
                'success_rate': total_synced / max(total_synced + total_failed, 1),
                'active_syncs': active_syncs,
                'total_syncs': len(self.sync_metrics)
            },
            'sync_metrics': {k: {
                'source': v.source,
                'destination': v.destination,
                'records_synced': v.records_synced,
                'sync_rate': v.sync_rate,
                'status': v.status.value,
                'last_sync': v.last_sync.isoformat() if v.last_sync else None
            } for k, v in self.sync_metrics.items()},
            'recent_alerts': [{
                'severity': a.severity.value,
                'source': a.source,
                'message': a.message,
                'timestamp': a.timestamp.isoformat()
            } for a in recent_alerts],
            'performance_trends': list(self.performance_history)[-50:]  # Last 50 data points
        }
    
    def generate_report(self) -> str:
        """Generate monitoring report"""
        data = self.get_dashboard_data()
        
        report = f"""
MARTECH SYNC MONITORING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Records Synced: {data['overview']['total_synced']:,}
- Success Rate: {data['overview']['success_rate']:.2%}
- Active Syncs: {data['overview']['active_syncs']}/{data['overview']['total_syncs']}

RECENT ALERTS: {len(data['recent_alerts'])}
"""
        
        for alert in data['recent_alerts'][:5]:
            report += f"- {alert['severity'].upper()}: {alert['message']}\n"
        
        return report


def demo_sync_monitoring():
    """Demo sync monitoring dashboard"""
    print("📊 SYNC MONITORING DASHBOARD DEMO")
    
    dashboard = SyncMonitoringDashboard()
    
    # Simulate sync activity
    sources = ["Salesforce", "HubSpot", "Mailchimp"]
    destinations = ["Data Warehouse", "Analytics", "CRM"]
    
    for i in range(10):
        source = sources[i % len(sources)]
        dest = destinations[i % len(destinations)]
        dashboard.update_sync_metrics(source, dest, 1000 + i * 100, i * 5)
    
    data = dashboard.get_dashboard_data()
    print(f"Success Rate: {data['overview']['success_rate']:.2%}")
    print(f"Recent Alerts: {len(data['recent_alerts'])}")
    
    print("\n🔗 Visit: https://verityai.co")
    print("💼 Connect: https://www.linkedin.com/in/sspyrou/")


if __name__ == "__main__":
    demo_sync_monitoring()
