import logging
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import jinja2
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    TABLE = "table"


@dataclass
class ReportMetric:
    """Represents a metric to include in the report."""
    name: str
    display_name: str
    data_source: str
    aggregation: str  # sum, avg, count, max, min
    format_type: str = "number"  # number, currency, percentage
    description: Optional[str] = None


@dataclass
class ReportFilter:
    """Represents a filter for report data."""
    field: str
    operator: str  # eq, gt, lt, in, contains
    value: Any
    display_name: Optional[str] = None


@dataclass
class ReportChart:
    """Represents a chart in the report."""
    title: str
    chart_type: ChartType
    data_source: str
    x_axis: str
    y_axis: str
    filters: List[ReportFilter] = None
    chart_options: Dict[str, Any] = None


@dataclass
class ReportDefinition:
    """Complete report definition."""
    name: str
    description: str
    metrics: List[ReportMetric]
    charts: List[ReportChart]
    filters: List[ReportFilter] = None
    date_range: Dict[str, Any] = None
    refresh_schedule: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = None


class CustomReportBuilder:
    """
    Flexible report builder for creating custom marketing analytics reports.
    Supports multiple data sources, formats, and visualization types.
    """
    
    def __init__(self):
        self.data_sources = {}
        self.report_templates = {}
        self.report_cache = {}
        self._setup_jinja_environment()
    
    def _setup_jinja_environment(self):
        """Set up Jinja2 template environment."""
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.jinja_env.filters['currency'] = self._format_currency
        self.jinja_env.filters['percentage'] = self._format_percentage
        self.jinja_env.filters['number'] = self._format_number
    
    def register_data_source(self, name: str, data_connector: Any):
        """Register a data source for use in reports."""
        self.data_sources[name] = data_connector
        logger.info(f"Registered data source: {name}")
    
    def create_report_definition(
        self,
        name: str,
        description: str,
        metrics: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        filters: Optional[List[Dict[str, Any]]] = None,
        date_range: Optional[Dict[str, Any]] = None
    ) -> ReportDefinition:
        """Create a new report definition."""
        
        # Convert dictionaries to dataclasses
        report_metrics = [ReportMetric(**metric) for metric in metrics]
        report_charts = [
            ReportChart(
                title=chart['title'],
                chart_type=ChartType(chart['chart_type']),
                data_source=chart['data_source'],
                x_axis=chart['x_axis'],
                y_axis=chart['y_axis'],
                filters=[ReportFilter(**f) for f in chart.get('filters', [])],
                chart_options=chart.get('chart_options', {})
            )
            for chart in charts
        ]
        
        report_filters = []
        if filters:
            report_filters = [ReportFilter(**f) for f in filters]
        
        definition = ReportDefinition(
            name=name,
            description=description,
            metrics=report_metrics,
            charts=report_charts,
            filters=report_filters,
            date_range=date_range,
            created_at=datetime.now()
        )
        
        logger.info(f"Created report definition: {name}")
        return definition
    
    def generate_report(
        self,
        definition: ReportDefinition,
        output_format: ReportFormat = ReportFormat.HTML,
        output_path: Optional[str] = None
    ) -> Union[str, bytes]:
        """Generate a report based on the definition."""
        
        try:
            logger.info(f"Generating report: {definition.name}")
            
            # Collect data for all metrics and charts
            report_data = self._collect_report_data(definition)
            
            # Generate visualizations
            charts_html = self._generate_charts(definition, report_data)
            
            # Create report content based on format
            if output_format == ReportFormat.HTML:
                content = self._generate_html_report(definition, report_data, charts_html)
            elif output_format == ReportFormat.JSON:
                content = self._generate_json_report(definition, report_data)
            elif output_format == ReportFormat.CSV:
                content = self._generate_csv_report(definition, report_data)
            elif output_format == ReportFormat.EXCEL:
                content = self._generate_excel_report(definition, report_data)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Save to file if path provided
            if output_path:
                self._save_report(content, output_path, output_format)
            
            logger.info(f"Successfully generated report: {definition.name}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating report {definition.name}: {e}")
            raise
    
    def _collect_report_data(self, definition: ReportDefinition) -> Dict[str, Any]:
        """Collect data from various sources for the report."""
        report_data = {
            'metrics': {},
            'charts': {},
            'metadata': {
                'generated_at': datetime.now(),
                'report_name': definition.name,
                'date_range': definition.date_range
            }
        }
        
        # Collect metric data
        for metric in definition.metrics:
            try:
                data_source = self.data_sources.get(metric.data_source)
                if not data_source:
                    logger.warning(f"Data source not found: {metric.data_source}")
                    continue
                
                metric_data = self._fetch_metric_data(data_source, metric, definition.filters)
                report_data['metrics'][metric.name] = {
                    'value': metric_data,
                    'display_name': metric.display_name,
                    'format_type': metric.format_type,
                    'description': metric.description
                }
                
            except Exception as e:
                logger.error(f"Error collecting metric {metric.name}: {e}")
                report_data['metrics'][metric.name] = {'error': str(e)}
        
        # Collect chart data
        for chart in definition.charts:
            try:
                data_source = self.data_sources.get(chart.data_source)
                if not data_source:
                    logger.warning(f"Data source not found: {chart.data_source}")
                    continue
                
                chart_data = self._fetch_chart_data(data_source, chart, definition.filters)
                report_data['charts'][chart.title] = chart_data
                
            except Exception as e:
                logger.error(f"Error collecting chart data {chart.title}: {e}")
                report_data['charts'][chart.title] = {'error': str(e)}
        
        return report_data
    
    def _fetch_metric_data(
        self, 
        data_source: Any, 
        metric: ReportMetric, 
        filters: List[ReportFilter]
    ) -> Any:
        """Fetch data for a specific metric."""
        
        # This would integrate with actual data connectors
        # For demo purposes, generating sample data
        
        if hasattr(data_source, 'get_metric'):
            return data_source.get_metric(
                metric_name=metric.name,
                aggregation=metric.aggregation,
                filters=filters
            )
        
        # Sample data based on metric name
        sample_metrics = {
            'total_sessions': 15420,
            'conversion_rate': 3.2,
            'total_revenue': 45890.50,
            'cost_per_acquisition': 28.75,
            'email_open_rate': 24.3,
            'bounce_rate': 42.1,
            'average_order_value': 89.25,
            'return_on_ad_spend': 4.2
        }
        
        return sample_metrics.get(metric.name, 0)
    
    def _fetch_chart_data(
        self, 
        data_source: Any, 
        chart: ReportChart, 
        filters: List[ReportFilter]
    ) -> Dict[str, Any]:
        """Fetch data for a specific chart."""
        
        if hasattr(data_source, 'get_chart_data'):
            return data_source.get_chart_data(
                chart_type=chart.chart_type.value,
                x_axis=chart.x_axis,
                y_axis=chart.y_axis,
                filters=chart.filters or filters
            )
        
        # Generate sample chart data
        import random
        import numpy as np
        
        if chart.chart_type == ChartType.LINE:
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            values = np.random.randint(100, 1000, 30)
            return {
                'labels': [d.strftime('%Y-%m-%d') for d in dates],
                'values': values.tolist(),
                'chart_type': 'line'
            }
        
        elif chart.chart_type == ChartType.BAR:
            categories = ['Organic', 'Paid Search', 'Social', 'Email', 'Direct']
            values = [random.randint(500, 5000) for _ in categories]
            return {
                'labels': categories,
                'values': values,
                'chart_type': 'bar'
            }
        
        elif chart.chart_type == ChartType.PIE:
            categories = ['Desktop', 'Mobile', 'Tablet']
            values = [45, 40, 15]
            return {
                'labels': categories,
                'values': values,
                'chart_type': 'pie'
            }
        
        else:
            return {'labels': [], 'values': [], 'chart_type': chart.chart_type.value}
    
    def _generate_charts(self, definition: ReportDefinition, report_data: Dict[str, Any]) -> str:
        """Generate HTML charts using Chart.js."""
        charts_html = []
        
        for chart in definition.charts:
            chart_data = report_data['charts'].get(chart.title, {})
            
            if 'error' in chart_data:
                charts_html.append(f'<div class="chart-error">Error loading chart: {chart.title}</div>')
                continue
            
            chart_id = f"chart_{chart.title.replace(' ', '_').lower()}"
            
            chart_html = f"""
            <div class="chart-container">
                <h3>{chart.title}</h3>
                <canvas id="{chart_id}" width="400" height="200"></canvas>
                <script>
                    var ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
                    var chart_{chart_id} = new Chart(ctx_{chart_id}, {{
                        type: '{chart_data.get('chart_type', 'bar')}',
                        data: {{
                            labels: {json.dumps(chart_data.get('labels', []))},
                            datasets: [{{
                                label: '{chart.title}',
                                data: {json.dumps(chart_data.get('values', []))},
                                backgroundColor: [
                                    'rgba(54, 162, 235, 0.2)',
                                    'rgba(255, 99, 132, 0.2)',
                                    'rgba(255, 205, 86, 0.2)',
                                    'rgba(75, 192, 192, 0.2)',
                                    'rgba(153, 102, 255, 0.2)',
                                ],
                                borderColor: [
                                    'rgba(54, 162, 235, 1)',
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(255, 205, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(153, 102, 255, 1)',
                                ],
                                borderWidth: 1
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            scales: {{
                                y: {{
                                    beginAtZero: true
                                }}
                            }}
                        }}
                    }});
                </script>
            </div>
            """
            charts_html.append(chart_html)
        
        return '\n'.join(charts_html)
    
    def _generate_html_report(
        self, 
        definition: ReportDefinition, 
        report_data: Dict[str, Any], 
        charts_html: str
    ) -> str:
        """Generate HTML report."""
        
        # Create HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ report_name }}</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; text-align: center; }
                .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
                .metric-label { color: #666; }
                .chart-container { margin-bottom: 30px; }
                .chart-error { color: red; padding: 10px; border: 1px solid red; border-radius: 5px; }
                .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report_name }}</h1>
                <p>{{ description }}</p>
                <p><strong>Generated:</strong> {{ generated_at }}</p>
                {% if date_range %}
                <p><strong>Date Range:</strong> {{ date_range.start }} to {{ date_range.end }}</p>
                {% endif %}
            </div>
            
            <div class="metrics-grid">
                {% for metric_name, metric_data in metrics.items() %}
                <div class="metric-card">
                    <div class="metric-value">{{ metric_data.value | format_by_type(metric_data.format_type) }}</div>
                    <div class="metric-label">{{ metric_data.display_name }}</div>
                    {% if metric_data.description %}
                    <div class="metric-description">{{ metric_data.description }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div class="charts-section">
                {{ charts_html | safe }}
            </div>
            
            <div class="footer">
                <p>Report generated by MarTech Integration Hub on {{ generated_at }}</p>
            </div>
        </body>
        </html>
        """
        
        # Add custom filter for formatting
        def format_by_type(value, format_type):
            if format_type == 'currency':
                return self._format_currency(value)
            elif format_type == 'percentage':
                return self._format_percentage(value)
            else:
                return self._format_number(value)
        
        self.jinja_env.filters['format_by_type'] = format_by_type
        
        template = self.jinja_env.from_string(html_template)
        
        return template.render(
            report_name=definition.name,
            description=definition.description,
            generated_at=report_data['metadata']['generated_at'].strftime('%Y-%m-%d %H:%M:%S'),
            date_range=definition.date_range,
            metrics=report_data['metrics'],
            charts_html=charts_html
        )
    
    def _generate_json_report(self, definition: ReportDefinition, report_data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        json_data = {
            'report_definition': {
                'name': definition.name,
                'description': definition.description,
                'created_at': definition.created_at.isoformat() if definition.created_at else None
            },
            'data': report_data,
            'generated_at': datetime.now().isoformat()
        }
        
        return json.dumps(json_data, indent=2, default=str)
    
    def _generate_csv_report(self, definition: ReportDefinition, report_data: Dict[str, Any]) -> str:
        """Generate CSV report."""
        
        # Create DataFrame from metrics
        metrics_data = []
        for metric_name, metric_info in report_data['metrics'].items():
            metrics_data.append({
                'Metric': metric_info.get('display_name', metric_name),
                'Value': metric_info.get('value', 'N/A'),
                'Description': metric_info.get('description', '')
            })
        
        df = pd.DataFrame(metrics_data)
        return df.to_csv(index=False)
    
    def _generate_excel_report(self, definition: ReportDefinition, report_data: Dict[str, Any]) -> bytes:
        """Generate Excel report."""
        
        # Create Excel file with multiple sheets
        from io import BytesIO
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Metrics sheet
            metrics_data = []
            for metric_name, metric_info in report_data['metrics'].items():
                metrics_data.append({
                    'Metric': metric_info.get('display_name', metric_name),
                    'Value': metric_info.get('value', 'N/A'),
                    'Format': metric_info.get('format_type', 'number'),
                    'Description': metric_info.get('description', '')
                })
            
            metrics_df = pd.DataFrame(metrics_data)
            metrics_df.to_sheet(writer, sheet_name='Metrics', index=False)
            
            # Chart data sheets
            for chart_name, chart_data in report_data['charts'].items():
                if 'error' not in chart_data:
                    chart_df = pd.DataFrame({
                        'Label': chart_data.get('labels', []),
                        'Value': chart_data.get('values', [])
                    })
                    safe_sheet_name = chart_name.replace(' ', '_')[:31]  # Excel sheet name limit
                    chart_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
        
        output.seek(0)
        return output.read()
    
    def _save_report(self, content: Union[str, bytes], output_path: str, format_type: ReportFormat):
        """Save report to file."""
        try:
            mode = 'wb' if format_type in [ReportFormat.PDF, ReportFormat.EXCEL] else 'w'
            
            with open(output_path, mode) as f:
                f.write(content)
            
            logger.info(f"Report saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise
    
    def _format_currency(self, value: Union[int, float]) -> str:
        """Format value as currency."""
        try:
            return f"${float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_percentage(self, value: Union[int, float]) -> str:
        """Format value as percentage."""
        try:
            return f"{float(value):.1f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _format_number(self, value: Union[int, float]) -> str:
        """Format value as number."""
        try:
            return f"{float(value):,.0f}"
        except (ValueError, TypeError):
            return str(value)
    
    def save_report_template(self, definition: ReportDefinition, template_name: str):
        """Save a report definition as a reusable template."""
        self.report_templates[template_name] = definition
        logger.info(f"Saved report template: {template_name}")
    
    def load_report_template(self, template_name: str) -> Optional[ReportDefinition]:
        """Load a saved report template."""
        return self.report_templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List all available report templates."""
        return list(self.report_templates.keys())
    
    def schedule_report(self, definition: ReportDefinition, schedule: str, output_path: str):
        """Schedule a report to run automatically."""
        # This would integrate with a job scheduler like Celery or cron
        logger.info(f"Scheduled report '{definition.name}' with schedule: {schedule}")
        
        # For now, just store the schedule info
        definition.refresh_schedule = schedule
        
        return {
            'report_name': definition.name,
            'schedule': schedule,
            'output_path': output_path,
            'next_run': 'Would be calculated based on schedule'
        }


# Example usage and preset report templates
def create_marketing_overview_template() -> ReportDefinition:
    """Create a standard marketing overview report template."""
    
    metrics = [
        {
            'name': 'total_sessions',
            'display_name': 'Total Sessions',
            'data_source': 'analytics',
            'aggregation': 'sum',
            'format_type': 'number'
        },
        {
            'name': 'conversion_rate',
            'display_name': 'Conversion Rate',
            'data_source': 'analytics',
            'aggregation': 'avg',
            'format_type': 'percentage'
        },
        {
            'name': 'total_revenue',
            'display_name': 'Total Revenue',
            'data_source': 'analytics',
            'aggregation': 'sum',
            'format_type': 'currency'
        },
        {
            'name': 'cost_per_acquisition',
            'display_name': 'Cost Per Acquisition',
            'data_source': 'advertising',
            'aggregation': 'avg',
            'format_type': 'currency'
        }
    ]
    
    charts = [
        {
            'title': 'Traffic Trend',
            'chart_type': 'line',
            'data_source': 'analytics',
            'x_axis': 'date',
            'y_axis': 'sessions'
        },
        {
            'title': 'Traffic Sources',
            'chart_type': 'pie',
            'data_source': 'analytics',
            'x_axis': 'source',
            'y_axis': 'sessions'
        },
        {
            'title': 'Channel Performance',
            'chart_type': 'bar',
            'data_source': 'analytics',
            'x_axis': 'channel',
            'y_axis': 'conversions'
        }
    ]
    
    builder = CustomReportBuilder()
    return builder.create_report_definition(
        name="Marketing Overview",
        description="Comprehensive overview of marketing performance metrics",
        metrics=metrics,
        charts=charts,
        date_range={'start': '2024-01-01', 'end': '2024-01-31'}
    )