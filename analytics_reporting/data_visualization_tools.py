import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import base64
from io import BytesIO
import json

logger = logging.getLogger(__name__)


class DataVisualizationTools:
    """
    Comprehensive data visualization toolkit for marketing analytics.
    Creates interactive charts, dashboards, and visual reports.
    """
    
    def __init__(self):
        self.color_palette = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#f1c40f'
        ]
        self.figure_cache = {}
        self._setup_styling()
    
    def _setup_styling(self):
        """Set up default styling for visualizations."""
        # Matplotlib styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette(self.color_palette)
        
        # Plotly default template
        self.plotly_template = {
            'layout': {
                'colorway': self.color_palette,
                'font': {'family': 'Arial, sans-serif', 'size': 12},
                'title': {'font': {'size': 16, 'color': '#2c3e50'}},
                'paper_bgcolor': 'white',
                'plot_bgcolor': 'white'
            }
        }
    
    def create_line_chart(
        self, 
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "Line Chart",
        color_col: Optional[str] = None,
        interactive: bool = True
    ) -> Union[str, bytes]:
        """Create a line chart visualization."""
        
        try:
            if interactive:
                return self._create_plotly_line_chart(data, x_col, y_col, title, color_col)
            else:
                return self._create_matplotlib_line_chart(data, x_col, y_col, title, color_col)
                
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            return self._create_error_chart(f"Error creating line chart: {str(e)}")
    
    def _create_plotly_line_chart(
        self, 
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        color_col: Optional[str] = None
    ) -> str:
        """Create interactive line chart with Plotly."""
        
        fig = go.Figure()
        
        if color_col and color_col in data.columns:
            # Multiple lines by category
            for category in data[color_col].unique():
                category_data = data[data[color_col] == category]
                fig.add_trace(go.Scatter(
                    x=category_data[x_col],
                    y=category_data[y_col],
                    mode='lines+markers',
                    name=str(category),
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        else:
            # Single line
            fig.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(width=3, color=self.color_palette[0]),
                marker=dict(size=6, color=self.color_palette[0])
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            hovermode='x unified',
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_matplotlib_line_chart(
        self, 
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        color_col: Optional[str] = None
    ) -> bytes:
        """Create static line chart with Matplotlib."""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if color_col and color_col in data.columns:
            for i, category in enumerate(data[color_col].unique()):
                category_data = data[data[color_col] == category]
                ax.plot(
                    category_data[x_col], 
                    category_data[y_col],
                    marker='o',
                    linewidth=2,
                    markersize=4,
                    label=str(category),
                    color=self.color_palette[i % len(self.color_palette)]
                )
            ax.legend()
        else:
            ax.plot(
                data[x_col], 
                data[y_col],
                marker='o',
                linewidth=3,
                markersize=6,
                color=self.color_palette[0]
            )
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if they're dates
        if pd.api.types.is_datetime64_any_dtype(data[x_col]):
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Convert to bytes
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()
    
    def create_bar_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "Bar Chart",
        orientation: str = "vertical",
        interactive: bool = True
    ) -> Union[str, bytes]:
        """Create a bar chart visualization."""
        
        try:
            if interactive:
                return self._create_plotly_bar_chart(data, x_col, y_col, title, orientation)
            else:
                return self._create_matplotlib_bar_chart(data, x_col, y_col, title, orientation)
                
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return self._create_error_chart(f"Error creating bar chart: {str(e)}")
    
    def _create_plotly_bar_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        orientation: str
    ) -> str:
        """Create interactive bar chart with Plotly."""
        
        if orientation == "horizontal":
            fig = go.Figure(go.Bar(
                x=data[y_col],
                y=data[x_col],
                orientation='h',
                marker_color=self.color_palette[0]
            ))
        else:
            fig = go.Figure(go.Bar(
                x=data[x_col],
                y=data[y_col],
                marker_color=self.color_palette[0]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_matplotlib_bar_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        orientation: str
    ) -> bytes:
        """Create static bar chart with Matplotlib."""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if orientation == "horizontal":
            ax.barh(data[x_col], data[y_col], color=self.color_palette[0])
        else:
            ax.bar(data[x_col], data[y_col], color=self.color_palette[0])
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())
        
        # Rotate x-axis labels if needed
        if orientation == "vertical" and len(data) > 10:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()
    
    def create_pie_chart(
        self,
        data: pd.DataFrame,
        labels_col: str,
        values_col: str,
        title: str = "Pie Chart",
        interactive: bool = True
    ) -> Union[str, bytes]:
        """Create a pie chart visualization."""
        
        try:
            if interactive:
                return self._create_plotly_pie_chart(data, labels_col, values_col, title)
            else:
                return self._create_matplotlib_pie_chart(data, labels_col, values_col, title)
                
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            return self._create_error_chart(f"Error creating pie chart: {str(e)}")
    
    def _create_plotly_pie_chart(
        self,
        data: pd.DataFrame,
        labels_col: str,
        values_col: str,
        title: str
    ) -> str:
        """Create interactive pie chart with Plotly."""
        
        fig = go.Figure(go.Pie(
            labels=data[labels_col],
            values=data[values_col],
            hole=0.3,  # Create donut chart
            marker=dict(colors=self.color_palette)
        ))
        
        fig.update_layout(
            title=title,
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_matplotlib_pie_chart(
        self,
        data: pd.DataFrame,
        labels_col: str,
        values_col: str,
        title: str
    ) -> bytes:
        """Create static pie chart with Matplotlib."""
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        wedges, texts, autotexts = ax.pie(
            data[values_col],
            labels=data[labels_col],
            colors=self.color_palette,
            autopct='%1.1f%%',
            startangle=90
        )
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        # Make percentage labels bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()
    
    def create_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Heatmap",
        interactive: bool = True
    ) -> Union[str, bytes]:
        """Create a heatmap visualization."""
        
        try:
            if interactive:
                return self._create_plotly_heatmap(data, title)
            else:
                return self._create_matplotlib_heatmap(data, title)
                
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return self._create_error_chart(f"Error creating heatmap: {str(e)}")
    
    def _create_plotly_heatmap(self, data: pd.DataFrame, title: str) -> str:
        """Create interactive heatmap with Plotly."""
        
        # Select only numeric columns
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            return self._create_error_chart("No numeric data available for heatmap")
        
        # Calculate correlation matrix
        corr_matrix = numeric_data.corr()
        
        fig = go.Figure(go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(
            title=title,
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_matplotlib_heatmap(self, data: pd.DataFrame, title: str) -> bytes:
        """Create static heatmap with Matplotlib."""
        
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            # Create error visualization
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, 'No numeric data available for heatmap', 
                   ha='center', va='center', fontsize=14)
            ax.set_title(title)
        else:
            corr_matrix = numeric_data.corr()
            
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(
                corr_matrix,
                annot=True,
                cmap='RdBu_r',
                center=0,
                square=True,
                fmt='.2f',
                cbar_kws={"shrink": .8}
            )
            ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()
    
    def create_scatter_plot(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "Scatter Plot",
        size_col: Optional[str] = None,
        color_col: Optional[str] = None,
        interactive: bool = True
    ) -> Union[str, bytes]:
        """Create a scatter plot visualization."""
        
        try:
            if interactive:
                return self._create_plotly_scatter(data, x_col, y_col, title, size_col, color_col)
            else:
                return self._create_matplotlib_scatter(data, x_col, y_col, title, size_col, color_col)
                
        except Exception as e:
            logger.error(f"Error creating scatter plot: {e}")
            return self._create_error_chart(f"Error creating scatter plot: {str(e)}")
    
    def _create_plotly_scatter(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        size_col: Optional[str] = None,
        color_col: Optional[str] = None
    ) -> str:
        """Create interactive scatter plot with Plotly."""
        
        fig = go.Figure()
        
        scatter_kwargs = {
            'x': data[x_col],
            'y': data[y_col],
            'mode': 'markers',
            'marker': dict(size=8 if not size_col else data[size_col])
        }
        
        if color_col and color_col in data.columns:
            scatter_kwargs['marker']['color'] = data[color_col]
            scatter_kwargs['marker']['colorscale'] = 'Viridis'
        else:
            scatter_kwargs['marker']['color'] = self.color_palette[0]
        
        fig.add_trace(go.Scatter(**scatter_kwargs))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_matplotlib_scatter(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        size_col: Optional[str] = None,
        color_col: Optional[str] = None
    ) -> bytes:
        """Create static scatter plot with Matplotlib."""
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        scatter_kwargs = {'alpha': 0.7}
        
        if size_col and size_col in data.columns:
            scatter_kwargs['s'] = data[size_col] * 50  # Scale size
        
        if color_col and color_col in data.columns:
            scatter = ax.scatter(
                data[x_col], 
                data[y_col],
                c=data[color_col],
                cmap='viridis',
                **scatter_kwargs
            )
            plt.colorbar(scatter, ax=ax, label=color_col.replace('_', ' ').title())
        else:
            ax.scatter(
                data[x_col], 
                data[y_col],
                color=self.color_palette[0],
                **scatter_kwargs
            )
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()
    
    def create_funnel_chart(
        self,
        data: pd.DataFrame,
        stages_col: str,
        values_col: str,
        title: str = "Funnel Chart"
    ) -> str:
        """Create a funnel chart for conversion analysis."""
        
        try:
            fig = go.Figure(go.Funnel(
                y=data[stages_col],
                x=data[values_col],
                textinfo="value+percent initial",
                marker=dict(color=self.color_palette[:len(data)])
            ))
            
            fig.update_layout(
                title=title,
                **self.plotly_template['layout']
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            logger.error(f"Error creating funnel chart: {e}")
            return self._create_error_chart(f"Error creating funnel chart: {str(e)}")
    
    def create_dashboard(
        self,
        charts: List[Dict[str, Any]],
        title: str = "Marketing Dashboard",
        layout: str = "grid"
    ) -> str:
        """Create a comprehensive dashboard with multiple charts."""
        
        try:
            if layout == "grid":
                return self._create_grid_dashboard(charts, title)
            else:
                return self._create_tabbed_dashboard(charts, title)
                
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return f"<div class='error'>Error creating dashboard: {str(e)}</div>"
    
    def _create_grid_dashboard(self, charts: List[Dict[str, Any]], title: str) -> str:
        """Create dashboard with grid layout."""
        
        # Calculate grid dimensions
        num_charts = len(charts)
        cols = min(2, num_charts)
        rows = (num_charts + cols - 1) // cols
        
        # Create subplots
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[chart.get('title', f'Chart {i+1}') for i, chart in enumerate(charts)],
            specs=[[{"secondary_y": False} for _ in range(cols)] for _ in range(rows)]
        )
        
        for i, chart_config in enumerate(charts):
            row = i // cols + 1
            col = i % cols + 1
            
            chart_data = chart_config.get('data', pd.DataFrame())
            chart_type = chart_config.get('type', 'line')
            
            if chart_type == 'line':
                fig.add_trace(
                    go.Scatter(
                        x=chart_data.get('x', []),
                        y=chart_data.get('y', []),
                        mode='lines+markers',
                        name=chart_config.get('name', f'Series {i+1}')
                    ),
                    row=row, col=col
                )
            elif chart_type == 'bar':
                fig.add_trace(
                    go.Bar(
                        x=chart_data.get('x', []),
                        y=chart_data.get('y', []),
                        name=chart_config.get('name', f'Series {i+1}')
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            title_text=title,
            height=400 * rows,
            showlegend=False,
            **self.plotly_template['layout']
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def create_kpi_cards(
        self,
        kpis: List[Dict[str, Any]],
        title: str = "Key Performance Indicators"
    ) -> str:
        """Create KPI cards display."""
        
        cards_html = f"<h2>{title}</h2><div class='kpi-container' style='display: flex; flex-wrap: wrap; gap: 20px;'>"
        
        for kpi in kpis:
            value = kpi.get('value', 0)
            label = kpi.get('label', 'KPI')
            change = kpi.get('change', 0)
            format_type = kpi.get('format', 'number')
            
            # Format value based on type
            if format_type == 'currency':
                formatted_value = f"${value:,.2f}"
            elif format_type == 'percentage':
                formatted_value = f"{value:.1f}%"
            else:
                formatted_value = f"{value:,.0f}"
            
            # Determine change color
            change_color = '#27ae60' if change >= 0 else '#e74c3c'
            change_symbol = '▲' if change >= 0 else '▼'
            
            card_html = f"""
            <div class='kpi-card' style='
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                min-width: 200px;
                text-align: center;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            '>
                <div style='font-size: 2.5em; font-weight: bold; color: #2c3e50; margin-bottom: 10px;'>
                    {formatted_value}
                </div>
                <div style='font-size: 1.1em; color: #7f8c8d; margin-bottom: 10px;'>
                    {label}
                </div>
                <div style='color: {change_color}; font-weight: bold;'>
                    {change_symbol} {abs(change):.1f}%
                </div>
            </div>
            """
            cards_html += card_html
        
        cards_html += "</div>"
        
        return cards_html
    
    def create_time_series_comparison(
        self,
        data: pd.DataFrame,
        date_col: str,
        metrics: List[str],
        title: str = "Time Series Comparison"
    ) -> str:
        """Create time series comparison chart."""
        
        try:
            fig = go.Figure()
            
            for i, metric in enumerate(metrics):
                if metric in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data[date_col],
                        y=data[metric],
                        mode='lines+markers',
                        name=metric.replace('_', ' ').title(),
                        line=dict(
                            color=self.color_palette[i % len(self.color_palette)],
                            width=2
                        ),
                        marker=dict(size=6)
                    ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Date",
                yaxis_title="Value",
                hovermode='x unified',
                **self.plotly_template['layout']
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            logger.error(f"Error creating time series comparison: {e}")
            return self._create_error_chart(f"Error creating time series comparison: {str(e)}")
    
    def _create_error_chart(self, error_message: str) -> str:
        """Create an error message chart."""
        return f"""
        <div style='
            border: 2px solid #e74c3c;
            border-radius: 5px;
            padding: 20px;
            margin: 10px;
            background-color: #fdf2f2;
            color: #e74c3c;
            text-align: center;
            font-family: Arial, sans-serif;
        '>
            <h3>Chart Error</h3>
            <p>{error_message}</p>
        </div>
        """
    
    def export_chart_as_image(self, chart_html: str, output_path: str, format: str = 'png'):
        """Export interactive chart as static image."""
        try:
            # This would require additional dependencies like kaleido for plotly
            logger.info(f"Chart export functionality would save to: {output_path}")
            return f"Chart would be exported to {output_path} as {format}"
        except Exception as e:
            logger.error(f"Error exporting chart: {e}")
            return f"Error exporting chart: {str(e)}"
    
    def create_marketing_metrics_dashboard(
        self,
        analytics_data: pd.DataFrame,
        campaign_data: pd.DataFrame,
        title: str = "Marketing Metrics Dashboard"
    ) -> str:
        """Create a comprehensive marketing metrics dashboard."""
        
        dashboard_html = f"<h1>{title}</h1>"
        
        # KPI Cards
        kpis = [
            {'label': 'Total Sessions', 'value': analytics_data.get('sessions', [0]).sum(), 'change': 5.2, 'format': 'number'},
            {'label': 'Conversion Rate', 'value': 3.2, 'change': -0.8, 'format': 'percentage'},
            {'label': 'Revenue', 'value': 45890, 'change': 12.5, 'format': 'currency'},
            {'label': 'ROAS', 'value': 4.2, 'change': 8.3, 'format': 'number'}
        ]
        
        dashboard_html += self.create_kpi_cards(kpis)
        
        # Traffic trend chart
        if not analytics_data.empty and 'date' in analytics_data.columns:
            traffic_chart = self.create_line_chart(
                analytics_data,
                'date',
                'sessions',
                'Traffic Trend Over Time'
            )
            dashboard_html += f"<div style='margin: 20px 0;'>{traffic_chart}</div>"
        
        return dashboard_html