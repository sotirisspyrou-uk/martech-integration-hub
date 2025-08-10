import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


@dataclass
class MarketingInsight:
    """Represents a marketing insight with metadata."""
    title: str
    description: str
    insight_type: str
    confidence_score: float
    impact_level: str  # low, medium, high
    data_points: int
    time_period: str
    recommendations: List[str]
    metrics: Dict[str, Any]
    created_at: datetime


class AutomatedInsightGenerator:
    """
    Automated marketing insight generation from integrated platform data.
    Identifies trends, anomalies, and actionable recommendations.
    """
    
    def __init__(self):
        self.insights_cache = {}
        self.thresholds = {
            'trend_significance': 0.05,  # p-value threshold
            'anomaly_std_dev': 2.0,      # standard deviations for anomaly detection
            'min_data_points': 7,        # minimum data points for analysis
            'confidence_threshold': 0.7   # minimum confidence for insights
        }
    
    def generate_insights(self, data: Dict[str, pd.DataFrame]) -> List[MarketingInsight]:
        """Generate comprehensive marketing insights from platform data."""
        insights = []
        
        try:
            # Traffic and engagement insights
            if 'analytics' in data:
                insights.extend(self._analyze_traffic_patterns(data['analytics']))
                insights.extend(self._detect_conversion_anomalies(data['analytics']))
            
            # Campaign performance insights
            if 'campaigns' in data:
                insights.extend(self._analyze_campaign_performance(data['campaigns']))
            
            # Lead quality insights
            if 'leads' in data:
                insights.extend(self._analyze_lead_quality_trends(data['leads']))
            
            # Revenue attribution insights
            if 'revenue' in data:
                insights.extend(self._analyze_revenue_attribution(data['revenue']))
            
            # Cross-platform insights
            insights.extend(self._generate_cross_platform_insights(data))
            
            # Filter by confidence threshold
            high_confidence_insights = [
                insight for insight in insights 
                if insight.confidence_score >= self.thresholds['confidence_threshold']
            ]
            
            logger.info(f"Generated {len(high_confidence_insights)} high-confidence insights from {len(insights)} total")
            return sorted(high_confidence_insights, key=lambda x: x.confidence_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    def _analyze_traffic_patterns(self, analytics_data: pd.DataFrame) -> List[MarketingInsight]:
        """Analyze website traffic patterns and trends."""
        insights = []
        
        try:
            if len(analytics_data) < self.thresholds['min_data_points']:
                return insights
            
            # Ensure date column exists and is datetime
            if 'date' in analytics_data.columns:
                analytics_data['date'] = pd.to_datetime(analytics_data['date'])
                analytics_data = analytics_data.sort_values('date')
            
            # Traffic trend analysis
            if 'sessions' in analytics_data.columns:
                trend_insight = self._detect_traffic_trend(analytics_data)
                if trend_insight:
                    insights.append(trend_insight)
            
            # Bounce rate analysis
            if 'bounce_rate' in analytics_data.columns:
                bounce_insight = self._analyze_bounce_rate(analytics_data)
                if bounce_insight:
                    insights.append(bounce_insight)
            
            # Channel performance comparison
            if 'source_medium' in analytics_data.columns:
                channel_insight = self._analyze_channel_performance(analytics_data)
                if channel_insight:
                    insights.append(channel_insight)
            
        except Exception as e:
            logger.error(f"Error analyzing traffic patterns: {e}")
        
        return insights
    
    def _detect_traffic_trend(self, data: pd.DataFrame) -> Optional[MarketingInsight]:
        """Detect significant traffic trends."""
        try:
            sessions = data['sessions'].values
            days = np.arange(len(sessions))
            
            # Linear regression to detect trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(days, sessions)
            
            if p_value < self.thresholds['trend_significance']:
                trend_direction = "increasing" if slope > 0 else "decreasing"
                percentage_change = (slope * len(days) / sessions[0]) * 100
                
                impact_level = "high" if abs(percentage_change) > 20 else "medium" if abs(percentage_change) > 10 else "low"
                
                recommendations = []
                if trend_direction == "decreasing":
                    recommendations = [
                        "Review recent changes to website or marketing campaigns",
                        "Analyze top-performing content and replicate successful strategies",
                        "Consider increasing ad spend on high-performing channels"
                    ]
                else:
                    recommendations = [
                        "Scale successful campaigns to maintain growth momentum",
                        "Ensure website can handle increased traffic load",
                        "Optimize conversion funnels to capitalize on traffic growth"
                    ]
                
                return MarketingInsight(
                    title=f"Traffic Trend: {trend_direction.title()} by {abs(percentage_change):.1f}%",
                    description=f"Website sessions are {trend_direction} with statistical significance (p={p_value:.3f})",
                    insight_type="trend_analysis",
                    confidence_score=1 - p_value,
                    impact_level=impact_level,
                    data_points=len(sessions),
                    time_period=f"{data['date'].min().date()} to {data['date'].max().date()}",
                    recommendations=recommendations,
                    metrics={
                        'slope': slope,
                        'r_squared': r_value**2,
                        'percentage_change': percentage_change,
                        'p_value': p_value
                    },
                    created_at=datetime.now()
                )
            
        except Exception as e:
            logger.error(f"Error detecting traffic trend: {e}")
        
        return None
    
    def _analyze_bounce_rate(self, data: pd.DataFrame) -> Optional[MarketingInsight]:
        """Analyze bounce rate patterns and anomalies."""
        try:
            bounce_rates = data['bounce_rate'].values
            mean_bounce = np.mean(bounce_rates)
            std_bounce = np.std(bounce_rates)
            
            # Find recent anomalies
            recent_data = data.tail(7)  # Last 7 days
            recent_bounce = recent_data['bounce_rate'].mean()
            
            z_score = (recent_bounce - mean_bounce) / std_bounce if std_bounce > 0 else 0
            
            if abs(z_score) > self.thresholds['anomaly_std_dev']:
                anomaly_type = "increased" if z_score > 0 else "decreased"
                impact_level = "high" if abs(z_score) > 3 else "medium"
                
                recommendations = []
                if anomaly_type == "increased":
                    recommendations = [
                        "Review recent website changes or technical issues",
                        "Check page load speeds and mobile responsiveness",
                        "Analyze landing page relevance to traffic sources"
                    ]
                else:
                    recommendations = [
                        "Identify what changes led to improved engagement",
                        "Scale successful content or design improvements",
                        "Monitor this positive trend and maintain best practices"
                    ]
                
                return MarketingInsight(
                    title=f"Bounce Rate Anomaly: {anomaly_type.title()} to {recent_bounce:.1f}%",
                    description=f"Recent bounce rate has {anomaly_type} significantly from the historical average of {mean_bounce:.1f}%",
                    insight_type="anomaly_detection",
                    confidence_score=min(abs(z_score) / 4, 0.95),
                    impact_level=impact_level,
                    data_points=len(bounce_rates),
                    time_period=f"Last 7 days vs historical average",
                    recommendations=recommendations,
                    metrics={
                        'recent_bounce_rate': recent_bounce,
                        'historical_average': mean_bounce,
                        'z_score': z_score,
                        'change_percentage': ((recent_bounce - mean_bounce) / mean_bounce) * 100
                    },
                    created_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error analyzing bounce rate: {e}")
        
        return None
    
    def _analyze_channel_performance(self, data: pd.DataFrame) -> Optional[MarketingInsight]:
        """Analyze performance differences between traffic channels."""
        try:
            if 'source_medium' not in data.columns or 'conversions' not in data.columns:
                return None
            
            # Group by channel and calculate metrics
            channel_metrics = data.groupby('source_medium').agg({
                'sessions': 'sum',
                'conversions': 'sum',
                'bounce_rate': 'mean'
            }).reset_index()
            
            # Calculate conversion rate
            channel_metrics['conversion_rate'] = (
                channel_metrics['conversions'] / channel_metrics['sessions'] * 100
            )
            
            # Find best and worst performing channels
            best_channel = channel_metrics.loc[channel_metrics['conversion_rate'].idxmax()]
            worst_channel = channel_metrics.loc[channel_metrics['conversion_rate'].idxmin()]
            
            performance_gap = best_channel['conversion_rate'] - worst_channel['conversion_rate']
            
            if performance_gap > 1.0:  # More than 1% difference
                recommendations = [
                    f"Increase budget allocation to {best_channel['source_medium']} (highest converting channel)",
                    f"Investigate and optimize {worst_channel['source_medium']} performance",
                    "Review landing page relevance for underperforming channels",
                    "A/B test different messaging for different traffic sources"
                ]
                
                return MarketingInsight(
                    title=f"Channel Performance Gap: {performance_gap:.1f}% difference",
                    description=f"Significant performance difference between channels. {best_channel['source_medium']} converts at {best_channel['conversion_rate']:.2f}% vs {worst_channel['source_medium']} at {worst_channel['conversion_rate']:.2f}%",
                    insight_type="performance_comparison",
                    confidence_score=0.85,
                    impact_level="high" if performance_gap > 3 else "medium",
                    data_points=len(channel_metrics),
                    time_period="Current analysis period",
                    recommendations=recommendations,
                    metrics={
                        'best_channel': best_channel['source_medium'],
                        'best_conversion_rate': best_channel['conversion_rate'],
                        'worst_channel': worst_channel['source_medium'],
                        'worst_conversion_rate': worst_channel['conversion_rate'],
                        'performance_gap': performance_gap
                    },
                    created_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error analyzing channel performance: {e}")
        
        return None
    
    def _detect_conversion_anomalies(self, data: pd.DataFrame) -> List[MarketingInsight]:
        """Detect conversion rate anomalies."""
        insights = []
        
        try:
            if 'conversions' not in data.columns or 'sessions' not in data.columns:
                return insights
            
            # Calculate daily conversion rates
            data['conversion_rate'] = (data['conversions'] / data['sessions']) * 100
            data['conversion_rate'] = data['conversion_rate'].fillna(0)
            
            # Statistical analysis
            mean_conv = data['conversion_rate'].mean()
            std_conv = data['conversion_rate'].std()
            
            # Find days with significant anomalies
            data['z_score'] = (data['conversion_rate'] - mean_conv) / std_conv
            anomalies = data[abs(data['z_score']) > self.thresholds['anomaly_std_dev']]
            
            if len(anomalies) > 0:
                recent_anomalies = anomalies.tail(3)  # Last 3 anomalies
                
                for _, anomaly in recent_anomalies.iterrows():
                    anomaly_type = "spike" if anomaly['z_score'] > 0 else "drop"
                    
                    recommendations = []
                    if anomaly_type == "drop":
                        recommendations = [
                            "Check for technical issues on conversion pages",
                            "Review recent changes to checkout or form processes",
                            "Analyze traffic quality changes"
                        ]
                    else:
                        recommendations = [
                            "Identify what drove the conversion spike",
                            "Scale successful tactics or campaigns",
                            "Document best practices for replication"
                        ]
                    
                    insight = MarketingInsight(
                        title=f"Conversion Rate {anomaly_type.title()}: {anomaly['conversion_rate']:.2f}%",
                        description=f"Conversion rate {anomaly_type} detected on {anomaly['date'].date()} with {abs(anomaly['z_score']):.1f} standard deviations from average",
                        insight_type="conversion_anomaly",
                        confidence_score=min(abs(anomaly['z_score']) / 4, 0.95),
                        impact_level="high" if abs(anomaly['z_score']) > 3 else "medium",
                        data_points=len(data),
                        time_period=str(anomaly['date'].date()),
                        recommendations=recommendations,
                        metrics={
                            'anomaly_conversion_rate': anomaly['conversion_rate'],
                            'average_conversion_rate': mean_conv,
                            'z_score': anomaly['z_score'],
                            'date': anomaly['date'].isoformat()
                        },
                        created_at=datetime.now()
                    )
                    insights.append(insight)
                    
        except Exception as e:
            logger.error(f"Error detecting conversion anomalies: {e}")
        
        return insights
    
    def _analyze_campaign_performance(self, campaign_data: pd.DataFrame) -> List[MarketingInsight]:
        """Analyze marketing campaign performance patterns."""
        insights = []
        
        try:
            if 'campaign_name' not in campaign_data.columns:
                return insights
            
            # Campaign ROI analysis
            if 'spend' in campaign_data.columns and 'revenue' in campaign_data.columns:
                campaign_data['roi'] = (campaign_data['revenue'] / campaign_data['spend'] - 1) * 100
                
                # Find top and bottom performing campaigns
                top_campaigns = campaign_data.nlargest(3, 'roi')
                bottom_campaigns = campaign_data.nsmallest(3, 'roi')
                
                avg_roi = campaign_data['roi'].mean()
                
                # Generate insights for top performers
                if len(top_campaigns) > 0:
                    best_campaign = top_campaigns.iloc[0]
                    
                    insight = MarketingInsight(
                        title=f"Top Campaign: {best_campaign['campaign_name']} ({best_campaign['roi']:.1f}% ROI)",
                        description=f"Campaign significantly outperforming average ROI of {avg_roi:.1f}%",
                        insight_type="campaign_performance",
                        confidence_score=0.9,
                        impact_level="high",
                        data_points=len(campaign_data),
                        time_period="Current campaign period",
                        recommendations=[
                            f"Increase budget allocation to {best_campaign['campaign_name']}",
                            "Analyze and replicate successful campaign elements",
                            "Scale similar campaigns with proven messaging/targeting"
                        ],
                        metrics={
                            'campaign_roi': best_campaign['roi'],
                            'average_roi': avg_roi,
                            'spend': best_campaign['spend'],
                            'revenue': best_campaign['revenue']
                        },
                        created_at=datetime.now()
                    )
                    insights.append(insight)
                
        except Exception as e:
            logger.error(f"Error analyzing campaign performance: {e}")
        
        return insights
    
    def _analyze_lead_quality_trends(self, leads_data: pd.DataFrame) -> List[MarketingInsight]:
        """Analyze lead quality and conversion trends."""
        insights = []
        
        try:
            if 'lead_score' in leads_data.columns and 'created_date' in leads_data.columns:
                leads_data['created_date'] = pd.to_datetime(leads_data['created_date'])
                
                # Weekly lead quality trends
                leads_data['week'] = leads_data['created_date'].dt.to_period('W')
                weekly_quality = leads_data.groupby('week')['lead_score'].mean()
                
                if len(weekly_quality) >= 4:  # At least 4 weeks of data
                    recent_avg = weekly_quality.tail(2).mean()
                    historical_avg = weekly_quality.head(-2).mean()
                    
                    change_pct = ((recent_avg - historical_avg) / historical_avg) * 100
                    
                    if abs(change_pct) > 10:  # More than 10% change
                        trend_type = "improvement" if change_pct > 0 else "decline"
                        
                        recommendations = []
                        if trend_type == "decline":
                            recommendations = [
                                "Review lead generation sources for quality issues",
                                "Tighten lead qualification criteria",
                                "Analyze and optimize lead scoring model"
                            ]
                        else:
                            recommendations = [
                                "Scale lead generation tactics driving quality improvement",
                                "Document successful lead qualification changes",
                                "Increase focus on high-quality lead sources"
                            ]
                        
                        insight = MarketingInsight(
                            title=f"Lead Quality Trend: {change_pct:+.1f}% {trend_type}",
                            description=f"Recent lead quality shows {trend_type} with average score changing from {historical_avg:.1f} to {recent_avg:.1f}",
                            insight_type="lead_quality_trend",
                            confidence_score=0.8,
                            impact_level="high" if abs(change_pct) > 20 else "medium",
                            data_points=len(weekly_quality),
                            time_period="Last 2 weeks vs previous period",
                            recommendations=recommendations,
                            metrics={
                                'recent_average_score': recent_avg,
                                'historical_average_score': historical_avg,
                                'percentage_change': change_pct
                            },
                            created_at=datetime.now()
                        )
                        insights.append(insight)
                        
        except Exception as e:
            logger.error(f"Error analyzing lead quality trends: {e}")
        
        return insights
    
    def _analyze_revenue_attribution(self, revenue_data: pd.DataFrame) -> List[MarketingInsight]:
        """Analyze revenue attribution across channels."""
        insights = []
        
        try:
            if 'channel' in revenue_data.columns and 'revenue' in revenue_data.columns:
                channel_revenue = revenue_data.groupby('channel')['revenue'].sum().sort_values(ascending=False)
                total_revenue = channel_revenue.sum()
                
                # Revenue concentration analysis
                top_3_share = channel_revenue.head(3).sum() / total_revenue * 100
                
                if top_3_share > 80:  # High concentration risk
                    insight = MarketingInsight(
                        title=f"Revenue Concentration Risk: {top_3_share:.1f}% from top 3 channels",
                        description="High revenue concentration in few channels creates dependency risk",
                        insight_type="revenue_attribution",
                        confidence_score=0.85,
                        impact_level="medium",
                        data_points=len(channel_revenue),
                        time_period="Current analysis period",
                        recommendations=[
                            "Diversify marketing channels to reduce dependency",
                            "Invest in developing alternative revenue sources",
                            "Test new channels with small budget allocations"
                        ],
                        metrics={
                            'top_3_concentration': top_3_share,
                            'total_channels': len(channel_revenue),
                            'top_channel_share': (channel_revenue.iloc[0] / total_revenue) * 100
                        },
                        created_at=datetime.now()
                    )
                    insights.append(insight)
                    
        except Exception as e:
            logger.error(f"Error analyzing revenue attribution: {e}")
        
        return insights
    
    def _generate_cross_platform_insights(self, data: Dict[str, pd.DataFrame]) -> List[MarketingInsight]:
        """Generate insights from cross-platform data correlations."""
        insights = []
        
        try:
            # Example: Email engagement vs website conversions
            if 'email_campaigns' in data and 'analytics' in data:
                # Simplified cross-platform correlation analysis
                insight = MarketingInsight(
                    title="Cross-Platform Integration Opportunity",
                    description="Multiple data sources available for comprehensive attribution analysis",
                    insight_type="integration_opportunity",
                    confidence_score=0.7,
                    impact_level="medium",
                    data_points=len(data),
                    time_period="Current analysis period",
                    recommendations=[
                        "Implement unified customer journey tracking",
                        "Set up cross-platform attribution modeling",
                        "Create integrated campaign performance dashboards"
                    ],
                    metrics={
                        'platforms_integrated': len(data),
                        'available_data_sources': list(data.keys())
                    },
                    created_at=datetime.now()
                )
                insights.append(insight)
                
        except Exception as e:
            logger.error(f"Error generating cross-platform insights: {e}")
        
        return insights
    
    def export_insights_report(self, insights: List[MarketingInsight]) -> str:
        """Export insights to a formatted report."""
        try:
            report = ["# Marketing Insights Report", ""]
            report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Total insights: {len(insights)}")
            report.append("")
            
            # Group by impact level
            high_impact = [i for i in insights if i.impact_level == "high"]
            medium_impact = [i for i in insights if i.impact_level == "medium"]
            low_impact = [i for i in insights if i.impact_level == "low"]
            
            for impact_group, title in [(high_impact, "High Impact"), (medium_impact, "Medium Impact"), (low_impact, "Low Impact")]:
                if impact_group:
                    report.append(f"## {title} Insights")
                    report.append("")
                    
                    for insight in impact_group:
                        report.append(f"### {insight.title}")
                        report.append(f"**Confidence:** {insight.confidence_score:.2f}")
                        report.append(f"**Description:** {insight.description}")
                        report.append("")
                        report.append("**Recommendations:**")
                        for rec in insight.recommendations:
                            report.append(f"- {rec}")
                        report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error exporting insights report: {e}")
            return "Error generating report"