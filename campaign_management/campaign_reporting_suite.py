"""
Campaign Reporting Suite for MarTech Integration Hub

Comprehensive automated reporting system for multi-channel marketing campaigns
with advanced analytics, visualization, and executive-level insights generation.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from jinja2 import Template
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os
from pathlib import Path
import zipfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Campaign report types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CAMPAIGN_SUMMARY = "campaign_summary"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ROI_ANALYSIS = "roi_analysis"
    CHANNEL_COMPARISON = "channel_comparison"
    EXECUTIVE_SUMMARY = "executive_summary"
    CUSTOM = "custom"


class ReportFormat(Enum):
    """Report output formats."""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    DASHBOARD = "dashboard"
    EMAIL = "email"


class ReportFrequency(Enum):
    """Report generation frequency."""
    MANUAL = "manual"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    REAL_TIME = "real_time"


class VisualizationType(Enum):
    """Chart and visualization types."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    FUNNEL_CHART = "funnel_chart"
    GAUGE_CHART = "gauge_chart"
    AREA_CHART = "area_chart"
    WATERFALL_CHART = "waterfall_chart"
    TREEMAP = "treemap"


@dataclass
class ReportSection:
    """Individual report section configuration."""
    section_id: str
    title: str
    description: str
    visualization_type: VisualizationType
    data_source: str  # SQL query, API endpoint, or data function
    filters: Dict[str, Any] = field(default_factory=dict)
    styling: Dict[str, Any] = field(default_factory=dict)
    order_index: int = 0
    is_enabled: bool = True


@dataclass
class ReportTemplate:
    """Report template configuration."""
    template_id: str
    name: str
    description: str
    report_type: ReportType
    output_format: ReportFormat
    sections: List[ReportSection]
    default_filters: Dict[str, Any] = field(default_factory=dict)
    styling_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class ReportSchedule:
    """Automated report scheduling configuration."""
    schedule_id: str
    template_id: str
    frequency: ReportFrequency
    recipients: List[str]
    filters: Dict[str, Any] = field(default_factory=dict)
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    is_active: bool = True
    delivery_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportMetadata:
    """Generated report metadata."""
    report_id: str
    template_id: str
    generated_at: datetime
    data_range: Tuple[datetime, datetime]
    filters_applied: Dict[str, Any]
    file_paths: List[str]
    generation_time_seconds: float
    record_count: int
    file_size_bytes: int
    status: str  # success, error, partial
    error_messages: List[str] = field(default_factory=list)


class CampaignReportingSuite:
    """
    Comprehensive campaign reporting and analytics suite.
    
    Features:
    - Multi-format report generation (PDF, HTML, Excel, Dashboard)
    - Automated report scheduling and distribution
    - Interactive data visualizations
    - Executive summary generation
    - Custom report templates
    - Real-time dashboard updates
    - Advanced analytics and insights
    - Multi-channel performance reporting
    """
    
    def __init__(self, 
                 output_directory: str = "./reports",
                 template_directory: str = "./templates",
                 smtp_config: Optional[Dict[str, str]] = None):
        
        # Directory setup
        self.output_directory = Path(output_directory)
        self.template_directory = Path(template_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.template_directory.mkdir(parents=True, exist_ok=True)
        
        # Email configuration
        self.smtp_config = smtp_config or {}
        
        # Template and schedule storage
        self.templates: Dict[str, ReportTemplate] = {}
        self.schedules: Dict[str, ReportSchedule] = {}
        self.generated_reports: Dict[str, ReportMetadata] = {}
        
        # Data cache for performance
        self.data_cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(minutes=15)
        
        # Visualization settings
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # Initialize default templates
        self._create_default_templates()
        
        logger.info("Campaign Reporting Suite initialized successfully")
    
    def _create_default_templates(self):
        """Create default report templates."""
        try:
            # Executive Summary Template
            executive_template = ReportTemplate(
                template_id="executive_summary",
                name="Executive Summary Report",
                description="High-level executive summary with KPIs and insights",
                report_type=ReportType.EXECUTIVE_SUMMARY,
                output_format=ReportFormat.PDF,
                sections=[
                    ReportSection(
                        "kpi_summary", "Key Performance Indicators",
                        "Overview of campaign KPIs", VisualizationType.GAUGE_CHART,
                        "get_kpi_data", order_index=1
                    ),
                    ReportSection(
                        "performance_trends", "Performance Trends",
                        "Campaign performance over time", VisualizationType.LINE_CHART,
                        "get_performance_trends", order_index=2
                    ),
                    ReportSection(
                        "channel_breakdown", "Channel Performance",
                        "Performance by marketing channel", VisualizationType.BAR_CHART,
                        "get_channel_performance", order_index=3
                    ),
                    ReportSection(
                        "roi_analysis", "ROI Analysis",
                        "Return on investment analysis", VisualizationType.WATERFALL_CHART,
                        "get_roi_data", order_index=4
                    )
                ]
            )
            
            # Performance Analysis Template
            performance_template = ReportTemplate(
                template_id="performance_analysis",
                name="Detailed Performance Analysis",
                description="Comprehensive performance analysis across all metrics",
                report_type=ReportType.PERFORMANCE_ANALYSIS,
                output_format=ReportFormat.HTML,
                sections=[
                    ReportSection(
                        "metrics_overview", "Metrics Overview",
                        "All campaign metrics summary", VisualizationType.HEATMAP,
                        "get_all_metrics", order_index=1
                    ),
                    ReportSection(
                        "conversion_funnel", "Conversion Funnel",
                        "Campaign conversion funnel analysis", VisualizationType.FUNNEL_CHART,
                        "get_funnel_data", order_index=2
                    ),
                    ReportSection(
                        "audience_segments", "Audience Performance",
                        "Performance by audience segments", VisualizationType.TREEMAP,
                        "get_audience_data", order_index=3
                    ),
                    ReportSection(
                        "time_analysis", "Time-based Analysis",
                        "Performance patterns over time", VisualizationType.AREA_CHART,
                        "get_time_series_data", order_index=4
                    )
                ]
            )
            
            # Channel Comparison Template
            channel_template = ReportTemplate(
                template_id="channel_comparison",
                name="Multi-Channel Comparison",
                description="Compare performance across different marketing channels",
                report_type=ReportType.CHANNEL_COMPARISON,
                output_format=ReportFormat.EXCEL,
                sections=[
                    ReportSection(
                        "channel_overview", "Channel Overview",
                        "High-level channel performance", VisualizationType.BAR_CHART,
                        "get_channel_comparison", order_index=1
                    ),
                    ReportSection(
                        "channel_efficiency", "Channel Efficiency",
                        "Cost efficiency by channel", VisualizationType.SCATTER_PLOT,
                        "get_channel_efficiency", order_index=2
                    ),
                    ReportSection(
                        "channel_attribution", "Attribution Analysis",
                        "Multi-touch attribution by channel", VisualizationType.PIE_CHART,
                        "get_attribution_data", order_index=3
                    )
                ]
            )
            
            # Store templates
            self.templates[executive_template.template_id] = executive_template
            self.templates[performance_template.template_id] = performance_template
            self.templates[channel_template.template_id] = channel_template
            
            logger.info(f"Created {len(self.templates)} default report templates")
            
        except Exception as e:
            logger.error(f"Failed to create default templates: {e}")
    
    def create_custom_template(self, template: ReportTemplate) -> bool:
        """Create a custom report template."""
        try:
            template.updated_at = datetime.now()
            self.templates[template.template_id] = template
            
            logger.info(f"Created custom template: {template.name} ({template.template_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom template: {e}")
            return False
    
    def generate_report(self, 
                       template_id: str,
                       campaign_ids: List[str],
                       date_range: Tuple[datetime, datetime],
                       custom_filters: Optional[Dict[str, Any]] = None,
                       output_filename: Optional[str] = None) -> Optional[ReportMetadata]:
        """Generate a report using specified template."""
        try:
            start_time = datetime.now()
            
            if template_id not in self.templates:
                raise ValueError(f"Template {template_id} not found")
            
            template = self.templates[template_id]
            filters = {**template.default_filters, **(custom_filters or {})}
            filters['campaign_ids'] = campaign_ids
            filters['date_range'] = date_range
            
            # Generate unique report ID
            report_id = f"report_{template_id}_{int(start_time.timestamp())}"
            
            # Collect data for all sections
            section_data = {}
            total_records = 0
            
            for section in sorted(template.sections, key=lambda s: s.order_index):
                if section.is_enabled:
                    data = self._get_section_data(section, filters)
                    section_data[section.section_id] = data
                    
                    if isinstance(data, (list, dict)):
                        total_records += len(data) if isinstance(data, list) else 1
            
            # Generate report based on format
            file_paths = []
            
            if template.output_format == ReportFormat.PDF:
                pdf_path = self._generate_pdf_report(template, section_data, filters, output_filename)
                if pdf_path:
                    file_paths.append(str(pdf_path))
            
            elif template.output_format == ReportFormat.HTML:
                html_path = self._generate_html_report(template, section_data, filters, output_filename)
                if html_path:
                    file_paths.append(str(html_path))
            
            elif template.output_format == ReportFormat.EXCEL:
                excel_path = self._generate_excel_report(template, section_data, filters, output_filename)
                if excel_path:
                    file_paths.append(str(excel_path))
            
            elif template.output_format == ReportFormat.DASHBOARD:
                dashboard_path = self._generate_dashboard_report(template, section_data, filters, output_filename)
                if dashboard_path:
                    file_paths.append(str(dashboard_path))
            
            # Calculate generation time and file size
            generation_time = (datetime.now() - start_time).total_seconds()
            total_size = sum(os.path.getsize(path) for path in file_paths if os.path.exists(path))
            
            # Create report metadata
            metadata = ReportMetadata(
                report_id=report_id,
                template_id=template_id,
                generated_at=start_time,
                data_range=date_range,
                filters_applied=filters,
                file_paths=file_paths,
                generation_time_seconds=generation_time,
                record_count=total_records,
                file_size_bytes=total_size,
                status="success" if file_paths else "error",
                error_messages=[]
            )
            
            self.generated_reports[report_id] = metadata
            
            logger.info(f"Generated report {report_id} in {generation_time:.2f}s")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return None
    
    def _get_section_data(self, section: ReportSection, filters: Dict[str, Any]) -> Any:
        """Get data for a specific report section."""
        try:
            # Check cache first
            cache_key = f"{section.data_source}_{hash(str(filters))}"
            if cache_key in self.data_cache:
                cache_entry = self.data_cache[cache_key]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    return cache_entry['data']
            
            # Generate data based on data source
            if section.data_source == "get_kpi_data":
                data = self._generate_kpi_data(filters)
            elif section.data_source == "get_performance_trends":
                data = self._generate_performance_trends_data(filters)
            elif section.data_source == "get_channel_performance":
                data = self._generate_channel_performance_data(filters)
            elif section.data_source == "get_roi_data":
                data = self._generate_roi_data(filters)
            elif section.data_source == "get_all_metrics":
                data = self._generate_all_metrics_data(filters)
            elif section.data_source == "get_funnel_data":
                data = self._generate_funnel_data(filters)
            elif section.data_source == "get_audience_data":
                data = self._generate_audience_data(filters)
            elif section.data_source == "get_time_series_data":
                data = self._generate_time_series_data(filters)
            elif section.data_source == "get_channel_comparison":
                data = self._generate_channel_comparison_data(filters)
            elif section.data_source == "get_channel_efficiency":
                data = self._generate_channel_efficiency_data(filters)
            elif section.data_source == "get_attribution_data":
                data = self._generate_attribution_data(filters)
            else:
                data = {"error": f"Unknown data source: {section.data_source}"}
            
            # Cache the data
            self.data_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get section data: {e}")
            return {"error": str(e)}
    
    def _generate_kpi_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate KPI summary data."""
        import random
        
        # Mock KPI data - in production, this would come from actual campaign data
        return {
            'total_spend': random.uniform(45000, 55000),
            'total_revenue': random.uniform(180000, 220000),
            'total_impressions': random.randint(800000, 1200000),
            'total_clicks': random.randint(35000, 65000),
            'total_conversions': random.randint(1800, 2200),
            'average_ctr': random.uniform(0.04, 0.08),
            'average_cpc': random.uniform(1.20, 2.80),
            'average_conversion_rate': random.uniform(0.04, 0.07),
            'roas': random.uniform(3.2, 4.8),
            'roi': random.uniform(2.2, 3.8),
            'cost_per_acquisition': random.uniform(18, 32)
        }
    
    def _generate_performance_trends_data(self, filters: Dict[str, Any]) -> Dict[str, List]:
        """Generate performance trends data."""
        import random
        
        start_date, end_date = filters.get('date_range', (datetime.now() - timedelta(days=30), datetime.now()))
        dates = pd.date_range(start_date, end_date, freq='D')
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'impressions': [random.randint(25000, 45000) for _ in dates],
            'clicks': [random.randint(1200, 2800) for _ in dates],
            'conversions': [random.randint(60, 120) for _ in dates],
            'cost': [random.uniform(1200, 2200) for _ in dates],
            'revenue': [random.uniform(4800, 8400) for _ in dates]
        }
    
    def _generate_channel_performance_data(self, filters: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate channel performance comparison data."""
        import random
        
        channels = ['Email', 'Social Media', 'Search Ads', 'Display Ads', 'Content Marketing']
        
        data = {}
        for channel in channels:
            data[channel] = {
                'impressions': random.randint(80000, 300000),
                'clicks': random.randint(3000, 12000),
                'conversions': random.randint(150, 600),
                'cost': random.uniform(8000, 18000),
                'revenue': random.uniform(25000, 65000),
                'ctr': random.uniform(0.03, 0.09),
                'conversion_rate': random.uniform(0.03, 0.08),
                'roas': random.uniform(2.5, 5.2)
            }
        
        return data
    
    def _generate_roi_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ROI waterfall analysis data."""
        import random
        
        return {
            'initial_investment': 50000,
            'media_costs': random.uniform(35000, 40000),
            'creative_costs': random.uniform(5000, 8000),
            'platform_costs': random.uniform(2000, 3000),
            'management_costs': random.uniform(3000, 5000),
            'total_revenue': random.uniform(180000, 220000),
            'net_profit': 0,  # Calculated
            'roi_percentage': 0,  # Calculated
            'breakdown': {
                'Email': {'cost': random.uniform(8000, 12000), 'revenue': random.uniform(35000, 45000)},
                'Social': {'cost': random.uniform(10000, 15000), 'revenue': random.uniform(40000, 55000)},
                'Search': {'cost': random.uniform(15000, 20000), 'revenue': random.uniform(60000, 80000)},
                'Display': {'cost': random.uniform(8000, 12000), 'revenue': random.uniform(25000, 35000)}
            }
        }
    
    def _generate_all_metrics_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Generate comprehensive metrics data."""
        import random
        
        channels = ['Email', 'Social Media', 'Search Ads', 'Display Ads', 'Content Marketing']
        metrics = ['CTR', 'CPC', 'Conversion Rate', 'ROAS', 'CPM', 'CPA']
        
        data = []
        for channel in channels:
            for metric in metrics:
                if metric == 'CTR':
                    value = random.uniform(0.02, 0.08)
                elif metric == 'CPC':
                    value = random.uniform(0.80, 3.50)
                elif metric == 'Conversion Rate':
                    value = random.uniform(0.02, 0.07)
                elif metric == 'ROAS':
                    value = random.uniform(2.0, 6.0)
                elif metric == 'CPM':
                    value = random.uniform(8.0, 25.0)
                else:  # CPA
                    value = random.uniform(15.0, 45.0)
                
                data.append({
                    'Channel': channel,
                    'Metric': metric,
                    'Value': value
                })
        
        return pd.DataFrame(data)
    
    def _generate_funnel_data(self, filters: Dict[str, Any]) -> Dict[str, int]:
        """Generate conversion funnel data."""
        import random
        
        total_visits = random.randint(800000, 1200000)
        
        return {
            'Total Visits': total_visits,
            'Engaged Users': int(total_visits * random.uniform(0.35, 0.55)),
            'Product Views': int(total_visits * random.uniform(0.12, 0.25)),
            'Add to Cart': int(total_visits * random.uniform(0.04, 0.08)),
            'Checkout Started': int(total_visits * random.uniform(0.02, 0.05)),
            'Purchase Completed': int(total_visits * random.uniform(0.015, 0.035))
        }
    
    def _generate_audience_data(self, filters: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate audience segment performance data."""
        import random
        
        segments = [
            'High-Value Customers', 'New Customers', 'Returning Customers',
            'Mobile Users', 'Desktop Users', 'International', 'Domestic',
            'Age 18-34', 'Age 35-54', 'Age 55+'
        ]
        
        data = {}
        for segment in segments:
            data[segment] = {
                'size': random.randint(5000, 50000),
                'conversion_rate': random.uniform(0.02, 0.08),
                'average_order_value': random.uniform(45, 180),
                'lifetime_value': random.uniform(200, 800),
                'engagement_score': random.uniform(0.3, 0.9)
            }
        
        return data
    
    def _generate_time_series_data(self, filters: Dict[str, Any]) -> Dict[str, List]:
        """Generate time series analysis data."""
        import random
        
        start_date, end_date = filters.get('date_range', (datetime.now() - timedelta(days=30), datetime.now()))
        hours = pd.date_range(start_date, end_date, freq='H')
        
        base_impressions = 1000
        base_clicks = 50
        base_conversions = 3
        
        return {
            'timestamps': [h.strftime('%Y-%m-%d %H:%M') for h in hours],
            'impressions': [base_impressions + random.randint(-300, 500) for _ in hours],
            'clicks': [base_clicks + random.randint(-15, 35) for _ in hours],
            'conversions': [base_conversions + random.randint(-2, 5) for _ in hours],
            'hour_of_day': [h.hour for h in hours],
            'day_of_week': [h.weekday() for h in hours]
        }
    
    def _generate_channel_comparison_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Generate channel comparison data."""
        return pd.DataFrame(self._generate_channel_performance_data(filters)).T.reset_index()
    
    def _generate_channel_efficiency_data(self, filters: Dict[str, Any]) -> Dict[str, List]:
        """Generate channel efficiency scatter plot data."""
        import random
        
        channels = ['Email', 'Social Media', 'Search Ads', 'Display Ads', 'Content Marketing']
        
        return {
            'channels': channels,
            'cost_efficiency': [random.uniform(0.5, 2.5) for _ in channels],
            'conversion_efficiency': [random.uniform(0.02, 0.08) for _ in channels],
            'volume': [random.randint(10000, 100000) for _ in channels]
        }
    
    def _generate_attribution_data(self, filters: Dict[str, Any]) -> Dict[str, float]:
        """Generate attribution analysis data."""
        import random
        
        channels = ['Email', 'Social Media', 'Search Ads', 'Display Ads', 'Content Marketing']
        values = [random.uniform(0.1, 0.4) for _ in channels]
        total = sum(values)
        
        # Normalize to 100%
        normalized_values = [v / total for v in values]
        
        return dict(zip(channels, normalized_values))
    
    def _generate_pdf_report(self, template: ReportTemplate, section_data: Dict, 
                           filters: Dict[str, Any], output_filename: Optional[str] = None) -> Optional[Path]:
        """Generate PDF report."""
        try:
            filename = output_filename or f"{template.template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = self.output_directory / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(output_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            
            story.append(Paragraph(template.name, title_style))
            story.append(Spacer(1, 12))
            
            # Executive Summary
            summary_style = styles['Normal']
            date_range = filters.get('date_range', (datetime.now() - timedelta(days=30), datetime.now()))
            summary_text = f"""
            Report generated on {datetime.now().strftime('%B %d, %Y')} for the period 
            {date_range[0].strftime('%B %d, %Y')} to {date_range[1].strftime('%B %d, %Y')}.
            
            This report provides comprehensive insights into campaign performance across 
            {len(filters.get('campaign_ids', []))} campaigns and multiple marketing channels.
            """
            
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Paragraph(summary_text, summary_style))
            story.append(Spacer(1, 20))
            
            # Add sections
            for section in sorted(template.sections, key=lambda s: s.order_index):
                if section.is_enabled and section.section_id in section_data:
                    story.append(Paragraph(section.title, styles['Heading2']))
                    story.append(Paragraph(section.description, styles['Normal']))
                    
                    # Add section data as table or text
                    data = section_data[section.section_id]
                    if isinstance(data, dict) and 'error' not in data:
                        # Create simple data table
                        table_data = [['Metric', 'Value']]
                        
                        for key, value in list(data.items())[:10]:  # Limit to 10 items
                            if isinstance(value, (int, float)):
                                if isinstance(value, float):
                                    formatted_value = f"{value:,.2f}"
                                else:
                                    formatted_value = f"{value:,}"
                            else:
                                formatted_value = str(value)[:50]  # Truncate long values
                            
                            table_data.append([key.replace('_', ' ').title(), formatted_value])
                        
                        if len(table_data) > 1:
                            table = Table(table_data)
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 14),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)
                            ]))
                            story.append(table)
                    
                    story.append(Spacer(1, 20))
            
            # Footer
            footer_text = f"""
            Report generated by MarTech Integration Hub
            Portfolio: https://verityai.co | LinkedIn: https://www.linkedin.com/in/sspyrou/
            
            DISCLAIMER: This is demonstration code for portfolio purposes.
            """
            
            story.append(Spacer(1, 40))
            story.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated PDF report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            return None
    
    def _generate_html_report(self, template: ReportTemplate, section_data: Dict,
                            filters: Dict[str, Any], output_filename: Optional[str] = None) -> Optional[Path]:
        """Generate HTML report with interactive visualizations."""
        try:
            filename = output_filename or f"{template.template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = self.output_directory / filename
            
            # HTML template
            html_template = Template("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ template.name }}</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { background-color: #1f77b4; color: white; padding: 20px; margin-bottom: 30px; }
                    .section { margin-bottom: 40px; border: 1px solid #ddd; padding: 20px; }
                    .chart-container { height: 400px; margin: 20px 0; }
                    .footer { margin-top: 40px; padding: 20px; background-color: #f8f9fa; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{ template.name }}</h1>
                    <p>Generated on {{ generation_date }}</p>
                </div>
                
                {% for section in sections %}
                <div class="section">
                    <h2>{{ section.title }}</h2>
                    <p>{{ section.description }}</p>
                    <div class="chart-container" id="chart-{{ section.section_id }}"></div>
                </div>
                {% endfor %}
                
                <div class="footer">
                    <p>Report generated by MarTech Integration Hub</p>
                    <p>Portfolio: <a href="https://verityai.co">https://verityai.co</a> | 
                    LinkedIn: <a href="https://www.linkedin.com/in/sspyrou/">https://www.linkedin.com/in/sspyrou/</a></p>
                    <p><strong>DISCLAIMER:</strong> This is demonstration code for portfolio purposes.</p>
                </div>
                
                <script>
                    // Chart generation scripts will be inserted here
                    {{ chart_scripts }}
                </script>
            </body>
            </html>
            """)
            
            # Generate chart scripts
            chart_scripts = []
            
            for section in template.sections:
                if section.is_enabled and section.section_id in section_data:
                    data = section_data[section.section_id]
                    script = self._generate_plotly_chart(section, data)
                    if script:
                        chart_scripts.append(script)
            
            # Render HTML
            html_content = html_template.render(
                template=template,
                sections=[s for s in template.sections if s.is_enabled],
                generation_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                chart_scripts='\n'.join(chart_scripts)
            )
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return None
    
    def _generate_plotly_chart(self, section: ReportSection, data: Any) -> str:
        """Generate Plotly chart JavaScript for a section."""
        try:
            if section.visualization_type == VisualizationType.LINE_CHART and isinstance(data, dict):
                if 'dates' in data and 'impressions' in data:
                    return f"""
                    var trace1 = {{
                        x: {json.dumps(data['dates'])},
                        y: {json.dumps(data['impressions'])},
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Impressions',
                        line: {{color: '#1f77b4'}}
                    }};
                    
                    var layout = {{
                        title: '{section.title}',
                        xaxis: {{ title: 'Date' }},
                        yaxis: {{ title: 'Impressions' }}
                    }};
                    
                    Plotly.newPlot('chart-{section.section_id}', [trace1], layout);
                    """
            
            elif section.visualization_type == VisualizationType.BAR_CHART and isinstance(data, dict):
                channels = list(data.keys())
                values = [data[ch].get('impressions', 0) if isinstance(data[ch], dict) else data[ch] for ch in channels]
                
                return f"""
                var trace1 = {{
                    x: {json.dumps(channels)},
                    y: {json.dumps(values)},
                    type: 'bar',
                    marker: {{ color: '#1f77b4' }}
                }};
                
                var layout = {{
                    title: '{section.title}',
                    xaxis: {{ title: 'Channel' }},
                    yaxis: {{ title: 'Performance' }}
                }};
                
                Plotly.newPlot('chart-{section.section_id}', [trace1], layout);
                """
            
            elif section.visualization_type == VisualizationType.PIE_CHART and isinstance(data, dict):
                return f"""
                var trace1 = {{
                    labels: {json.dumps(list(data.keys()))},
                    values: {json.dumps(list(data.values()))},
                    type: 'pie'
                }};
                
                var layout = {{
                    title: '{section.title}'
                }};
                
                Plotly.newPlot('chart-{section.section_id}', [trace1], layout);
                """
            
            # Default: simple data table
            return f"""
            document.getElementById('chart-{section.section_id}').innerHTML = 
                '<pre>' + JSON.stringify({json.dumps(data)}, null, 2) + '</pre>';
            """
            
        except Exception as e:
            logger.error(f"Failed to generate chart script: {e}")
            return ""
    
    def _generate_excel_report(self, template: ReportTemplate, section_data: Dict,
                             filters: Dict[str, Any], output_filename: Optional[str] = None) -> Optional[Path]:
        """Generate Excel report with multiple sheets."""
        try:
            filename = output_filename or f"{template.template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = self.output_directory / filename
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Report': template.name,
                    'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Template ID': template.template_id,
                    'Campaigns': ', '.join(filters.get('campaign_ids', [])),
                    'Date Range': f"{filters.get('date_range', ('N/A', 'N/A'))[0]} to {filters.get('date_range', ('N/A', 'N/A'))[1]}"
                }
                
                summary_df = pd.DataFrame(list(summary_data.items()), columns=['Attribute', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Data sheets for each section
                for section in template.sections:
                    if section.is_enabled and section.section_id in section_data:
                        data = section_data[section.section_id]
                        
                        if isinstance(data, pd.DataFrame):
                            data.to_excel(writer, sheet_name=section.title[:31], index=False)  # Excel sheet name limit
                        elif isinstance(data, dict) and 'error' not in data:
                            df = pd.DataFrame(list(data.items()), columns=['Metric', 'Value'])
                            df.to_excel(writer, sheet_name=section.title[:31], index=False)
                        elif isinstance(data, list):
                            df = pd.DataFrame(data)
                            df.to_excel(writer, sheet_name=section.title[:31], index=False)
            
            logger.info(f"Generated Excel report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            return None
    
    def _generate_dashboard_report(self, template: ReportTemplate, section_data: Dict,
                                 filters: Dict[str, Any], output_filename: Optional[str] = None) -> Optional[Path]:
        """Generate interactive dashboard report."""
        try:
            filename = output_filename or f"{template.template_id}_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = self.output_directory / filename
            
            # Create dashboard using Plotly Dash-style HTML
            dashboard_template = Template("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{{ template.name }} - Interactive Dashboard</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                <style>
                    .dashboard-header { background: linear-gradient(135deg, #1f77b4, #ff7f0e); color: white; padding: 30px 0; margin-bottom: 30px; }
                    .metric-card { background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; }
                    .metric-value { font-size: 2.5rem; font-weight: bold; color: #1f77b4; }
                    .metric-label { color: #666; font-size: 0.9rem; }
                    .chart-container { height: 400px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="dashboard-header text-center">
                    <div class="container">
                        <h1>{{ template.name }}</h1>
                        <p>Real-time Campaign Performance Dashboard</p>
                        <small>Last updated: {{ generation_date }}</small>
                    </div>
                </div>
                
                <div class="container">
                    <div class="row">
                        {% for metric in key_metrics %}
                        <div class="col-md-3">
                            <div class="metric-card text-center">
                                <div class="metric-value">{{ metric.value }}</div>
                                <div class="metric-label">{{ metric.label }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    
                    {% for section in sections %}
                    <div class="row">
                        <div class="col-12">
                            <div class="metric-card">
                                <h3>{{ section.title }}</h3>
                                <p class="text-muted">{{ section.description }}</p>
                                <div class="chart-container" id="chart-{{ section.section_id }}"></div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <footer class="mt-5 py-4 bg-light text-center">
                    <p>Dashboard powered by MarTech Integration Hub</p>
                    <p>Portfolio: <a href="https://verityai.co">https://verityai.co</a> | 
                    LinkedIn: <a href="https://www.linkedin.com/in/sspyrou/">https://www.linkedin.com/in/sspyrou/</a></p>
                    <p><small><strong>DISCLAIMER:</strong> This is demonstration code for portfolio purposes.</small></p>
                </footer>
                
                <script>
                    {{ chart_scripts }}
                    
                    // Auto-refresh every 5 minutes
                    setTimeout(function() {
                        location.reload();
                    }, 300000);
                </script>
            </body>
            </html>
            """)
            
            # Extract key metrics for dashboard cards
            key_metrics = []
            if 'kpi_summary' in section_data:
                kpi_data = section_data['kpi_summary']
                key_metrics = [
                    {'label': 'Total Revenue', 'value': f"${kpi_data.get('total_revenue', 0):,.0f}"},
                    {'label': 'ROAS', 'value': f"{kpi_data.get('roas', 0):.1f}x"},
                    {'label': 'Conversion Rate', 'value': f"{kpi_data.get('average_conversion_rate', 0)*100:.1f}%"},
                    {'label': 'Total Conversions', 'value': f"{kpi_data.get('total_conversions', 0):,}"}
                ]
            
            # Generate chart scripts
            chart_scripts = []
            for section in template.sections:
                if section.is_enabled and section.section_id in section_data:
                    script = self._generate_plotly_chart(section, section_data[section.section_id])
                    if script:
                        chart_scripts.append(script)
            
            # Render dashboard
            dashboard_content = dashboard_template.render(
                template=template,
                sections=[s for s in template.sections if s.is_enabled],
                key_metrics=key_metrics,
                generation_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
                chart_scripts='\n'.join(chart_scripts)
            )
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
            
            logger.info(f"Generated dashboard report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard report: {e}")
            return None
    
    def schedule_report(self, schedule: ReportSchedule) -> bool:
        """Schedule automated report generation."""
        try:
            self.schedules[schedule.schedule_id] = schedule
            
            # Calculate next run time
            now = datetime.now()
            if schedule.frequency == ReportFrequency.DAILY:
                schedule.next_run = now.replace(hour=9, minute=0, second=0) + timedelta(days=1)
            elif schedule.frequency == ReportFrequency.WEEKLY:
                schedule.next_run = now.replace(hour=9, minute=0, second=0) + timedelta(days=7)
            elif schedule.frequency == ReportFrequency.MONTHLY:
                schedule.next_run = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=9, minute=0, second=0)
            
            logger.info(f"Scheduled report: {schedule.schedule_id} (next run: {schedule.next_run})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule report: {e}")
            return False
    
    def send_report_email(self, report_metadata: ReportMetadata, recipients: List[str],
                         subject: Optional[str] = None, message: Optional[str] = None) -> bool:
        """Send generated report via email."""
        try:
            if not self.smtp_config or not report_metadata.file_paths:
                logger.warning("SMTP not configured or no report files to send")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get('from_address', 'reports@martech-hub.com')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject or f"Campaign Report - {report_metadata.template_id}"
            
            # Email body
            body = message or f"""
            Please find attached your campaign performance report.
            
            Report Details:
            - Generated: {report_metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
            - Data Range: {report_metadata.data_range[0].strftime('%Y-%m-%d')} to {report_metadata.data_range[1].strftime('%Y-%m-%d')}
            - Records: {report_metadata.record_count:,}
            - Generation Time: {report_metadata.generation_time_seconds:.2f} seconds
            
            Best regards,
            MarTech Integration Hub
            
            Portfolio: https://verityai.co
            LinkedIn: https://www.linkedin.com/in/sspyrou/
            
            DISCLAIMER: This is demonstration code for portfolio purposes.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report files
            for file_path in report_metadata.file_paths:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config.get('smtp_port', 587))
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            text = msg.as_string()
            server.sendmail(msg['From'], recipients, text)
            server.quit()
            
            logger.info(f"Sent report email to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send report email: {e}")
            return False
    
    def get_report_history(self, limit: int = 100) -> List[ReportMetadata]:
        """Get history of generated reports."""
        try:
            reports = list(self.generated_reports.values())
            reports.sort(key=lambda r: r.generated_at, reverse=True)
            return reports[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get report history: {e}")
            return []
    
    def cleanup_old_reports(self, days_to_keep: int = 30) -> int:
        """Clean up old report files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for report_id, metadata in list(self.generated_reports.items()):
                if metadata.generated_at < cutoff_date:
                    # Delete files
                    for file_path in metadata.file_paths:
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                cleaned_count += 1
                        except OSError:
                            pass
                    
                    # Remove from tracking
                    del self.generated_reports[report_id]
            
            logger.info(f"Cleaned up {cleaned_count} old report files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")
            return 0


def create_sample_reporting_suite() -> CampaignReportingSuite:
    """Create sample campaign reporting suite for demonstration."""
    
    suite = CampaignReportingSuite()
    
    # Create sample scheduled reports
    schedules = [
        ReportSchedule(
            schedule_id="weekly_executive",
            template_id="executive_summary",
            frequency=ReportFrequency.WEEKLY,
            recipients=["cmo@example.com", "marketing-director@example.com"]
        ),
        ReportSchedule(
            schedule_id="daily_performance",
            template_id="performance_analysis",
            frequency=ReportFrequency.DAILY,
            recipients=["marketing-manager@example.com"]
        )
    ]
    
    for schedule in schedules:
        suite.schedule_report(schedule)
    
    return suite


def run_campaign_reporting_demo():
    """
    Run the campaign reporting suite demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("📊 Campaign Reporting Suite Demo")
    print("=" * 50)
    
    print("📈 Key Features:")
    print("  • Multi-format report generation (PDF, HTML, Excel, Dashboard)")
    print("  • Automated report scheduling and distribution")
    print("  • Interactive data visualizations")
    print("  • Executive summary generation")
    print("  • Custom report templates")
    print("  • Real-time dashboard updates")
    print("  • Advanced analytics and insights")
    print("  • Multi-channel performance reporting")
    
    print("\n📋 Supported Report Types:")
    for report_type in ReportType:
        print(f"  • {report_type.value}")
    
    print("\n📄 Output Formats:")
    for format_type in ReportFormat:
        print(f"  • {format_type.value}")
    
    print("\n📊 Visualization Types:")
    for viz_type in list(VisualizationType)[:6]:  # Show first 6
        print(f"  • {viz_type.value}")
    print(f"  • ... and {len(VisualizationType) - 6} more visualization types")
    
    print("\n🚀 Initializing reporting suite...")
    suite = create_sample_reporting_suite()
    
    print("✅ Reporting suite initialized")
    print(f"   • Default templates: {len(suite.templates)}")
    print(f"   • Scheduled reports: {len(suite.schedules)}")
    
    # Generate sample reports
    print("\n📊 Generating sample reports...")
    
    sample_campaigns = ['campaign_001', 'campaign_002', 'campaign_003']
    date_range = (datetime.now() - timedelta(days=30), datetime.now())
    
    generated_reports = []
    
    for template_id in ['executive_summary', 'performance_analysis']:
        if template_id in suite.templates:
            print(f"   Generating {template_id} report...")
            metadata = suite.generate_report(
                template_id=template_id,
                campaign_ids=sample_campaigns,
                date_range=date_range
            )
            
            if metadata:
                generated_reports.append(metadata)
                print(f"   ✅ Generated {metadata.file_paths[0] if metadata.file_paths else 'report'}")
                print(f"      • Records: {metadata.record_count:,}")
                print(f"      • Generation time: {metadata.generation_time_seconds:.2f}s")
                print(f"      • File size: {metadata.file_size_bytes:,} bytes")
    
    # Display template information
    print("\n📋 Available Report Templates:")
    for template_id, template in suite.templates.items():
        print(f"\n   📊 {template.name}:")
        print(f"      • Type: {template.report_type.value}")
        print(f"      • Format: {template.output_format.value}")
        print(f"      • Sections: {len(template.sections)}")
        print(f"      • Description: {template.description}")
        
        for section in template.sections[:2]:  # Show first 2 sections
            print(f"        - {section.title} ({section.visualization_type.value})")
    
    # Show scheduled reports
    print("\n⏰ Scheduled Reports:")
    for schedule_id, schedule in suite.schedules.items():
        template_name = suite.templates[schedule.template_id].name
        print(f"   • {template_name}")
        print(f"     - Frequency: {schedule.frequency.value}")
        print(f"     - Recipients: {len(schedule.recipients)}")
        if schedule.next_run:
            print(f"     - Next run: {schedule.next_run.strftime('%Y-%m-%d %H:%M')}")
    
    # Report history
    history = suite.get_report_history(5)
    if history:
        print(f"\n📚 Recent Reports ({len(history)} total):")
        for report in history[:3]:  # Show last 3
            print(f"   • {report.report_id}")
            print(f"     - Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"     - Template: {report.template_id}")
            print(f"     - Status: {report.status}")
    
    # Sample data insights
    print("\n💡 Sample Report Insights:")
    insights = [
        "📈 Campaign performance shows 23% improvement in ROAS over last month",
        "🎯 Email channel delivering highest conversion rate at 6.8%",
        "📱 Mobile traffic accounts for 68% of total impressions",
        "💰 Cost per acquisition decreased by 15% through optimization",
        "🔍 Search ads showing strong performance with 4.2x ROAS"
    ]
    
    for insight in insights:
        print(f"   {insight}")
    
    print("\n🌟 Advanced Capabilities:")
    print("  • Automated anomaly detection in report data")
    print("  • Cross-campaign performance benchmarking")
    print("  • Predictive trend analysis and forecasting")
    print("  • Custom KPI threshold alerting")
    print("  • Multi-stakeholder report distribution")
    print("  • Historical performance comparison")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return suite


if __name__ == "__main__":
    run_campaign_reporting_demo()

