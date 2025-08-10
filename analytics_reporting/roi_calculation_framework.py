"""
ROI Calculation Framework for MarTech Integration Hub

Comprehensive return on investment analysis for marketing campaigns, channels,
and initiatives with advanced attribution modeling and financial metrics.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import json
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class ROIMetricType(Enum):
    SIMPLE_ROI = "simple_roi"
    ROAS = "return_on_ad_spend"
    CUSTOMER_LTV_ROI = "customer_ltv_roi"
    INCREMENTAL_ROI = "incremental_roi"
    BLENDED_ROI = "blended_roi"
    CHANNEL_ROI = "channel_roi"
    CAMPAIGN_ROI = "campaign_roi"


class AttributionModel(Enum):
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"


class TimeFrame(Enum):
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


@dataclass
class ROICalculation:
    """ROI calculation result with comprehensive metrics."""
    metric_type: str
    roi_value: float
    roi_percentage: float
    total_revenue: float
    total_investment: float
    profit: float
    calculation_date: datetime
    time_period: str
    attribution_model: str
    confidence_score: float
    data_points: int
    breakdown: Dict[str, Any]
    recommendations: List[str]


@dataclass
class InvestmentData:
    """Investment/cost data structure."""
    source: str
    amount: float
    date: datetime
    category: str
    campaign_id: Optional[str] = None
    channel: Optional[str] = None
    tags: Dict[str, Any] = None


@dataclass
class RevenueData:
    """Revenue data structure with attribution."""
    source: str
    amount: float
    date: datetime
    customer_id: Optional[str] = None
    conversion_path: Optional[List[str]] = None
    attribution_weight: float = 1.0
    campaign_id: Optional[str] = None
    channel: Optional[str] = None
    tags: Dict[str, Any] = None


class ROICalculationFramework:
    """
    Comprehensive ROI calculation framework for marketing analytics.
    
    Provides multiple ROI calculation methods, attribution modeling,
    and advanced financial analysis for marketing investments.
    """
    
    def __init__(self):
        self.investment_data = []
        self.revenue_data = []
        self.attribution_weights = {}
        self.baseline_metrics = {}
        self.calculation_cache = {}
        
        # Configuration
        self.default_attribution_model = AttributionModel.LINEAR
        self.default_time_decay_days = 30
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # Industry benchmarks for comparison
        self.industry_benchmarks = {
            'email_marketing': {'roi': 4200, 'min': 3800, 'max': 4400},
            'social_media': {'roi': 275, 'min': 200, 'max': 350},
            'content_marketing': {'roi': 300, 'min': 250, 'max': 400},
            'ppc_advertising': {'roi': 200, 'min': 150, 'max': 300},
            'seo': {'roi': 500, 'min': 400, 'max': 650},
            'influencer_marketing': {'roi': 650, 'min': 500, 'max': 800}
        }
    
    def add_investment_data(
        self,
        investments: Union[List[InvestmentData], pd.DataFrame, Dict[str, Any]]
    ):
        """Add investment/cost data for ROI calculations."""
        
        try:
            if isinstance(investments, pd.DataFrame):
                for _, row in investments.iterrows():
                    investment = InvestmentData(
                        source=row.get('source', 'unknown'),
                        amount=float(row.get('amount', 0)),
                        date=pd.to_datetime(row.get('date', datetime.now())),
                        category=row.get('category', 'marketing'),
                        campaign_id=row.get('campaign_id'),
                        channel=row.get('channel'),
                        tags=row.get('tags', {})
                    )
                    self.investment_data.append(investment)
            
            elif isinstance(investments, list):
                self.investment_data.extend(investments)
            
            elif isinstance(investments, dict):
                investment = InvestmentData(**investments)
                self.investment_data.append(investment)
            
            logger.info(f"Added {len(investments) if hasattr(investments, '__len__') else 1} investment records")
            
        except Exception as e:
            logger.error(f"Error adding investment data: {e}")
            raise
    
    def add_revenue_data(
        self,
        revenue: Union[List[RevenueData], pd.DataFrame, Dict[str, Any]]
    ):
        """Add revenue data for ROI calculations."""
        
        try:
            if isinstance(revenue, pd.DataFrame):
                for _, row in revenue.iterrows():
                    rev = RevenueData(
                        source=row.get('source', 'unknown'),
                        amount=float(row.get('amount', 0)),
                        date=pd.to_datetime(row.get('date', datetime.now())),
                        customer_id=row.get('customer_id'),
                        conversion_path=row.get('conversion_path', []),
                        attribution_weight=float(row.get('attribution_weight', 1.0)),
                        campaign_id=row.get('campaign_id'),
                        channel=row.get('channel'),
                        tags=row.get('tags', {})
                    )
                    self.revenue_data.append(rev)
            
            elif isinstance(revenue, list):
                self.revenue_data.extend(revenue)
            
            elif isinstance(revenue, dict):
                rev = RevenueData(**revenue)
                self.revenue_data.append(rev)
            
            logger.info(f"Added {len(revenue) if hasattr(revenue, '__len__') else 1} revenue records")
            
        except Exception as e:
            logger.error(f"Error adding revenue data: {e}")
            raise
    
    def calculate_simple_roi(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ROICalculation:
        """
        Calculate simple ROI: (Revenue - Investment) / Investment * 100.
        
        Args:
            start_date: Start date for calculation period
            end_date: End date for calculation period
            filters: Additional filters for data selection
        """
        
        try:
            logger.info("Calculating simple ROI")
            
            # Filter data by date range and filters
            filtered_investments = self._filter_investments(start_date, end_date, filters)
            filtered_revenue = self._filter_revenue(start_date, end_date, filters)
            
            if not filtered_investments or not filtered_revenue:
                raise ValueError("Insufficient data for ROI calculation")
            
            # Calculate totals
            total_investment = sum(inv.amount for inv in filtered_investments)
            total_revenue = sum(rev.amount for rev in filtered_revenue)
            
            if total_investment == 0:
                raise ValueError("Total investment cannot be zero")
            
            # Calculate ROI
            profit = total_revenue - total_investment
            roi_value = profit / total_investment
            roi_percentage = roi_value * 100
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                len(filtered_investments) + len(filtered_revenue),
                roi_percentage
            )
            
            # Generate breakdown
            breakdown = self._generate_roi_breakdown(filtered_investments, filtered_revenue)
            
            # Generate recommendations
            recommendations = self._generate_roi_recommendations(roi_percentage, breakdown)
            
            return ROICalculation(
                metric_type=ROIMetricType.SIMPLE_ROI.value,
                roi_value=roi_value,
                roi_percentage=roi_percentage,
                total_revenue=total_revenue,
                total_investment=total_investment,
                profit=profit,
                calculation_date=datetime.now(),
                time_period=self._format_time_period(start_date, end_date),
                attribution_model="none",
                confidence_score=confidence_score,
                data_points=len(filtered_investments) + len(filtered_revenue),
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating simple ROI: {e}")
            raise
    
    def calculate_roas(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ROICalculation:
        """
        Calculate Return on Ad Spend (ROAS): Revenue / Ad Spend.
        
        Focuses specifically on advertising spend vs. revenue generated.
        """
        
        try:
            logger.info("Calculating ROAS (Return on Ad Spend)")
            
            # Filter for advertising spend only
            ad_filters = filters or {}
            ad_filters.update({'category': ['advertising', 'ppc', 'social_ads', 'display']})
            
            filtered_investments = self._filter_investments(start_date, end_date, ad_filters)
            filtered_revenue = self._filter_revenue(start_date, end_date, filters)
            
            if not filtered_investments:
                raise ValueError("No advertising spend data found")
            
            if not filtered_revenue:
                raise ValueError("No revenue data found")
            
            total_ad_spend = sum(inv.amount for inv in filtered_investments)
            total_revenue = sum(rev.amount for rev in filtered_revenue)
            
            if total_ad_spend == 0:
                raise ValueError("Total ad spend cannot be zero")
            
            # ROAS calculation
            roas_value = total_revenue / total_ad_spend
            roas_percentage = roas_value * 100
            profit = total_revenue - total_ad_spend
            
            confidence_score = self._calculate_confidence_score(
                len(filtered_investments) + len(filtered_revenue),
                roas_percentage
            )
            
            breakdown = {
                'total_ad_spend': total_ad_spend,
                'total_revenue': total_revenue,
                'profit_margin': (profit / total_revenue * 100) if total_revenue > 0 else 0,
                'spend_by_channel': self._group_by_channel(filtered_investments),
                'revenue_by_channel': self._group_by_channel(filtered_revenue),
                'roas_by_channel': self._calculate_channel_roas(filtered_investments, filtered_revenue)
            }
            
            recommendations = self._generate_roas_recommendations(roas_value, breakdown)
            
            return ROICalculation(
                metric_type=ROIMetricType.ROAS.value,
                roi_value=roas_value,
                roi_percentage=roas_percentage,
                total_revenue=total_revenue,
                total_investment=total_ad_spend,
                profit=profit,
                calculation_date=datetime.now(),
                time_period=self._format_time_period(start_date, end_date),
                attribution_model="none",
                confidence_score=confidence_score,
                data_points=len(filtered_investments) + len(filtered_revenue),
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating ROAS: {e}")
            raise
    
    def calculate_attributed_roi(
        self,
        attribution_model: AttributionModel = AttributionModel.LINEAR,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ROICalculation:
        """
        Calculate ROI with advanced attribution modeling.
        
        Args:
            attribution_model: Attribution model to use for revenue allocation
            start_date: Start date for calculation period
            end_date: End date for calculation period
            filters: Additional filters for data selection
        """
        
        try:
            logger.info(f"Calculating attributed ROI using {attribution_model.value} model")
            
            # Apply attribution modeling to revenue data
            attributed_revenue = self._apply_attribution_model(
                self.revenue_data, attribution_model, start_date, end_date
            )
            
            filtered_investments = self._filter_investments(start_date, end_date, filters)
            
            if not filtered_investments or not attributed_revenue:
                raise ValueError("Insufficient data for attributed ROI calculation")
            
            # Calculate ROI with attributed revenue
            total_investment = sum(inv.amount for inv in filtered_investments)
            total_attributed_revenue = sum(rev.amount * rev.attribution_weight for rev in attributed_revenue)
            
            if total_investment == 0:
                raise ValueError("Total investment cannot be zero")
            
            profit = total_attributed_revenue - total_investment
            roi_value = profit / total_investment
            roi_percentage = roi_value * 100
            
            confidence_score = self._calculate_confidence_score(
                len(filtered_investments) + len(attributed_revenue),
                roi_percentage,
                attribution_adjustment=True
            )
            
            breakdown = {
                'attribution_model': attribution_model.value,
                'total_attributed_revenue': total_attributed_revenue,
                'attribution_breakdown': self._generate_attribution_breakdown(attributed_revenue),
                'channel_attribution': self._calculate_channel_attribution(attributed_revenue),
                'touchpoint_analysis': self._analyze_touchpoints(attributed_revenue)
            }
            
            recommendations = self._generate_attribution_recommendations(
                roi_percentage, attribution_model, breakdown
            )
            
            return ROICalculation(
                metric_type=ROIMetricType.INCREMENTAL_ROI.value,
                roi_value=roi_value,
                roi_percentage=roi_percentage,
                total_revenue=total_attributed_revenue,
                total_investment=total_investment,
                profit=profit,
                calculation_date=datetime.now(),
                time_period=self._format_time_period(start_date, end_date),
                attribution_model=attribution_model.value,
                confidence_score=confidence_score,
                data_points=len(filtered_investments) + len(attributed_revenue),
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating attributed ROI: {e}")
            raise
    
    def calculate_customer_ltv_roi(
        self,
        customer_ltv_data: pd.DataFrame,
        acquisition_cost_data: pd.DataFrame
    ) -> ROICalculation:
        """
        Calculate ROI based on Customer Lifetime Value.
        
        Args:
            customer_ltv_data: DataFrame with customer_id and ltv columns
            acquisition_cost_data: DataFrame with customer_id and acquisition_cost columns
        """
        
        try:
            logger.info("Calculating Customer LTV ROI")
            
            # Merge LTV and acquisition cost data
            ltv_roi_data = customer_ltv_data.merge(
                acquisition_cost_data,
                on='customer_id',
                how='inner'
            )
            
            if ltv_roi_data.empty:
                raise ValueError("No matching customer data for LTV ROI calculation")
            
            total_ltv = ltv_roi_data['ltv'].sum()
            total_acquisition_cost = ltv_roi_data['acquisition_cost'].sum()
            
            if total_acquisition_cost == 0:
                raise ValueError("Total acquisition cost cannot be zero")
            
            # LTV ROI calculation
            ltv_profit = total_ltv - total_acquisition_cost
            ltv_roi = ltv_profit / total_acquisition_cost
            ltv_roi_percentage = ltv_roi * 100
            
            # Calculate additional metrics
            avg_ltv = ltv_roi_data['ltv'].mean()
            avg_cac = ltv_roi_data['acquisition_cost'].mean()
            ltv_cac_ratio = avg_ltv / avg_cac if avg_cac > 0 else 0
            
            confidence_score = self._calculate_confidence_score(
                len(ltv_roi_data),
                ltv_roi_percentage,
                data_quality_bonus=0.1  # LTV data typically higher quality
            )
            
            breakdown = {
                'total_customers': len(ltv_roi_data),
                'average_ltv': avg_ltv,
                'average_cac': avg_cac,
                'ltv_cac_ratio': ltv_cac_ratio,
                'ltv_distribution': self._analyze_ltv_distribution(ltv_roi_data),
                'cohort_analysis': self._perform_ltv_cohort_analysis(ltv_roi_data)
            }
            
            recommendations = self._generate_ltv_recommendations(ltv_cac_ratio, breakdown)
            
            return ROICalculation(
                metric_type=ROIMetricType.CUSTOMER_LTV_ROI.value,
                roi_value=ltv_roi,
                roi_percentage=ltv_roi_percentage,
                total_revenue=total_ltv,
                total_investment=total_acquisition_cost,
                profit=ltv_profit,
                calculation_date=datetime.now(),
                time_period="lifetime",
                attribution_model="customer_level",
                confidence_score=confidence_score,
                data_points=len(ltv_roi_data),
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating Customer LTV ROI: {e}")
            raise
    
    def calculate_incremental_roi(
        self,
        test_group_data: Dict[str, pd.DataFrame],
        control_group_data: Dict[str, pd.DataFrame],
        test_period: Tuple[datetime, datetime]
    ) -> ROICalculation:
        """
        Calculate incremental ROI using test/control group analysis.
        
        Args:
            test_group_data: Data for test group (investments and revenue)
            control_group_data: Data for control group (revenue only)
            test_period: Start and end dates of the test period
        """
        
        try:
            logger.info("Calculating incremental ROI")
            
            start_date, end_date = test_period
            
            # Calculate test group metrics
            test_investment = test_group_data['investments']['amount'].sum()
            test_revenue = test_group_data['revenue']['amount'].sum()
            
            # Calculate control group metrics
            control_revenue = control_group_data['revenue']['amount'].sum()
            
            # Calculate incremental revenue
            incremental_revenue = test_revenue - control_revenue
            
            if test_investment == 0:
                raise ValueError("Test group investment cannot be zero")
            
            # Incremental ROI calculation
            incremental_profit = incremental_revenue - test_investment
            incremental_roi = incremental_profit / test_investment
            incremental_roi_percentage = incremental_roi * 100
            
            # Calculate uplift percentage
            uplift_percentage = (incremental_revenue / control_revenue * 100) if control_revenue > 0 else 0
            
            confidence_score = self._calculate_incremental_confidence(
                test_group_data, control_group_data, incremental_roi_percentage
            )
            
            breakdown = {
                'test_group_revenue': test_revenue,
                'control_group_revenue': control_revenue,
                'incremental_revenue': incremental_revenue,
                'uplift_percentage': uplift_percentage,
                'test_investment': test_investment,
                'statistical_significance': self._calculate_statistical_significance(
                    test_group_data['revenue'], control_group_data['revenue']
                )
            }
            
            recommendations = self._generate_incremental_recommendations(
                incremental_roi_percentage, uplift_percentage, breakdown
            )
            
            return ROICalculation(
                metric_type=ROIMetricType.INCREMENTAL_ROI.value,
                roi_value=incremental_roi,
                roi_percentage=incremental_roi_percentage,
                total_revenue=incremental_revenue,
                total_investment=test_investment,
                profit=incremental_profit,
                calculation_date=datetime.now(),
                time_period=self._format_time_period(start_date, end_date),
                attribution_model="incremental",
                confidence_score=confidence_score,
                data_points=len(test_group_data['investments']) + len(test_group_data['revenue']),
                breakdown=breakdown,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error calculating incremental ROI: {e}")
            raise
    
    def calculate_channel_roi_comparison(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, ROICalculation]:
        """
        Calculate and compare ROI across different marketing channels.
        
        Returns a dictionary with channel names as keys and ROI calculations as values.
        """
        
        try:
            logger.info("Calculating channel ROI comparison")
            
            # Get all unique channels
            channels = set()
            for inv in self.investment_data:
                if inv.channel:
                    channels.add(inv.channel)
            for rev in self.revenue_data:
                if rev.channel:
                    channels.add(rev.channel)
            
            channel_roi_results = {}
            
            for channel in channels:
                try:
                    # Filter data for this channel
                    channel_filter = {'channel': [channel]}
                    
                    roi_result = self.calculate_simple_roi(
                        start_date=start_date,
                        end_date=end_date,
                        filters=channel_filter
                    )
                    
                    # Add channel-specific analysis
                    roi_result.breakdown['channel_name'] = channel
                    roi_result.breakdown['industry_benchmark'] = self._get_channel_benchmark(channel)
                    roi_result.breakdown['performance_vs_benchmark'] = self._compare_to_benchmark(
                        roi_result.roi_percentage, channel
                    )
                    
                    channel_roi_results[channel] = roi_result
                    
                except Exception as e:
                    logger.warning(f"Could not calculate ROI for channel {channel}: {e}")
                    continue
            
            # Add cross-channel insights
            if len(channel_roi_results) > 1:
                self._add_cross_channel_insights(channel_roi_results)
            
            logger.info(f"Calculated ROI for {len(channel_roi_results)} channels")
            return channel_roi_results
            
        except Exception as e:
            logger.error(f"Error calculating channel ROI comparison: {e}")
            raise
    
    def generate_roi_dashboard_data(
        self,
        time_frames: List[TimeFrame] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive ROI dashboard data for visualization.
        
        Args:
            time_frames: List of time frames to analyze
        """
        
        try:
            logger.info("Generating ROI dashboard data")
            
            if time_frames is None:
                time_frames = [TimeFrame.MONTHLY, TimeFrame.QUARTERLY]
            
            dashboard_data = {
                'summary_metrics': {},
                'time_series_data': {},
                'channel_comparison': {},
                'attribution_analysis': {},
                'recommendations': [],
                'generated_at': datetime.now().isoformat()
            }
            
            # Calculate summary metrics
            current_roi = self.calculate_simple_roi(
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now()
            )
            
            dashboard_data['summary_metrics'] = {
                'current_roi': current_roi.roi_percentage,
                'total_revenue': current_roi.total_revenue,
                'total_investment': current_roi.total_investment,
                'profit': current_roi.profit,
                'confidence_score': current_roi.confidence_score
            }
            
            # Generate time series data
            for timeframe in time_frames:
                time_series = self._generate_time_series_roi(timeframe)
                dashboard_data['time_series_data'][timeframe.value] = time_series
            
            # Channel comparison
            channel_comparison = self.calculate_channel_roi_comparison()
            dashboard_data['channel_comparison'] = {
                channel: {
                    'roi_percentage': roi.roi_percentage,
                    'revenue': roi.total_revenue,
                    'investment': roi.total_investment,
                    'confidence': roi.confidence_score
                }
                for channel, roi in channel_comparison.items()
            }
            
            # Attribution analysis
            attribution_models = [
                AttributionModel.FIRST_TOUCH,
                AttributionModel.LAST_TOUCH,
                AttributionModel.LINEAR
            ]
            
            for model in attribution_models:
                try:
                    attributed_roi = self.calculate_attributed_roi(attribution_model=model)
                    dashboard_data['attribution_analysis'][model.value] = {
                        'roi_percentage': attributed_roi.roi_percentage,
                        'attribution_breakdown': attributed_roi.breakdown.get('attribution_breakdown', {})
                    }
                except Exception as e:
                    logger.warning(f"Could not calculate attribution for {model.value}: {e}")
            
            # Aggregate recommendations
            all_recommendations = []
            for roi_calc in [current_roi] + list(channel_comparison.values()):
                all_recommendations.extend(roi_calc.recommendations)
            
            # Deduplicate and prioritize recommendations
            dashboard_data['recommendations'] = self._prioritize_recommendations(all_recommendations)
            
            logger.info("ROI dashboard data generated successfully")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating ROI dashboard data: {e}")
            raise
    
    # Helper methods for calculations and analysis
    
    def _filter_investments(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        filters: Optional[Dict[str, Any]]
    ) -> List[InvestmentData]:
        """Filter investment data by date range and additional filters."""
        
        filtered = self.investment_data
        
        if start_date:
            filtered = [inv for inv in filtered if inv.date >= start_date]
        if end_date:
            filtered = [inv for inv in filtered if inv.date <= end_date]
        
        if filters:
            for key, values in filters.items():
                if key == 'category':
                    filtered = [inv for inv in filtered if inv.category in values]
                elif key == 'channel':
                    filtered = [inv for inv in filtered if inv.channel in values]
                elif key == 'campaign_id':
                    filtered = [inv for inv in filtered if inv.campaign_id in values]
        
        return filtered
    
    def _filter_revenue(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        filters: Optional[Dict[str, Any]]
    ) -> List[RevenueData]:
        """Filter revenue data by date range and additional filters."""
        
        filtered = self.revenue_data
        
        if start_date:
            filtered = [rev for rev in filtered if rev.date >= start_date]
        if end_date:
            filtered = [rev for rev in filtered if rev.date <= end_date]
        
        if filters:
            for key, values in filters.items():
                if key == 'channel':
                    filtered = [rev for rev in filtered if rev.channel in values]
                elif key == 'campaign_id':
                    filtered = [rev for rev in filtered if rev.campaign_id in values]
        
        return filtered
    
    def _apply_attribution_model(
        self,
        revenue_data: List[RevenueData],
        model: AttributionModel,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[RevenueData]:
        """Apply attribution model to revenue data."""
        
        attributed_revenue = []
        
        for revenue in revenue_data:
            if start_date and revenue.date < start_date:
                continue
            if end_date and revenue.date > end_date:
                continue
            
            # Apply attribution weight based on model
            if model == AttributionModel.FIRST_TOUCH:
                weight = 1.0 if revenue.conversion_path and len(revenue.conversion_path) > 0 else 1.0
            elif model == AttributionModel.LAST_TOUCH:
                weight = 1.0  # Last touch gets full credit
            elif model == AttributionModel.LINEAR:
                path_length = len(revenue.conversion_path) if revenue.conversion_path else 1
                weight = 1.0 / path_length
            elif model == AttributionModel.TIME_DECAY:
                weight = self._calculate_time_decay_weight(revenue)
            elif model == AttributionModel.POSITION_BASED:
                weight = self._calculate_position_based_weight(revenue)
            else:
                weight = 1.0
            
            # Create attributed revenue record
            attributed = RevenueData(
                source=revenue.source,
                amount=revenue.amount,
                date=revenue.date,
                customer_id=revenue.customer_id,
                conversion_path=revenue.conversion_path,
                attribution_weight=weight,
                campaign_id=revenue.campaign_id,
                channel=revenue.channel,
                tags=revenue.tags
            )
            
            attributed_revenue.append(attributed)
        
        return attributed_revenue
    
    def _calculate_time_decay_weight(self, revenue: RevenueData) -> float:
        """Calculate time decay attribution weight."""
        
        # Simple time decay - more recent interactions get higher weight
        days_since = (datetime.now() - revenue.date).days
        max_days = self.default_time_decay_days
        
        if days_since >= max_days:
            return 0.1  # Minimum weight
        
        # Exponential decay
        decay_rate = 0.1
        weight = np.exp(-decay_rate * days_since / max_days)
        return max(0.1, weight)
    
    def _calculate_position_based_weight(self, revenue: RevenueData) -> float:
        """Calculate position-based attribution weight (40% first, 20% middle, 40% last)."""
        
        if not revenue.conversion_path or len(revenue.conversion_path) <= 1:
            return 1.0
        
        path_length = len(revenue.conversion_path)
        
        if path_length == 2:
            return 0.5  # Split evenly for 2 touchpoints
        
        # For longer paths: 40% first, 40% last, 20% distributed among middle
        middle_weight = 0.2 / (path_length - 2) if path_length > 2 else 0
        
        # Assuming this is for the last touchpoint (can be adjusted)
        return 0.4
    
    def _calculate_confidence_score(
        self,
        data_points: int,
        roi_percentage: float,
        attribution_adjustment: bool = False,
        data_quality_bonus: float = 0
    ) -> float:
        """Calculate confidence score for ROI calculation."""
        
        # Base confidence from data volume
        if data_points >= 1000:
            volume_score = 1.0
        elif data_points >= 100:
            volume_score = 0.8
        elif data_points >= 50:
            volume_score = 0.6
        else:
            volume_score = 0.4
        
        # ROI stability factor (extreme values less reliable)
        if -50 <= roi_percentage <= 500:
            stability_score = 1.0
        elif -100 <= roi_percentage <= 1000:
            stability_score = 0.8
        else:
            stability_score = 0.5
        
        # Attribution model adjustment
        attribution_penalty = 0.1 if attribution_adjustment else 0
        
        # Calculate final confidence
        confidence = (volume_score * 0.4 + stability_score * 0.6 - attribution_penalty + data_quality_bonus)
        
        return max(0.1, min(1.0, confidence))
    
    def _generate_roi_breakdown(
        self,
        investments: List[InvestmentData],
        revenue: List[RevenueData]
    ) -> Dict[str, Any]:
        """Generate detailed ROI breakdown."""
        
        return {
            'investment_by_category': self._group_by_category(investments),
            'investment_by_channel': self._group_by_channel(investments),
            'revenue_by_source': self._group_by_source(revenue),
            'revenue_by_channel': self._group_by_channel(revenue),
            'monthly_trends': self._calculate_monthly_trends(investments, revenue)
        }
    
    def _group_by_category(self, investments: List[InvestmentData]) -> Dict[str, float]:
        """Group investments by category."""
        
        category_totals = defaultdict(float)
        for inv in investments:
            category_totals[inv.category] += inv.amount
        
        return dict(category_totals)
    
    def _group_by_channel(self, data: List[Union[InvestmentData, RevenueData]]) -> Dict[str, float]:
        """Group data by channel."""
        
        channel_totals = defaultdict(float)
        for item in data:
            if item.channel:
                channel_totals[item.channel] += item.amount
        
        return dict(channel_totals)
    
    def _group_by_source(self, revenue: List[RevenueData]) -> Dict[str, float]:
        """Group revenue by source."""
        
        source_totals = defaultdict(float)
        for rev in revenue:
            source_totals[rev.source] += rev.amount
        
        return dict(source_totals)
    
    def _calculate_monthly_trends(
        self,
        investments: List[InvestmentData],
        revenue: List[RevenueData]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate monthly trends for investments and revenue."""
        
        # Group by month
        monthly_investment = defaultdict(float)
        monthly_revenue = defaultdict(float)
        
        for inv in investments:
            month_key = inv.date.strftime('%Y-%m')
            monthly_investment[month_key] += inv.amount
        
        for rev in revenue:
            month_key = rev.date.strftime('%Y-%m')
            monthly_revenue[month_key] += rev.amount
        
        # Combine into trend data
        all_months = set(monthly_investment.keys()) | set(monthly_revenue.keys())
        trend_data = []
        
        for month in sorted(all_months):
            investment = monthly_investment.get(month, 0)
            revenue = monthly_revenue.get(month, 0)
            roi = ((revenue - investment) / investment * 100) if investment > 0 else 0
            
            trend_data.append({
                'month': month,
                'investment': investment,
                'revenue': revenue,
                'roi_percentage': roi
            })
        
        return {'monthly_data': trend_data}
    
    def _generate_roi_recommendations(
        self,
        roi_percentage: float,
        breakdown: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on ROI analysis."""
        
        recommendations = []
        
        if roi_percentage < 0:
            recommendations.extend([
                "ROI is negative - immediate action required to reduce costs or improve revenue",
                "Analyze underperforming channels and consider reallocation of budget",
                "Review campaign effectiveness and pause low-performing initiatives"
            ])
        elif roi_percentage < 100:
            recommendations.extend([
                f"ROI of {roi_percentage:.1f}% is below break-even - optimization needed",
                "Focus on improving conversion rates and reducing customer acquisition costs",
                "Consider A/B testing different marketing approaches"
            ])
        elif roi_percentage < 300:
            recommendations.extend([
                f"ROI of {roi_percentage:.1f}% shows positive returns with room for improvement",
                "Identify top-performing channels for budget reallocation",
                "Scale successful campaigns while optimizing underperforming ones"
            ])
        else:
            recommendations.extend([
                f"Strong ROI of {roi_percentage:.1f}% indicates effective marketing strategy",
                "Consider increasing budget allocation to maintain growth trajectory",
                "Document successful strategies for replication across other initiatives"
            ])
        
        # Channel-specific recommendations
        if 'investment_by_channel' in breakdown:
            top_channels = sorted(
                breakdown['investment_by_channel'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            if top_channels:
                recommendations.append(
                    f"Top investment channels: {', '.join([ch[0] for ch in top_channels])} - monitor performance closely"
                )
        
        return recommendations
    
    def _generate_roas_recommendations(
        self,
        roas_value: float,
        breakdown: Dict[str, Any]
    ) -> List[str]:
        """Generate ROAS-specific recommendations."""
        
        recommendations = []
        
        if roas_value < 1:
            recommendations.extend([
                f"ROAS of {roas_value:.2f} indicates ad spend exceeds revenue - urgent optimization needed",
                "Pause underperforming ad campaigns immediately",
                "Review targeting, creative, and landing page performance"
            ])
        elif roas_value < 2:
            recommendations.extend([
                f"ROAS of {roas_value:.2f} shows minimal profitability - improve efficiency",
                "Optimize bidding strategies and audience targeting",
                "Test new creative formats and messaging"
            ])
        elif roas_value < 4:
            recommendations.extend([
                f"ROAS of {roas_value:.2f} indicates good performance with optimization opportunities",
                "Scale winning campaigns and ad groups",
                "Expand successful audiences to similar segments"
            ])
        else:
            recommendations.extend([
                f"Excellent ROAS of {roas_value:.2f} - consider increasing ad spend",
                "Scale successful campaigns while monitoring performance",
                "Test expansion into new markets or audience segments"
            ])
        
        return recommendations
    
    def _generate_attribution_recommendations(
        self,
        roi_percentage: float,
        attribution_model: AttributionModel,
        breakdown: Dict[str, Any]
    ) -> List[str]:
        """Generate attribution-specific recommendations."""
        
        recommendations = []
        
        recommendations.append(
            f"Attribution model '{attribution_model.value}' shows {roi_percentage:.1f}% ROI"
        )
        
        if attribution_model == AttributionModel.LINEAR:
            recommendations.append(
                "Linear attribution provides balanced view - consider data-driven model for more accuracy"
            )
        elif attribution_model == AttributionModel.FIRST_TOUCH:
            recommendations.append(
                "First-touch attribution emphasizes awareness - complement with last-touch analysis"
            )
        elif attribution_model == AttributionModel.LAST_TOUCH:
            recommendations.append(
                "Last-touch attribution focuses on conversion - consider multi-touch for full journey"
            )
        
        return recommendations
    
    def _generate_ltv_recommendations(
        self,
        ltv_cac_ratio: float,
        breakdown: Dict[str, Any]
    ) -> List[str]:
        """Generate LTV-specific recommendations."""
        
        recommendations = []
        
        if ltv_cac_ratio < 1:
            recommendations.extend([
                f"LTV:CAC ratio of {ltv_cac_ratio:.2f} indicates customers cost more than they're worth",
                "Focus on reducing customer acquisition costs",
                "Improve customer retention and increase lifetime value"
            ])
        elif ltv_cac_ratio < 3:
            recommendations.extend([
                f"LTV:CAC ratio of {ltv_cac_ratio:.2f} shows marginal profitability",
                "Optimize acquisition channels for higher-value customers",
                "Implement retention programs to increase LTV"
            ])
        else:
            recommendations.extend([
                f"Strong LTV:CAC ratio of {ltv_cac_ratio:.2f} indicates profitable customer acquisition",
                "Consider increasing acquisition investment",
                "Scale successful acquisition channels"
            ])
        
        return recommendations
    
    def _generate_incremental_recommendations(
        self,
        incremental_roi: float,
        uplift_percentage: float,
        breakdown: Dict[str, Any]
    ) -> List[str]:
        """Generate incremental ROI recommendations."""
        
        recommendations = []
        
        if incremental_roi > 0 and uplift_percentage > 10:
            recommendations.extend([
                f"Strong incremental ROI of {incremental_roi:.1f}% with {uplift_percentage:.1f}% uplift",
                "Scale this initiative across broader audience",
                "Document successful tactics for replication"
            ])
        elif incremental_roi > 0:
            recommendations.extend([
                f"Positive incremental ROI of {incremental_roi:.1f}% but modest uplift",
                "Optimize campaign elements to increase impact",
                "Test different messaging or creative approaches"
            ])
        else:
            recommendations.extend([
                f"Negative incremental ROI of {incremental_roi:.1f}% indicates ineffective initiative",
                "Pause or significantly modify current approach",
                "Analyze what drove poor performance"
            ])
        
        return recommendations
    
    def _format_time_period(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> str:
        """Format time period for display."""
        
        if not start_date and not end_date:
            return "All time"
        elif start_date and end_date:
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            return f"Since {start_date.strftime('%Y-%m-%d')}"
        else:
            return f"Until {end_date.strftime('%Y-%m-%d')}"
    
    def _get_channel_benchmark(self, channel: str) -> Dict[str, float]:
        """Get industry benchmark for a specific channel."""
        
        channel_lower = channel.lower()
        
        for benchmark_key, values in self.industry_benchmarks.items():
            if benchmark_key in channel_lower or any(
                keyword in channel_lower for keyword in benchmark_key.split('_')
            ):
                return values
        
        # Default benchmark if no match found
        return {'roi': 250, 'min': 200, 'max': 300}
    
    def _compare_to_benchmark(self, roi_percentage: float, channel: str) -> Dict[str, Any]:
        """Compare ROI to industry benchmark."""
        
        benchmark = self._get_channel_benchmark(channel)
        benchmark_roi = benchmark['roi']
        
        performance_ratio = roi_percentage / benchmark_roi if benchmark_roi > 0 else 0
        
        if performance_ratio >= 1.2:
            performance = "Excellent"
        elif performance_ratio >= 1.0:
            performance = "Above Average"
        elif performance_ratio >= 0.8:
            performance = "Average"
        else:
            performance = "Below Average"
        
        return {
            'benchmark_roi': benchmark_roi,
            'performance_ratio': performance_ratio,
            'performance_rating': performance,
            'vs_benchmark_percentage': (roi_percentage - benchmark_roi) / benchmark_roi * 100
        }
    
    def _add_cross_channel_insights(self, channel_results: Dict[str, ROICalculation]):
        """Add cross-channel insights to results."""
        
        # Calculate channel rankings
        sorted_channels = sorted(
            channel_results.items(),
            key=lambda x: x[1].roi_percentage,
            reverse=True
        )
        
        for i, (channel, roi_calc) in enumerate(sorted_channels):
            roi_calc.breakdown['channel_rank'] = i + 1
            roi_calc.breakdown['total_channels'] = len(sorted_channels)
            
            if i == 0:
                roi_calc.recommendations.insert(0, f"Top performing channel - consider increasing investment")
            elif i == len(sorted_channels) - 1:
                roi_calc.recommendations.insert(0, f"Lowest performing channel - optimize or reallocate budget")
    
    def _generate_time_series_roi(self, timeframe: TimeFrame) -> List[Dict[str, Any]]:
        """Generate time series ROI data for specified timeframe."""
        
        # This would generate historical ROI data points
        # For demo purposes, creating sample data
        
        time_series = []
        
        if timeframe == TimeFrame.MONTHLY:
            for i in range(12):
                month_date = datetime.now() - timedelta(days=30 * i)
                roi_value = 200 + (i * 10) + np.random.normal(0, 20)  # Sample ROI with trend
                
                time_series.append({
                    'date': month_date.strftime('%Y-%m'),
                    'roi_percentage': max(0, roi_value),
                    'investment': 10000 + np.random.normal(0, 1000),
                    'revenue': 20000 + np.random.normal(0, 2000)
                })
        
        return sorted(time_series, key=lambda x: x['date'])
    
    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize and deduplicate recommendations."""
        
        # Remove duplicates while preserving order
        seen = set()
        prioritized = []
        
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                prioritized.append(rec)
        
        # Sort by priority keywords
        priority_keywords = ['negative', 'urgent', 'immediate', 'critical', 'pause']
        
        def priority_score(rec):
            score = 0
            for keyword in priority_keywords:
                if keyword.lower() in rec.lower():
                    score += 1
            return score
        
        return sorted(prioritized, key=priority_score, reverse=True)[:10]  # Top 10 recommendations
    
    def _calculate_channel_roas(
        self,
        investments: List[InvestmentData],
        revenue: List[RevenueData]
    ) -> Dict[str, float]:
        """Calculate ROAS by channel."""
        
        channel_spend = self._group_by_channel(investments)
        channel_revenue = self._group_by_channel(revenue)
        
        channel_roas = {}
        
        for channel in set(channel_spend.keys()) | set(channel_revenue.keys()):
            spend = channel_spend.get(channel, 0)
            revenue = channel_revenue.get(channel, 0)
            
            if spend > 0:
                channel_roas[channel] = revenue / spend
            else:
                channel_roas[channel] = 0
        
        return channel_roas
    
    def _generate_attribution_breakdown(self, attributed_revenue: List[RevenueData]) -> Dict[str, Any]:
        """Generate attribution breakdown analysis."""
        
        total_attributed = sum(rev.amount * rev.attribution_weight for rev in attributed_revenue)
        
        channel_attribution = defaultdict(float)
        for rev in attributed_revenue:
            if rev.channel:
                channel_attribution[rev.channel] += rev.amount * rev.attribution_weight
        
        return {
            'total_attributed_revenue': total_attributed,
            'channel_attribution': dict(channel_attribution),
            'attribution_weights_distribution': {
                'min_weight': min(rev.attribution_weight for rev in attributed_revenue),
                'max_weight': max(rev.attribution_weight for rev in attributed_revenue),
                'avg_weight': np.mean([rev.attribution_weight for rev in attributed_revenue])
            }
        }
    
    def _calculate_channel_attribution(self, attributed_revenue: List[RevenueData]) -> Dict[str, float]:
        """Calculate attribution percentages by channel."""
        
        total_attributed = sum(rev.amount * rev.attribution_weight for rev in attributed_revenue)
        channel_attribution = defaultdict(float)
        
        for rev in attributed_revenue:
            if rev.channel:
                channel_attribution[rev.channel] += rev.amount * rev.attribution_weight
        
        # Convert to percentages
        channel_percentages = {}
        for channel, amount in channel_attribution.items():
            channel_percentages[channel] = (amount / total_attributed * 100) if total_attributed > 0 else 0
        
        return channel_percentages
    
    def _analyze_touchpoints(self, attributed_revenue: List[RevenueData]) -> Dict[str, Any]:
        """Analyze customer touchpoints for attribution insights."""
        
        touchpoint_analysis = {
            'avg_touchpoints_per_conversion': 0,
            'most_common_first_touchpoint': None,
            'most_common_last_touchpoint': None,
            'conversion_path_lengths': defaultdict(int)
        }
        
        valid_paths = [rev.conversion_path for rev in attributed_revenue if rev.conversion_path]
        
        if valid_paths:
            # Average touchpoints
            touchpoint_analysis['avg_touchpoints_per_conversion'] = np.mean([len(path) for path in valid_paths])
            
            # Path length distribution
            for path in valid_paths:
                touchpoint_analysis['conversion_path_lengths'][len(path)] += 1
            
            # Most common touchpoints
            first_touchpoints = [path[0] for path in valid_paths if len(path) > 0]
            last_touchpoints = [path[-1] for path in valid_paths if len(path) > 0]
            
            if first_touchpoints:
                touchpoint_analysis['most_common_first_touchpoint'] = max(set(first_touchpoints), key=first_touchpoints.count)
            
            if last_touchpoints:
                touchpoint_analysis['most_common_last_touchpoint'] = max(set(last_touchpoints), key=last_touchpoints.count)
        
        return touchpoint_analysis
    
    def _analyze_ltv_distribution(self, ltv_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze customer LTV distribution."""
        
        ltv_values = ltv_data['ltv'].values
        
        return {
            'mean_ltv': np.mean(ltv_values),
            'median_ltv': np.median(ltv_values),
            'std_ltv': np.std(ltv_values),
            'percentiles': {
                '25th': np.percentile(ltv_values, 25),
                '75th': np.percentile(ltv_values, 75),
                '90th': np.percentile(ltv_values, 90)
            },
            'high_value_customers_pct': len(ltv_data[ltv_data['ltv'] > ltv_data['ltv'].quantile(0.8)]) / len(ltv_data) * 100
        }
    
    def _perform_ltv_cohort_analysis(self, ltv_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform cohort analysis on LTV data."""
        
        # Simple cohort analysis by acquisition month (if available)
        if 'acquisition_date' in ltv_data.columns:
            ltv_data['cohort_month'] = pd.to_datetime(ltv_data['acquisition_date']).dt.to_period('M')
            cohort_analysis = ltv_data.groupby('cohort_month').agg({
                'ltv': ['mean', 'median', 'count'],
                'acquisition_cost': 'mean'
            }).round(2)
            
            return {
                'cohort_data': cohort_analysis.to_dict(),
                'total_cohorts': len(ltv_data['cohort_month'].unique())
            }
        
        return {'message': 'Acquisition date not available for cohort analysis'}
    
    def _calculate_incremental_confidence(
        self,
        test_data: Dict[str, pd.DataFrame],
        control_data: Dict[str, pd.DataFrame],
        incremental_roi: float
    ) -> float:
        """Calculate confidence score for incremental ROI."""
        
        test_size = len(test_data['revenue'])
        control_size = len(control_data['revenue'])
        
        # Base confidence from sample sizes
        min_sample_size = min(test_size, control_size)
        
        if min_sample_size >= 1000:
            size_confidence = 0.9
        elif min_sample_size >= 100:
            size_confidence = 0.7
        else:
            size_confidence = 0.5
        
        # ROI magnitude adjustment
        roi_confidence = min(1.0, abs(incremental_roi) / 100)  # Higher ROI = higher confidence
        
        return (size_confidence + roi_confidence) / 2
    
    def _calculate_statistical_significance(
        self,
        test_data: pd.DataFrame,
        control_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate statistical significance of test results."""
        
        try:
            from scipy import stats
            
            test_values = test_data['amount'].values
            control_values = control_data['amount'].values
            
            # Perform t-test
            t_stat, p_value = stats.ttest_ind(test_values, control_values)
            
            # Determine significance
            significance_level = 0.05
            is_significant = p_value < significance_level
            
            return {
                't_statistic': t_stat,
                'p_value': p_value,
                'is_significant': is_significant,
                'confidence_level': (1 - p_value) * 100 if p_value < 1 else 50
            }
            
        except ImportError:
            logger.warning("SciPy not available for statistical significance testing")
            return {'message': 'Statistical significance calculation unavailable'}
        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return {'error': str(e)}


# Demo functions and sample data generation

def create_sample_roi_data() -> Tuple[List[InvestmentData], List[RevenueData]]:
    """Create sample investment and revenue data for ROI calculations."""
    
    import random
    from datetime import datetime, timedelta
    
    np.random.seed(42)
    random.seed(42)
    
    # Sample investment data
    investments = []
    channels = ['google_ads', 'facebook_ads', 'email_marketing', 'content_marketing', 'seo']
    categories = ['advertising', 'content', 'email', 'social', 'organic']
    
    for i in range(100):
        date = datetime.now() - timedelta(days=random.randint(1, 365))
        channel = random.choice(channels)
        category = random.choice(categories)
        
        investment = InvestmentData(
            source=f"campaign_{i}",
            amount=random.uniform(500, 5000),
            date=date,
            category=category,
            campaign_id=f"camp_{i}",
            channel=channel,
            tags={'source': 'demo'}
        )
        investments.append(investment)
    
    # Sample revenue data with attribution
    revenue = []
    conversion_paths = [
        ['google_ads', 'email_marketing'],
        ['facebook_ads', 'content_marketing', 'email_marketing'],
        ['seo', 'google_ads'],
        ['content_marketing'],
        ['email_marketing', 'google_ads', 'facebook_ads']
    ]
    
    for i in range(80):
        date = datetime.now() - timedelta(days=random.randint(1, 365))
        channel = random.choice(channels)
        path = random.choice(conversion_paths)
        
        rev = RevenueData(
            source=f"customer_{i}",
            amount=random.uniform(100, 2000),
            date=date,
            customer_id=f"cust_{i}",
            conversion_path=path,
            attribution_weight=1.0,
            campaign_id=f"camp_{random.randint(0, 99)}",
            channel=channel,
            tags={'source': 'demo'}
        )
        revenue.append(rev)
    
    return investments, revenue


def run_roi_calculation_demo():
    """
    Demonstration of ROI calculation framework capabilities.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("📈 MarTech ROI Calculation Framework Demo")
    print("=" * 50)
    
    # Initialize ROI framework
    roi_framework = ROICalculationFramework()
    
    # Create sample data
    print("📊 Generating sample investment and revenue data...")
    investments, revenue = create_sample_roi_data()
    
    # Add data to framework
    roi_framework.add_investment_data(investments)
    roi_framework.add_revenue_data(revenue)
    
    print(f"✅ Added {len(investments)} investment records and {len(revenue)} revenue records")
    
    # Calculate different types of ROI
    print("\n🔢 Calculating various ROI metrics...")
    
    try:
        # Simple ROI
        print("  📌 Simple ROI calculation...")
        simple_roi = roi_framework.calculate_simple_roi(
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        print(f"     ROI: {simple_roi.roi_percentage:.1f}% | Revenue: ${simple_roi.total_revenue:,.2f} | Investment: ${simple_roi.total_investment:,.2f}")
        
        # ROAS
        print("  📌 ROAS calculation...")
        roas = roi_framework.calculate_roas(
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        print(f"     ROAS: {roas.roi_value:.2f}x | Ad Revenue: ${roas.total_revenue:,.2f} | Ad Spend: ${roas.total_investment:,.2f}")
        
        # Attributed ROI
        print("  📌 Attributed ROI calculation (Linear model)...")
        attributed_roi = roi_framework.calculate_attributed_roi(
            attribution_model=AttributionModel.LINEAR,
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        print(f"     Attributed ROI: {attributed_roi.roi_percentage:.1f}% | Confidence: {attributed_roi.confidence_score:.2f}")
        
        # Channel comparison
        print("  📌 Channel ROI comparison...")
        channel_roi = roi_framework.calculate_channel_roi_comparison(
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        
        print("     Channel Performance:")
        for channel, roi_calc in sorted(channel_roi.items(), key=lambda x: x[1].roi_percentage, reverse=True):
            print(f"       {channel}: {roi_calc.roi_percentage:.1f}% ROI (Rank #{roi_calc.breakdown['channel_rank']})")
        
        # Dashboard data
        print("\n📊 Generating ROI dashboard data...")
        dashboard = roi_framework.generate_roi_dashboard_data()
        
        print("📋 Dashboard Summary:")
        summary = dashboard['summary_metrics']
        print(f"  Current ROI: {summary['current_roi']:.1f}%")
        print(f"  Total Revenue: ${summary['total_revenue']:,.2f}")
        print(f"  Total Investment: ${summary['total_investment']:,.2f}")
        print(f"  Profit: ${summary['profit']:,.2f}")
        print(f"  Confidence Score: {summary['confidence_score']:.2f}")
        
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(dashboard['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        
        print("\n📈 Attribution Analysis:")
        attr_analysis = dashboard['attribution_analysis']
        for model, data in attr_analysis.items():
            print(f"  {model.replace('_', ' ').title()}: {data['roi_percentage']:.1f}% ROI")
        
        print("\n💰 Channel Comparison (ROI):")
        channel_comp = dashboard['channel_comparison']
        for channel, data in sorted(channel_comp.items(), key=lambda x: x[1]['roi_percentage'], reverse=True):
            print(f"  {channel}: {data['roi_percentage']:.1f}% (Revenue: ${data['revenue']:,.0f})")
        
        print(f"\n🚀 Framework processed {len(investments) + len(revenue)} data points")
        print("✅ All ROI calculations completed successfully!")
        
        print("\n💼 Portfolio: https://verityai.co")
        print("🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
        
        return {
            'simple_roi': simple_roi,
            'roas': roas,
            'attributed_roi': attributed_roi,
            'channel_roi': channel_roi,
            'dashboard': dashboard
        }
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        return {}


if __name__ == "__main__":
    run_roi_calculation_demo()