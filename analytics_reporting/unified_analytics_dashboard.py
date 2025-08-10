"""
Unified Analytics Dashboard for MarTech Integration Hub

Executive-level marketing analytics dashboard that aggregates data from all
integrated platforms into a comprehensive, real-time business intelligence interface.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

# Import our custom analytics modules
try:
    from .executive_summary_generator import ExecutiveSummaryGenerator
    from .predictive_analytics_engine import PredictiveAnalyticsEngine
    from .real_time_performance_monitor import RealTimePerformanceMonitor
    from .roi_calculation_framework import ROICalculationFramework
    from .data_visualization_tools import DataVisualizationTools
    from .automated_insight_generator import AutomatedInsightGenerator
except ImportError:
    # For demo purposes when modules are not available
    pass

logger = logging.getLogger(__name__)


class DashboardTheme(Enum):
    EXECUTIVE = "executive"
    MARKETER = "marketer"
    ANALYST = "analyst"
    COMPLIANCE = "compliance"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_id: str
    title: str
    widget_type: str
    data_source: str
    refresh_interval: int
    size: str
    position: Dict[str, int]
    config: Dict[str, Any]
    permissions: List[str]


@dataclass
class DashboardMetrics:
    """Key dashboard metrics summary."""
    total_revenue: float
    total_spend: float
    roi_percentage: float
    conversion_rate: float
    customer_acquisition_cost: float
    lifetime_value: float
    active_campaigns: int
    data_freshness: datetime
    alert_count: int
    trend_direction: str


class UnifiedAnalyticsDashboard:
    """
    Unified analytics dashboard for comprehensive marketing performance monitoring.
    
    Provides executive-level insights, real-time monitoring, predictive analytics,
    and actionable recommendations across all integrated marketing platforms.
    """
    
    def __init__(self, theme: DashboardTheme = DashboardTheme.EXECUTIVE):
        self.theme = theme
        self.widgets = {}
        self.data_connectors = {}
        self.user_permissions = []
        self.refresh_intervals = {}
        
        # Initialize analytics engines
        self.executive_generator = None
        self.predictive_engine = None
        self.performance_monitor = None
        self.roi_framework = None
        self.visualization_tools = None
        self.insight_generator = None
        
        self._initialize_engines()
        self._setup_default_widgets()
        
        # Dash app configuration
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
            meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
        )
        
        self._setup_dashboard_layout()
        self._register_callbacks()
    
    def _initialize_engines(self):
        """Initialize analytics engines with error handling."""
        try:
            self.executive_generator = ExecutiveSummaryGenerator()
            logger.info("Executive summary generator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize executive generator: {e}")
        
        try:
            self.predictive_engine = PredictiveAnalyticsEngine()
            logger.info("Predictive analytics engine initialized")
        except Exception as e:
            logger.warning(f"Could not initialize predictive engine: {e}")
        
        try:
            self.performance_monitor = RealTimePerformanceMonitor()
            logger.info("Performance monitor initialized")
        except Exception as e:
            logger.warning(f"Could not initialize performance monitor: {e}")
        
        try:
            self.roi_framework = ROICalculationFramework()
            logger.info("ROI framework initialized")
        except Exception as e:
            logger.warning(f"Could not initialize ROI framework: {e}")
        
        try:
            self.visualization_tools = DataVisualizationTools()
            logger.info("Visualization tools initialized")
        except Exception as e:
            logger.warning(f"Could not initialize visualization tools: {e}")
        
        try:
            self.insight_generator = AutomatedInsightGenerator()
            logger.info("Insight generator initialized")
        except Exception as e:
            logger.warning(f"Could not initialize insight generator: {e}")
    
    def _setup_default_widgets(self):
        """Set up default dashboard widgets based on theme."""
        
        if self.theme == DashboardTheme.EXECUTIVE:
            self.widgets.update({
                'kpi_summary': DashboardWidget(
                    widget_id='kpi_summary',
                    title='Executive KPI Summary',
                    widget_type='kpi_cards',
                    data_source='aggregated',
                    refresh_interval=300,  # 5 minutes
                    size='large',
                    position={'row': 0, 'col': 0, 'width': 12},
                    config={'metrics': ['revenue', 'roi', 'cac', 'ltv']},
                    permissions=['executive', 'admin']
                ),
                'revenue_trend': DashboardWidget(
                    widget_id='revenue_trend',
                    title='Revenue Trend Analysis',
                    widget_type='line_chart',
                    data_source='revenue',
                    refresh_interval=600,
                    size='medium',
                    position={'row': 1, 'col': 0, 'width': 8},
                    config={'time_period': '30d', 'granularity': 'daily'},
                    permissions=['executive', 'admin', 'analyst']
                ),
                'channel_performance': DashboardWidget(
                    widget_id='channel_performance',
                    title='Channel ROI Comparison',
                    widget_type='bar_chart',
                    data_source='channels',
                    refresh_interval=900,
                    size='medium',
                    position={'row': 1, 'col': 8, 'width': 4},
                    config={'metric': 'roi', 'top_n': 10},
                    permissions=['executive', 'admin', 'analyst']
                )
            })
        
        elif self.theme == DashboardTheme.MARKETER:
            self.widgets.update({
                'campaign_performance': DashboardWidget(
                    widget_id='campaign_performance',
                    title='Campaign Performance Dashboard',
                    widget_type='campaign_grid',
                    data_source='campaigns',
                    refresh_interval=300,
                    size='large',
                    position={'row': 0, 'col': 0, 'width': 12},
                    config={'status': 'active', 'metrics': ['ctr', 'cpc', 'conversions']},
                    permissions=['marketer', 'admin', 'analyst']
                ),
                'audience_insights': DashboardWidget(
                    widget_id='audience_insights',
                    title='Audience Segmentation Analysis',
                    widget_type='pie_chart',
                    data_source='audiences',
                    refresh_interval=1800,
                    size='medium',
                    position={'row': 1, 'col': 0, 'width': 6},
                    config={'segment_type': 'demographic'},
                    permissions=['marketer', 'admin']
                )
            })
    
    def _setup_dashboard_layout(self):
        """Set up the main dashboard layout."""
        
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("MarTech Analytics Dashboard", className="text-primary mb-0"),
                    html.P(f"Real-time marketing performance insights", className="text-muted"),
                    html.Small([
                        "Powered by ",
                        html.A("VerityAI", href="https://verityai.co", target="_blank", className="text-decoration-none"),
                        " | Created by ",
                        html.A("Sotiris Spyrou", href="https://www.linkedin.com/in/sspyrou/", target="_blank", className="text-decoration-none")
                    ], className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Refresh", id="refresh-btn", color="primary", size="sm"),
                        dbc.Button("Export", id="export-btn", color="secondary", size="sm"),
                        dbc.Button("Settings", id="settings-btn", color="outline-secondary", size="sm")
                    ], className="float-end")
                ], width=4, className="d-flex align-items-center")
            ], className="mb-4"),
            
            # Alert Banner
            dbc.Row([
                dbc.Col([
                    dbc.Alert(
                        id="alert-banner",
                        children="Dashboard loaded successfully",
                        color="success",
                        dismissable=True,
                        is_open=False
                    )
                ])
            ]),
            
            # KPI Summary Cards
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("$127,450", className="text-primary mb-0"),
                            html.P("Total Revenue", className="text-muted mb-0"),
                            html.Small("↑ 15.3% vs last month", className="text-success")
                        ])
                    ], className="h-100")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("324%", className="text-primary mb-0"),
                            html.P("Marketing ROI", className="text-muted mb-0"),
                            html.Small("↑ 23.1% vs last month", className="text-success")
                        ])
                    ], className="h-100")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("$42.50", className="text-primary mb-0"),
                            html.P("Customer Acq. Cost", className="text-muted mb-0"),
                            html.Small("↓ 8.7% vs last month", className="text-success")
                        ])
                    ], className="h-100")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("$890", className="text-primary mb-0"),
                            html.P("Customer LTV", className="text-muted mb-0"),
                            html.Small("↑ 12.4% vs last month", className="text-success")
                        ])
                    ], className="h-100")
                ], md=3)
            ], className="mb-4"),
            
            # Main Content Area
            dbc.Row([
                # Revenue Trend Chart
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Revenue Trend Analysis", className="mb-0"),
                            dbc.ButtonGroup([
                                dbc.Button("7D", size="sm", outline=True),
                                dbc.Button("30D", size="sm", color="primary"),
                                dbc.Button("90D", size="sm", outline=True)
                            ], size="sm", className="float-end")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                id="revenue-trend-chart",
                                figure=self._create_revenue_trend_chart(),
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], md=8),
                
                # Channel Performance
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Channel Performance", className="mb-0")),
                        dbc.CardBody([
                            dcc.Graph(
                                id="channel-performance-chart",
                                figure=self._create_channel_performance_chart(),
                                config={'displayModeBar': False}
                            )
                        ])
                    ])
                ], md=4)
            ], className="mb-4"),
            
            # Secondary Content Row
            dbc.Row([
                # Campaign Performance Table
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Active Campaigns", className="mb-0"),
                            dbc.Badge("12 Active", color="success", className="float-end")
                        ]),
                        dbc.CardBody([
                            html.Div(id="campaign-table")
                        ])
                    ])
                ], md=8),
                
                # Real-time Alerts
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Performance Alerts", className="mb-0")),
                        dbc.CardBody([
                            html.Div(id="alerts-list")
                        ])
                    ])
                ], md=4)
            ], className="mb-4"),
            
            # Insights and Recommendations
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("AI-Powered Insights & Recommendations", className="mb-0")),
                        dbc.CardBody([
                            html.Div(id="insights-recommendations")
                        ])
                    ])
                ])
            ], className="mb-4"),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P([
                        "MarTech Integration Hub - Advanced Marketing Analytics Platform | ",
                        html.A("Learn More", href="https://verityai.co", target="_blank"),
                        " | ",
                        html.A("Connect on LinkedIn", href="https://www.linkedin.com/in/sspyrou/", target="_blank"),
                        html.Br(),
                        html.Small("⚠️ DISCLAIMER: This is demonstration code for portfolio purposes. Not intended for production use without proper testing and validation.", className="text-muted")
                    ], className="text-center text-muted")
                ])
            ])
        ], fluid=True, className="py-3")
    
    def _register_callbacks(self):
        """Register dashboard callbacks for interactivity."""
        
        @self.app.callback(
            Output("revenue-trend-chart", "figure"),
            [Input("refresh-btn", "n_clicks")]
        )
        def update_revenue_chart(n_clicks):
            """Update revenue trend chart."""
            return self._create_revenue_trend_chart()
        
        @self.app.callback(
            Output("channel-performance-chart", "figure"),
            [Input("refresh-btn", "n_clicks")]
        )
        def update_channel_chart(n_clicks):
            """Update channel performance chart."""
            return self._create_channel_performance_chart()
        
        @self.app.callback(
            Output("campaign-table", "children"),
            [Input("refresh-btn", "n_clicks")]
        )
        def update_campaign_table(n_clicks):
            """Update campaign performance table."""
            return self._create_campaign_table()
        
        @self.app.callback(
            Output("alerts-list", "children"),
            [Input("refresh-btn", "n_clicks")]
        )
        def update_alerts(n_clicks):
            """Update performance alerts."""
            return self._create_alerts_list()
        
        @self.app.callback(
            Output("insights-recommendations", "children"),
            [Input("refresh-btn", "n_clicks")]
        )
        def update_insights(n_clicks):
            """Update AI insights and recommendations."""
            return self._create_insights_section()
        
        @self.app.callback(
            Output("alert-banner", "is_open"),
            Output("alert-banner", "children"),
            Output("alert-banner", "color"),
            [Input("refresh-btn", "n_clicks")]
        )
        def show_refresh_alert(n_clicks):
            """Show refresh notification."""
            if n_clicks:
                return True, f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}", "info"
            return False, "", "success"
    
    def _create_revenue_trend_chart(self) -> go.Figure:
        """Create revenue trend chart."""
        
        # Sample data for demonstration
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        revenue = np.random.normal(4000, 800, len(dates)) + np.linspace(3000, 5000, len(dates))
        target = [4500] * len(dates)
        
        fig = go.Figure()
        
        # Actual revenue line
        fig.add_trace(go.Scatter(
            x=dates,
            y=revenue,
            mode='lines+markers',
            name='Actual Revenue',
            line=dict(color='#0066CC', width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
        ))
        
        # Target line
        fig.add_trace(go.Scatter(
            x=dates,
            y=target,
            mode='lines',
            name='Target',
            line=dict(color='#FF6B35', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>Target: $%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title=None,
            yaxis_title="Revenue ($)",
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=20, b=0),
            height=350
        )
        
        return fig
    
    def _create_channel_performance_chart(self) -> go.Figure:
        """Create channel performance chart."""
        
        channels = ['Google Ads', 'Facebook', 'Email', 'SEO', 'LinkedIn']
        roi_values = [420, 350, 890, 540, 280]
        colors = ['#0066CC', '#1877F2', '#34A853', '#FF9500', '#0077B5']
        
        fig = go.Figure(go.Bar(
            x=roi_values,
            y=channels,
            orientation='h',
            marker_color=colors,
            hovertemplate='<b>%{y}</b><br>ROI: %{x}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="ROI (%)",
            yaxis_title=None,
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
            height=350
        )
        
        return fig
    
    def _create_campaign_table(self) -> html.Div:
        """Create campaign performance table."""
        
        campaigns = [
            {'name': 'Holiday Sale 2024', 'status': 'Active', 'budget': '$5,000', 'spent': '$3,247', 'conversions': 89, 'cpa': '$36.48'},
            {'name': 'Brand Awareness Q1', 'status': 'Active', 'budget': '$8,000', 'spent': '$4,892', 'conversions': 156, 'cpa': '$31.36'},
            {'name': 'Product Launch', 'status': 'Active', 'budget': '$12,000', 'spent': '$9,834', 'conversions': 234, 'cpa': '$42.02'},
            {'name': 'Retargeting Campaign', 'status': 'Active', 'budget': '$3,500', 'spent': '$2,456', 'conversions': 67, 'cpa': '$36.66'}
        ]
        
        table_header = [
            html.Thead(html.Tr([
                html.Th("Campaign"),
                html.Th("Status"),
                html.Th("Budget"),
                html.Th("Spent"),
                html.Th("Conv."),
                html.Th("CPA")
            ]))
        ]
        
        table_body = [
            html.Tbody([
                html.Tr([
                    html.Td(campaign['name']),
                    html.Td(dbc.Badge(campaign['status'], color="success" if campaign['status'] == 'Active' else 'secondary')),
                    html.Td(campaign['budget']),
                    html.Td(campaign['spent']),
                    html.Td(campaign['conversions']),
                    html.Td(campaign['cpa'])
                ]) for campaign in campaigns
            ])
        ]
        
        return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, size='sm')
    
    def _create_alerts_list(self) -> html.Div:
        """Create performance alerts list."""
        
        alerts = [
            {'type': 'success', 'message': 'Email campaign ROI up 23%', 'time': '5m ago'},
            {'type': 'warning', 'message': 'Facebook CPC increased 15%', 'time': '12m ago'},
            {'type': 'info', 'message': 'New audience segment identified', 'time': '1h ago'},
            {'type': 'danger', 'message': 'Budget threshold reached', 'time': '2h ago'}
        ]
        
        alert_components = []
        for alert in alerts:
            color_map = {'success': 'success', 'warning': 'warning', 'info': 'info', 'danger': 'danger'}
            
            alert_components.append(
                dbc.Alert([
                    html.Strong(alert['message']),
                    html.Br(),
                    html.Small(alert['time'], className="text-muted")
                ], color=color_map[alert['type']], className="py-2 mb-2")
            )
        
        return html.Div(alert_components)
    
    def _create_insights_section(self) -> html.Div:
        """Create AI insights and recommendations section."""
        
        insights = [
            {
                'title': 'Revenue Growth Acceleration',
                'description': 'Email marketing shows 890% ROI - highest performing channel. Consider increasing budget allocation by 25%.',
                'priority': 'high',
                'impact': 'Potential $15K additional monthly revenue'
            },
            {
                'title': 'Customer Acquisition Optimization',
                'description': 'Facebook CPC has increased 15% in the last week. Review targeting and creative performance.',
                'priority': 'medium',
                'impact': 'Potential $2K monthly cost savings'
            },
            {
                'title': 'Cross-Channel Attribution',
                'description': 'Multi-touch attribution shows SEO contributing to 34% more conversions than last-click model indicates.',
                'priority': 'low',
                'impact': 'Better budget allocation decisions'
            }
        ]
        
        insight_cards = []
        for insight in insights:
            color_map = {'high': 'danger', 'medium': 'warning', 'low': 'info'}
            
            insight_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H6(insight['title'], className="mb-2"),
                            dbc.Badge(insight['priority'].upper(), color=color_map[insight['priority']], className="float-end")
                        ]),
                        html.P(insight['description'], className="mb-2"),
                        html.Small(f"💡 {insight['impact']}", className="text-muted")
                    ])
                ], className="mb-3")
            )
        
        return html.Div([
            html.P("🤖 AI-powered insights based on your marketing data:", className="mb-3"),
            html.Div(insight_cards)
        ])
    
    def add_widget(self, widget: DashboardWidget):
        """Add a new widget to the dashboard."""
        self.widgets[widget.widget_id] = widget
        logger.info(f"Added widget: {widget.widget_id}")
    
    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard."""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            logger.info(f"Removed widget: {widget_id}")
    
    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics summary."""
        
        # In a real implementation, this would aggregate data from all connectors
        return DashboardMetrics(
            total_revenue=127450.0,
            total_spend=39280.0,
            roi_percentage=324.0,
            conversion_rate=3.2,
            customer_acquisition_cost=42.50,
            lifetime_value=890.0,
            active_campaigns=12,
            data_freshness=datetime.now(),
            alert_count=4,
            trend_direction="up"
        )
    
    def export_dashboard_data(self, format: str = "json") -> Union[str, bytes]:
        """Export dashboard data in specified format."""
        
        metrics = self.get_dashboard_metrics()
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'dashboard_theme': self.theme.value,
            'metrics': asdict(metrics),
            'widgets': [asdict(widget) for widget in self.widgets.values()],
            'metadata': {
                'author': 'Sotiris Spyrou',
                'portfolio': 'https://verityai.co',
                'linkedin': 'https://www.linkedin.com/in/sspyrou/',
                'disclaimer': 'This is demonstration code for portfolio purposes.'
            }
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        elif format.lower() == "csv":
            df = pd.DataFrame([metrics])
            return df.to_csv(index=False)
        else:
            return json.dumps(data, default=str)
    
    def set_user_permissions(self, permissions: List[str]):
        """Set user permissions for dashboard access."""
        self.user_permissions = permissions
        logger.info(f"User permissions set: {permissions}")
    
    def run_dashboard(self, host: str = "127.0.0.1", port: int = 8050, debug: bool = True):
        """Run the dashboard server."""
        
        logger.info(f"Starting dashboard server at http://{host}:{port}")
        print(f"\n🚀 MarTech Analytics Dashboard")
        print(f"📊 Starting server at: http://{host}:{port}")
        print(f"👤 Created by: Sotiris Spyrou")
        print(f"🌐 Portfolio: https://verityai.co")
        print(f"💼 LinkedIn: https://www.linkedin.com/in/sspyrou/")
        print(f"\n⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.\n")
        
        self.app.run_server(host=host, port=port, debug=debug)


def create_sample_dashboard() -> UnifiedAnalyticsDashboard:
    """Create a sample dashboard with demo data."""
    
    dashboard = UnifiedAnalyticsDashboard(theme=DashboardTheme.EXECUTIVE)
    
    # Add custom widgets
    custom_widget = DashboardWidget(
        widget_id='custom_metrics',
        title='Custom KPIs',
        widget_type='custom',
        data_source='api',
        refresh_interval=60,
        size='small',
        position={'row': 2, 'col': 0, 'width': 6},
        config={'api_endpoint': '/api/custom-metrics'},
        permissions=['admin']
    )
    
    dashboard.add_widget(custom_widget)
    
    return dashboard


def run_dashboard_demo():
    """
    Run the unified analytics dashboard demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("📊 MarTech Unified Analytics Dashboard Demo")
    print("=" * 50)
    
    # Create dashboard instance
    print("🔧 Initializing dashboard components...")
    dashboard = create_sample_dashboard()
    
    # Set permissions
    dashboard.set_user_permissions(['executive', 'admin', 'analyst'])
    
    # Get current metrics
    print("📈 Loading dashboard metrics...")
    metrics = dashboard.get_dashboard_metrics()
    
    print(f"✅ Dashboard initialized with {len(dashboard.widgets)} widgets")
    print(f"💰 Total Revenue: ${metrics.total_revenue:,.2f}")
    print(f"📊 Marketing ROI: {metrics.roi_percentage:.1f}%")
    print(f"🎯 Active Campaigns: {metrics.active_campaigns}")
    print(f"🚨 Performance Alerts: {metrics.alert_count}")
    
    # Export sample data
    print("\n📄 Exporting dashboard data...")
    json_export = dashboard.export_dashboard_data("json")
    print(f"✅ Exported {len(json_export)} characters of dashboard data")
    
    print("\n🌟 Key Dashboard Features:")
    print("  • Real-time performance monitoring")
    print("  • Executive-level KPI summaries")
    print("  • AI-powered insights and recommendations")
    print("  • Multi-channel campaign performance")
    print("  • Advanced ROI and attribution analysis")
    print("  • Customizable widgets and themes")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    
    # Option to run the actual dashboard
    try:
        user_input = input("\n🚀 Would you like to start the dashboard server? (y/n): ")
        if user_input.lower() == 'y':
            print("Starting dashboard server...")
            dashboard.run_dashboard(debug=False)
        else:
            print("Demo completed. Dashboard instance created successfully.")
    except KeyboardInterrupt:
        print("\nDemo completed.")
    
    return dashboard


if __name__ == "__main__":
    run_dashboard_demo()