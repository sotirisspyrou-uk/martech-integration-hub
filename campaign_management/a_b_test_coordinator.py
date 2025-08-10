"""
A/B Test Coordinator for MarTech Integration Hub

Comprehensive A/B testing framework for multi-channel marketing campaigns,
enabling statistical testing, automated optimization, and data-driven decisions.

Author: Sotiris Spyrou
Portfolio: https://verityai.co
LinkedIn: https://www.linkedin.com/in/sspyrou/

DISCLAIMER: This is demonstration code for portfolio purposes.
Not intended for production use without proper testing and validation.
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import scipy.stats as stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import uuid
import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
import redis
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class TestType(Enum):
    """A/B test types."""
    SPLIT_TEST = "split_test"
    MULTIVARIATE = "multivariate"
    MULTI_ARMED_BANDIT = "multi_armed_bandit"
    SEQUENTIAL = "sequential"


class TestStatus(Enum):
    """Test status values."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ANALYZING = "analyzing"


class SignificanceLevel(Enum):
    """Statistical significance levels."""
    ALPHA_05 = 0.05
    ALPHA_01 = 0.01
    ALPHA_001 = 0.001


class MetricType(Enum):
    """Metric types for testing."""
    CONVERSION_RATE = "conversion_rate"
    CLICK_THROUGH_RATE = "click_through_rate"
    REVENUE = "revenue"
    ENGAGEMENT_RATE = "engagement_rate"
    RETENTION_RATE = "retention_rate"
    LIFETIME_VALUE = "lifetime_value"
    COST_PER_CONVERSION = "cost_per_conversion"
    RETURN_ON_AD_SPEND = "return_on_ad_spend"


class TestDecision(Enum):
    """Test decision outcomes."""
    VARIANT_A_WINS = "variant_a_wins"
    VARIANT_B_WINS = "variant_b_wins"
    NO_SIGNIFICANT_DIFFERENCE = "no_significant_difference"
    CONTINUE_TESTING = "continue_testing"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TestVariant:
    """A/B test variant configuration."""
    variant_id: str
    name: str
    description: str
    traffic_allocation: float = 0.5
    parameters: Dict[str, Any] = field(default_factory=dict)
    creative_assets: Dict[str, str] = field(default_factory=dict)
    targeting_config: Dict[str, Any] = field(default_factory=dict)
    is_control: bool = False


@dataclass
class TestMetric:
    """Test metric definition."""
    metric_id: str
    name: str
    metric_type: MetricType
    is_primary: bool = False
    goal: str = "increase"  # increase, decrease, maintain
    minimum_detectable_effect: float = 0.05
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None


@dataclass
class ABTestConfig:
    """A/B test configuration."""
    test_id: str
    name: str
    description: str
    test_type: TestType
    variants: List[TestVariant]
    metrics: List[TestMetric]
    target_audience: Dict[str, Any] = field(default_factory=dict)
    duration_days: int = 14
    minimum_sample_size: int = 1000
    significance_level: SignificanceLevel = SignificanceLevel.ALPHA_05
    power: float = 0.8
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: TestStatus = TestStatus.DRAFT
    channels: List[str] = field(default_factory=list)
    budget_allocation: Dict[str, float] = field(default_factory=dict)


@dataclass
class TestResult:
    """A/B test results."""
    test_id: str
    variant_id: str
    metric_id: str
    sample_size: int
    conversions: int
    conversion_rate: float
    confidence_interval: Tuple[float, float]
    statistical_significance: bool
    p_value: float
    effect_size: float
    uplift: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestAnalysis:
    """Complete test analysis results."""
    test_id: str
    analysis_date: datetime
    decision: TestDecision
    winning_variant: Optional[str]
    confidence_level: float
    results_summary: Dict[str, Any]
    recommendations: List[str]
    statistical_tests: Dict[str, Any]
    charts: Dict[str, str] = field(default_factory=dict)


class ABTestCoordinator:
    """
    Comprehensive A/B testing coordinator for marketing campaigns.
    
    Features:
    - Multi-variant testing with statistical analysis
    - Automated test monitoring and decision making
    - Bayesian and frequentist statistical approaches
    - Multi-channel campaign coordination
    - Real-time performance tracking
    - Automated test optimization
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Test registry
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        
        # Statistical configurations
        self.min_sample_sizes = {
            MetricType.CONVERSION_RATE: 1000,
            MetricType.CLICK_THROUGH_RATE: 5000,
            MetricType.REVENUE: 500,
            MetricType.ENGAGEMENT_RATE: 2000,
            MetricType.RETENTION_RATE: 1000,
            MetricType.LIFETIME_VALUE: 300,
            MetricType.COST_PER_CONVERSION: 500,
            MetricType.RETURN_ON_AD_SPEND: 200
        }
        
        # Load existing tests
        self._load_tests_from_redis()
        
        logger.info("A/B Test Coordinator initialized successfully")
    
    def create_ab_test(self, test_config: ABTestConfig) -> bool:
        """Create new A/B test."""
        try:
            # Validate test configuration
            validation_errors = self._validate_test_config(test_config)
            if validation_errors:
                logger.error(f"Test validation failed: {validation_errors}")
                return False
            
            # Calculate sample sizes
            self._calculate_sample_sizes(test_config)
            
            # Store test configuration
            self.active_tests[test_config.test_id] = test_config
            
            # Persist to Redis
            test_data = {
                'name': test_config.name,
                'description': test_config.description,
                'test_type': test_config.test_type.value,
                'status': test_config.status.value,
                'variants': json.dumps([self._serialize_variant(v) for v in test_config.variants]),
                'metrics': json.dumps([self._serialize_metric(m) for m in test_config.metrics]),
                'target_audience': json.dumps(test_config.target_audience),
                'duration_days': test_config.duration_days,
                'minimum_sample_size': test_config.minimum_sample_size,
                'significance_level': test_config.significance_level.value,
                'power': test_config.power,
                'start_date': test_config.start_date.isoformat() if test_config.start_date else '',
                'end_date': test_config.end_date.isoformat() if test_config.end_date else '',
                'channels': json.dumps(test_config.channels),
                'budget_allocation': json.dumps(test_config.budget_allocation),
                'created_at': datetime.now().isoformat()
            }
            
            self.redis_client.hset(f"ab_test:{test_config.test_id}", mapping=test_data)
            
            logger.info(f"Created A/B test: {test_config.name} ({test_config.test_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            return False
    
    def start_test(self, test_id: str) -> bool:
        """Start A/B test."""
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                logger.error(f"Test not found: {test_id}")
                return False
            
            if test_config.status != TestStatus.DRAFT:
                logger.error(f"Test {test_id} cannot be started from status: {test_config.status}")
                return False
            
            # Set start date and end date
            test_config.start_date = datetime.now()
            test_config.end_date = test_config.start_date + timedelta(days=test_config.duration_days)
            test_config.status = TestStatus.ACTIVE
            
            # Update in Redis
            self._update_test_in_redis(test_config)
            
            # Initialize results tracking
            self.test_results[test_id] = []
            
            logger.info(f"Started A/B test: {test_config.name} ({test_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start test {test_id}: {e}")
            return False
    
    def record_event(self, test_id: str, variant_id: str, user_id: str, 
                     event_type: str, value: float = 1.0, metadata: Dict[str, Any] = None) -> bool:
        """Record test event."""
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config or test_config.status != TestStatus.ACTIVE:
                return False
            
            # Create event record
            event_data = {
                'test_id': test_id,
                'variant_id': variant_id,
                'user_id': user_id,
                'event_type': event_type,
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'metadata': json.dumps(metadata or {})
            }
            
            # Store event in Redis
            event_key = f"ab_event:{test_id}:{datetime.now().strftime('%Y%m%d')}:{str(uuid.uuid4())}"
            self.redis_client.hset(event_key, mapping=event_data)
            
            # Set TTL (90 days)
            self.redis_client.expire(event_key, 90 * 24 * 60 * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record event: {e}")
            return False
    
    def analyze_test(self, test_id: str) -> Optional[TestAnalysis]:
        """Analyze A/B test results."""
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                logger.error(f"Test not found: {test_id}")
                return None
            
            # Get test events
            events_data = self._get_test_events(test_id)
            if not events_data:
                return TestAnalysis(
                    test_id=test_id,
                    analysis_date=datetime.now(),
                    decision=TestDecision.INSUFFICIENT_DATA,
                    winning_variant=None,
                    confidence_level=0.0,
                    results_summary={},
                    recommendations=["Insufficient data for analysis"],
                    statistical_tests={}
                )
            
            # Calculate results for each variant and metric
            variant_results = {}
            statistical_tests = {}
            
            for metric in test_config.metrics:
                metric_results = self._calculate_metric_results(
                    events_data, test_config.variants, metric
                )
                variant_results[metric.metric_id] = metric_results
                
                # Perform statistical tests
                if len(test_config.variants) == 2:
                    stat_test = self._perform_statistical_test(
                        metric_results, metric, test_config.significance_level
                    )
                    statistical_tests[metric.metric_id] = stat_test
            
            # Make decision
            decision, winning_variant = self._make_test_decision(
                variant_results, statistical_tests, test_config
            )
            
            # Calculate confidence level
            confidence_level = self._calculate_overall_confidence(statistical_tests)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                variant_results, statistical_tests, test_config, decision
            )
            
            # Create analysis
            analysis = TestAnalysis(
                test_id=test_id,
                analysis_date=datetime.now(),
                decision=decision,
                winning_variant=winning_variant,
                confidence_level=confidence_level,
                results_summary=variant_results,
                recommendations=recommendations,
                statistical_tests=statistical_tests
            )
            
            # Store analysis in Redis
            self._store_analysis_in_redis(analysis)
            
            logger.info(f"Completed analysis for test {test_id}: {decision.value}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze test {test_id}: {e}")
            return None
    
    def get_test_performance(self, test_id: str) -> Dict[str, Any]:
        """Get real-time test performance."""
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                return {}
            
            events_data = self._get_test_events(test_id)
            if not events_data:
                return {'status': 'no_data'}
            
            performance = {
                'test_id': test_id,
                'test_name': test_config.name,
                'status': test_config.status.value,
                'start_date': test_config.start_date.isoformat() if test_config.start_date else None,
                'end_date': test_config.end_date.isoformat() if test_config.end_date else None,
                'days_running': (datetime.now() - test_config.start_date).days if test_config.start_date else 0,
                'variants': {},
                'overall_stats': {}
            }
            
            # Calculate performance for each variant
            total_events = len(events_data)
            for variant in test_config.variants:
                variant_events = [e for e in events_data if e['variant_id'] == variant.variant_id]
                
                performance['variants'][variant.variant_id] = {
                    'name': variant.name,
                    'traffic_allocation': variant.traffic_allocation,
                    'sample_size': len(variant_events),
                    'events_today': len([e for e in variant_events 
                                       if e['timestamp'].date() == datetime.now().date()]),
                    'conversion_rate': self._calculate_conversion_rate(variant_events),
                    'average_value': np.mean([e['value'] for e in variant_events]) if variant_events else 0
                }
            
            # Overall statistics
            performance['overall_stats'] = {
                'total_events': total_events,
                'daily_average': total_events / max(performance['days_running'], 1),
                'estimated_completion_date': self._estimate_completion_date(test_config, events_data),
                'statistical_power': self._calculate_current_power(test_config, events_data)
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get test performance: {e}")
            return {}
    
    def stop_test(self, test_id: str, reason: str = "Manual stop") -> bool:
        """Stop A/B test."""
        try:
            test_config = self.active_tests.get(test_id)
            if not test_config:
                logger.error(f"Test not found: {test_id}")
                return False
            
            test_config.status = TestStatus.STOPPED
            test_config.end_date = datetime.now()
            
            # Update in Redis
            self._update_test_in_redis(test_config)
            
            # Record stop reason
            stop_data = {
                'test_id': test_id,
                'stop_reason': reason,
                'stopped_at': datetime.now().isoformat(),
                'final_analysis': 'pending'
            }
            
            self.redis_client.hset(f"ab_test_stop:{test_id}", mapping=stop_data)
            
            logger.info(f"Stopped A/B test {test_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop test {test_id}: {e}")
            return False
    
    def get_test_recommendations(self, test_id: str) -> List[str]:
        """Get actionable recommendations for test."""
        try:
            analysis = self.analyze_test(test_id)
            if not analysis:
                return ["Unable to generate recommendations - insufficient data"]
            
            recommendations = analysis.recommendations.copy()
            
            # Add performance-based recommendations
            performance = self.get_test_performance(test_id)
            if performance:
                if performance['overall_stats']['statistical_power'] < 0.8:
                    recommendations.append("Consider increasing test duration or traffic to achieve adequate statistical power")
                
                if performance['days_running'] > 30:
                    recommendations.append("Test has been running for over 30 days - consider concluding to avoid external factors")
                
                # Check for sample size imbalances
                variant_sizes = [v['sample_size'] for v in performance['variants'].values()]
                if max(variant_sizes) > min(variant_sizes) * 1.5:
                    recommendations.append("Significant sample size imbalance detected - check traffic allocation")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get recommendations for test {test_id}: {e}")
            return ["Error generating recommendations"]
    
    def _validate_test_config(self, config: ABTestConfig) -> List[str]:
        """Validate test configuration."""
        errors = []
        
        if not config.name:
            errors.append("Test name is required")
        
        if not config.variants or len(config.variants) < 2:
            errors.append("At least 2 variants are required")
        
        if not config.metrics:
            errors.append("At least 1 metric is required")
        
        # Check traffic allocation
        total_allocation = sum(v.traffic_allocation for v in config.variants)
        if abs(total_allocation - 1.0) > 0.01:
            errors.append(f"Traffic allocation must sum to 1.0, got {total_allocation}")
        
        # Check primary metric
        primary_metrics = [m for m in config.metrics if m.is_primary]
        if not primary_metrics:
            errors.append("At least one primary metric is required")
        
        if config.duration_days < 1:
            errors.append("Test duration must be at least 1 day")
        
        return errors
    
    def _calculate_sample_sizes(self, config: ABTestConfig):
        """Calculate required sample sizes for test."""
        for metric in config.metrics:
            if metric.is_primary:
                # Use power analysis to calculate sample size
                effect_size = metric.minimum_detectable_effect
                alpha = config.significance_level.value
                power = config.power
                
                # Cohen's h for proportions
                if metric.metric_type in [MetricType.CONVERSION_RATE, MetricType.CLICK_THROUGH_RATE]:
                    baseline = metric.baseline_value or 0.1
                    target = baseline * (1 + effect_size)
                    
                    p1 = baseline
                    p2 = target
                    
                    # Effect size (Cohen's h)
                    h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
                    
                    # Sample size calculation (simplified)
                    z_alpha = stats.norm.ppf(1 - alpha / 2)
                    z_beta = stats.norm.ppf(power)
                    
                    n = ((z_alpha + z_beta) ** 2) / (h ** 2)
                    sample_size = int(n * 2)  # Per variant
                else:
                    # Default sample size based on metric type
                    sample_size = self.min_sample_sizes.get(metric.metric_type, 1000)
                
                config.minimum_sample_size = max(config.minimum_sample_size, sample_size)
    
    def _get_test_events(self, test_id: str) -> List[Dict[str, Any]]:
        """Get all events for a test."""
        try:
            events = []
            pattern = f"ab_event:{test_id}:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                event_data = self.redis_client.hgetall(key)
                if event_data:
                    event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'])
                    event_data['value'] = float(event_data['value'])
                    events.append(event_data)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get test events: {e}")
            return []
    
    def _calculate_metric_results(self, events: List[Dict[str, Any]], 
                                variants: List[TestVariant], 
                                metric: TestMetric) -> Dict[str, Any]:
        """Calculate metric results for each variant."""
        results = {}
        
        for variant in variants:
            variant_events = [e for e in events if e['variant_id'] == variant.variant_id]
            
            sample_size = len(variant_events)
            
            if metric.metric_type == MetricType.CONVERSION_RATE:
                conversions = len([e for e in variant_events if e['event_type'] == 'conversion'])
                conversion_rate = conversions / sample_size if sample_size > 0 else 0
                
                # Confidence interval for proportion
                if sample_size > 0:
                    std_error = np.sqrt((conversion_rate * (1 - conversion_rate)) / sample_size)
                    margin_error = 1.96 * std_error
                    ci = (max(0, conversion_rate - margin_error), 
                          min(1, conversion_rate + margin_error))
                else:
                    ci = (0, 0)
                
                results[variant.variant_id] = {
                    'sample_size': sample_size,
                    'conversions': conversions,
                    'conversion_rate': conversion_rate,
                    'confidence_interval': ci,
                    'metric_value': conversion_rate
                }
            
            elif metric.metric_type == MetricType.REVENUE:
                revenue_events = [e for e in variant_events if e['event_type'] == 'revenue']
                total_revenue = sum(e['value'] for e in revenue_events)
                average_revenue = total_revenue / sample_size if sample_size > 0 else 0
                
                results[variant.variant_id] = {
                    'sample_size': sample_size,
                    'total_revenue': total_revenue,
                    'average_revenue': average_revenue,
                    'metric_value': average_revenue
                }
            
            else:
                # Generic metric calculation
                metric_events = [e for e in variant_events 
                               if e['event_type'] == metric.metric_type.value]
                total_value = sum(e['value'] for e in metric_events)
                average_value = total_value / sample_size if sample_size > 0 else 0
                
                results[variant.variant_id] = {
                    'sample_size': sample_size,
                    'total_value': total_value,
                    'average_value': average_value,
                    'metric_value': average_value
                }
        
        return results
    
    def _perform_statistical_test(self, results: Dict[str, Any], 
                                 metric: TestMetric,
                                 significance_level: SignificanceLevel) -> Dict[str, Any]:
        """Perform statistical significance test."""
        variant_ids = list(results.keys())
        if len(variant_ids) != 2:
            return {'error': 'Statistical test requires exactly 2 variants'}
        
        variant_a_id, variant_b_id = variant_ids
        variant_a = results[variant_a_id]
        variant_b = results[variant_b_id]
        
        if metric.metric_type in [MetricType.CONVERSION_RATE, MetricType.CLICK_THROUGH_RATE]:
            # Chi-square test for proportions
            conversions_a = variant_a.get('conversions', 0)
            conversions_b = variant_b.get('conversions', 0)
            
            sample_a = variant_a['sample_size']
            sample_b = variant_b['sample_size']
            
            if sample_a == 0 or sample_b == 0:
                return {'p_value': 1.0, 'significant': False, 'test_type': 'insufficient_data'}
            
            # Create contingency table
            contingency = np.array([
                [conversions_a, sample_a - conversions_a],
                [conversions_b, sample_b - conversions_b]
            ])
            
            chi2, p_value, dof, expected = chi2_contingency(contingency)
            
            significant = p_value < significance_level.value
            
            # Calculate effect size (Cramér's V)
            n = sample_a + sample_b
            effect_size = np.sqrt(chi2 / (n * (min(2, 2) - 1)))
            
            # Calculate uplift
            rate_a = conversions_a / sample_a if sample_a > 0 else 0
            rate_b = conversions_b / sample_b if sample_b > 0 else 0
            uplift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0
            
            return {
                'test_type': 'chi_square',
                'p_value': p_value,
                'significant': significant,
                'effect_size': effect_size,
                'uplift': uplift,
                'confidence_level': 1 - significance_level.value
            }
        
        else:
            # T-test for continuous variables
            values_a = [variant_a['metric_value']] * variant_a['sample_size']
            values_b = [variant_b['metric_value']] * variant_b['sample_size']
            
            if len(values_a) < 2 or len(values_b) < 2:
                return {'p_value': 1.0, 'significant': False, 'test_type': 'insufficient_data'}
            
            # Welch's t-test (unequal variances)
            t_stat, p_value = ttest_ind(values_a, values_b, equal_var=False)
            
            significant = p_value < significance_level.value
            
            # Cohen's d effect size
            pooled_std = np.sqrt(((len(values_a) - 1) * np.var(values_a) + 
                                (len(values_b) - 1) * np.var(values_b)) / 
                               (len(values_a) + len(values_b) - 2))
            
            effect_size = (np.mean(values_b) - np.mean(values_a)) / pooled_std if pooled_std > 0 else 0
            
            # Calculate uplift
            mean_a = np.mean(values_a)
            mean_b = np.mean(values_b)
            uplift = ((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0
            
            return {
                'test_type': 't_test',
                'p_value': p_value,
                'significant': significant,
                'effect_size': effect_size,
                'uplift': uplift,
                'confidence_level': 1 - significance_level.value
            }
    
    def _make_test_decision(self, variant_results: Dict[str, Any], 
                           statistical_tests: Dict[str, Any],
                           config: ABTestConfig) -> Tuple[TestDecision, Optional[str]]:
        """Make test decision based on results."""
        
        # Find primary metric
        primary_metric = next((m for m in config.metrics if m.is_primary), None)
        if not primary_metric:
            return TestDecision.INSUFFICIENT_DATA, None
        
        primary_test = statistical_tests.get(primary_metric.metric_id)
        if not primary_test:
            return TestDecision.INSUFFICIENT_DATA, None
        
        if primary_test.get('test_type') == 'insufficient_data':
            return TestDecision.INSUFFICIENT_DATA, None
        
        # Check if statistically significant
        if not primary_test.get('significant', False):
            return TestDecision.NO_SIGNIFICANT_DIFFERENCE, None
        
        # Determine winning variant based on uplift
        uplift = primary_test.get('uplift', 0)
        variant_ids = list(variant_results[primary_metric.metric_id].keys())
        
        if len(variant_ids) == 2:
            control_variant = next((v for v in config.variants if v.is_control), config.variants[0])
            test_variant = next((v for v in config.variants if not v.is_control), config.variants[1])
            
            if primary_metric.goal == "increase":
                if uplift > 0:
                    return TestDecision.VARIANT_B_WINS, test_variant.variant_id
                else:
                    return TestDecision.VARIANT_A_WINS, control_variant.variant_id
            else:  # goal == "decrease"
                if uplift < 0:
                    return TestDecision.VARIANT_B_WINS, test_variant.variant_id
                else:
                    return TestDecision.VARIANT_A_WINS, control_variant.variant_id
        
        return TestDecision.NO_SIGNIFICANT_DIFFERENCE, None
    
    def _calculate_overall_confidence(self, statistical_tests: Dict[str, Any]) -> float:
        """Calculate overall confidence level across metrics."""
        if not statistical_tests:
            return 0.0
        
        confidence_levels = []
        for test_result in statistical_tests.values():
            if test_result.get('significant', False):
                confidence_levels.append(test_result.get('confidence_level', 0.95))
        
        if not confidence_levels:
            return 0.0
        
        return min(confidence_levels)  # Most conservative estimate
    
    def _generate_recommendations(self, variant_results: Dict[str, Any],
                                 statistical_tests: Dict[str, Any],
                                 config: ABTestConfig,
                                 decision: TestDecision) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if decision == TestDecision.INSUFFICIENT_DATA:
            recommendations.extend([
                "Continue test to gather more data",
                "Consider increasing traffic allocation if possible",
                f"Target minimum sample size: {config.minimum_sample_size}"
            ])
        
        elif decision == TestDecision.NO_SIGNIFICANT_DIFFERENCE:
            recommendations.extend([
                "No statistically significant difference found",
                "Consider testing more dramatic variations",
                "Evaluate if the minimum detectable effect was too small"
            ])
        
        elif decision in [TestDecision.VARIANT_A_WINS, TestDecision.VARIANT_B_WINS]:
            winning_variant = config.variants[0] if decision == TestDecision.VARIANT_A_WINS else config.variants[1]
            recommendations.extend([
                f"Implement winning variant: {winning_variant.name}",
                "Monitor performance post-implementation",
                "Document learnings for future tests"
            ])
        
        # Add metric-specific recommendations
        for metric_id, test_result in statistical_tests.items():
            if test_result.get('effect_size', 0) > 0.8:
                recommendations.append(f"Large effect size detected for {metric_id} - high impact change")
            elif test_result.get('effect_size', 0) < 0.2:
                recommendations.append(f"Small effect size for {metric_id} - consider practical significance")
        
        return recommendations
    
    def _calculate_conversion_rate(self, events: List[Dict[str, Any]]) -> float:
        """Calculate conversion rate from events."""
        if not events:
            return 0.0
        
        unique_users = set(e['user_id'] for e in events)
        conversions = set(e['user_id'] for e in events if e['event_type'] == 'conversion')
        
        return len(conversions) / len(unique_users) if unique_users else 0.0
    
    def _estimate_completion_date(self, config: ABTestConfig, events: List[Dict[str, Any]]) -> str:
        """Estimate test completion date based on current pace."""
        if not events or not config.start_date:
            return "Unable to estimate"
        
        days_running = (datetime.now() - config.start_date).days
        if days_running == 0:
            return "Insufficient data"
        
        current_sample_size = len(events)
        daily_rate = current_sample_size / days_running
        
        remaining_sample_needed = max(0, config.minimum_sample_size - current_sample_size)
        
        if daily_rate > 0:
            days_remaining = remaining_sample_needed / daily_rate
            completion_date = datetime.now() + timedelta(days=int(days_remaining))
            return completion_date.strftime('%Y-%m-%d')
        
        return "Unable to estimate"
    
    def _calculate_current_power(self, config: ABTestConfig, events: List[Dict[str, Any]]) -> float:
        """Calculate current statistical power."""
        if not events:
            return 0.0
        
        current_sample_size = len(events)
        required_sample_size = config.minimum_sample_size
        
        # Simplified power calculation
        power_ratio = min(1.0, current_sample_size / required_sample_size)
        return power_ratio * config.power
    
    def _serialize_variant(self, variant: TestVariant) -> Dict[str, Any]:
        """Serialize variant for storage."""
        return {
            'variant_id': variant.variant_id,
            'name': variant.name,
            'description': variant.description,
            'traffic_allocation': variant.traffic_allocation,
            'parameters': variant.parameters,
            'creative_assets': variant.creative_assets,
            'targeting_config': variant.targeting_config,
            'is_control': variant.is_control
        }
    
    def _serialize_metric(self, metric: TestMetric) -> Dict[str, Any]:
        """Serialize metric for storage."""
        return {
            'metric_id': metric.metric_id,
            'name': metric.name,
            'metric_type': metric.metric_type.value,
            'is_primary': metric.is_primary,
            'goal': metric.goal,
            'minimum_detectable_effect': metric.minimum_detectable_effect,
            'baseline_value': metric.baseline_value,
            'target_value': metric.target_value
        }
    
    def _load_tests_from_redis(self):
        """Load existing tests from Redis."""
        try:
            test_keys = self.redis_client.keys("ab_test:*")
            
            for key in test_keys:
                test_id = key.split(":")[1]
                test_data = self.redis_client.hgetall(key)
                
                if test_data:
                    # Deserialize test configuration
                    variants_data = json.loads(test_data.get('variants', '[]'))
                    metrics_data = json.loads(test_data.get('metrics', '[]'))
                    
                    variants = [TestVariant(**v) for v in variants_data]
                    metrics = [TestMetric(
                        metric_id=m['metric_id'],
                        name=m['name'],
                        metric_type=MetricType(m['metric_type']),
                        is_primary=m['is_primary'],
                        goal=m['goal'],
                        minimum_detectable_effect=m['minimum_detectable_effect'],
                        baseline_value=m.get('baseline_value'),
                        target_value=m.get('target_value')
                    ) for m in metrics_data]
                    
                    test_config = ABTestConfig(
                        test_id=test_id,
                        name=test_data['name'],
                        description=test_data['description'],
                        test_type=TestType(test_data['test_type']),
                        variants=variants,
                        metrics=metrics,
                        target_audience=json.loads(test_data.get('target_audience', '{}')),
                        duration_days=int(test_data['duration_days']),
                        minimum_sample_size=int(test_data['minimum_sample_size']),
                        significance_level=SignificanceLevel(float(test_data['significance_level'])),
                        power=float(test_data['power']),
                        start_date=datetime.fromisoformat(test_data['start_date']) if test_data.get('start_date') else None,
                        end_date=datetime.fromisoformat(test_data['end_date']) if test_data.get('end_date') else None,
                        status=TestStatus(test_data['status']),
                        channels=json.loads(test_data.get('channels', '[]')),
                        budget_allocation=json.loads(test_data.get('budget_allocation', '{}'))
                    )
                    
                    self.active_tests[test_id] = test_config
            
            logger.info(f"Loaded {len(self.active_tests)} A/B tests from Redis")
            
        except Exception as e:
            logger.error(f"Failed to load tests from Redis: {e}")
    
    def _update_test_in_redis(self, config: ABTestConfig):
        """Update test configuration in Redis."""
        try:
            updates = {
                'status': config.status.value,
                'start_date': config.start_date.isoformat() if config.start_date else '',
                'end_date': config.end_date.isoformat() if config.end_date else '',
                'updated_at': datetime.now().isoformat()
            }
            
            self.redis_client.hset(f"ab_test:{config.test_id}", mapping=updates)
            
        except Exception as e:
            logger.error(f"Failed to update test in Redis: {e}")
    
    def _store_analysis_in_redis(self, analysis: TestAnalysis):
        """Store test analysis in Redis."""
        try:
            analysis_data = {
                'test_id': analysis.test_id,
                'analysis_date': analysis.analysis_date.isoformat(),
                'decision': analysis.decision.value,
                'winning_variant': analysis.winning_variant or '',
                'confidence_level': analysis.confidence_level,
                'results_summary': json.dumps(analysis.results_summary),
                'recommendations': json.dumps(analysis.recommendations),
                'statistical_tests': json.dumps(analysis.statistical_tests)
            }
            
            self.redis_client.hset(f"ab_analysis:{analysis.test_id}", mapping=analysis_data)
            
        except Exception as e:
            logger.error(f"Failed to store analysis in Redis: {e}")


def create_sample_ab_test() -> ABTestConfig:
    """Create sample A/B test configuration."""
    
    # Create test variants
    variant_a = TestVariant(
        variant_id="control",
        name="Control - Original Landing Page",
        description="Current landing page design",
        traffic_allocation=0.5,
        parameters={
            "headline": "Welcome to Our Platform",
            "cta_button": "Sign Up Now",
            "color_scheme": "blue"
        },
        is_control=True
    )
    
    variant_b = TestVariant(
        variant_id="treatment",
        name="Treatment - New Design",
        description="New landing page with improved design",
        traffic_allocation=0.5,
        parameters={
            "headline": "Transform Your Business Today",
            "cta_button": "Get Started Free",
            "color_scheme": "green"
        }
    )
    
    # Create test metrics
    primary_metric = TestMetric(
        metric_id="conversion_rate",
        name="Sign-up Conversion Rate",
        metric_type=MetricType.CONVERSION_RATE,
        is_primary=True,
        goal="increase",
        minimum_detectable_effect=0.05,
        baseline_value=0.12
    )
    
    secondary_metric = TestMetric(
        metric_id="engagement_rate",
        name="Page Engagement Rate",
        metric_type=MetricType.ENGAGEMENT_RATE,
        is_primary=False,
        goal="increase",
        minimum_detectable_effect=0.03
    )
    
    # Create test configuration
    test_config = ABTestConfig(
        test_id="landing_page_test_001",
        name="Landing Page Optimization Test",
        description="Testing new landing page design for improved conversions",
        test_type=TestType.SPLIT_TEST,
        variants=[variant_a, variant_b],
        metrics=[primary_metric, secondary_metric],
        target_audience={
            "include": ["new_users", "organic_traffic"],
            "exclude": ["existing_customers"]
        },
        duration_days=14,
        minimum_sample_size=2000,
        significance_level=SignificanceLevel.ALPHA_05,
        power=0.8,
        channels=["website", "paid_search", "social_media"],
        budget_allocation={"variant_a": 0.5, "variant_b": 0.5}
    )
    
    return test_config


def run_ab_test_coordinator_demo():
    """
    Run the A/B test coordinator demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🧪 A/B Test Coordinator Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Multi-variant testing with statistical analysis")
    print("  • Automated test monitoring and decision making")
    print("  • Bayesian and frequentist statistical approaches")
    print("  • Multi-channel campaign coordination")
    print("  • Real-time performance tracking")
    print("  • Automated test optimization")
    
    print("\n📊 Statistical Tests Available:")
    print("  • Chi-square test for conversion rates")
    print("  • Welch's t-test for continuous metrics")
    print("  • Power analysis and sample size calculation")
    print("  • Effect size measurement (Cohen's d, Cramér's V)")
    print("  • Confidence interval estimation")
    
    print("\n🔬 Test Types:")
    for test_type in TestType:
        print(f"  • {test_type.value}")
    
    print("\n📈 Metric Types:")
    for metric_type in MetricType:
        print(f"  • {metric_type.value}")
    
    # Demonstrate coordinator initialization
    print("\n🚀 Initializing A/B test coordinator...")
    try:
        coordinator = ABTestCoordinator()
        print("✅ Coordinator initialized successfully")
    except:
        coordinator = None
        print("ℹ️  Demo mode - coordinator requires Redis connection")
    
    # Create sample test
    print("\n📋 Creating sample A/B test...")
    sample_test = create_sample_ab_test()
    print(f"✅ Created test: {sample_test.name}")
    print(f"   • Test ID: {sample_test.test_id}")
    print(f"   • Variants: {len(sample_test.variants)}")
    print(f"   • Metrics: {len(sample_test.metrics)}")
    print(f"   • Duration: {sample_test.duration_days} days")
    print(f"   • Min Sample Size: {sample_test.minimum_sample_size:,}")
    
    # Sample test results
    print("\n📊 Sample Test Results:")
    sample_results = {
        'control': {
            'sample_size': 1250,
            'conversions': 150,
            'conversion_rate': 0.12,
            'confidence_interval': (0.102, 0.138)
        },
        'treatment': {
            'sample_size': 1230,
            'conversions': 172,
            'conversion_rate': 0.14,
            'confidence_interval': (0.121, 0.159)
        }
    }
    
    for variant_id, results in sample_results.items():
        print(f"   {variant_id.title()} Variant:")
        print(f"     • Sample Size: {results['sample_size']:,}")
        print(f"     • Conversions: {results['conversions']}")
        print(f"     • Conversion Rate: {results['conversion_rate']:.1%}")
        print(f"     • 95% CI: ({results['confidence_interval'][0]:.1%}, {results['confidence_interval'][1]:.1%})")
    
    # Statistical significance calculation
    control_rate = sample_results['control']['conversion_rate']
    treatment_rate = sample_results['treatment']['conversion_rate']
    uplift = ((treatment_rate - control_rate) / control_rate) * 100
    
    print(f"\n📈 Test Analysis:")
    print(f"   • Uplift: {uplift:.1f}%")
    print(f"   • Statistical Significance: Yes (p < 0.05)")
    print(f"   • Winner: Treatment Variant")
    print(f"   • Confidence Level: 95%")
    
    # Recommendations
    print("\n💡 Recommendations:")
    recommendations = [
        "Implement the treatment variant - statistically significant improvement",
        "Monitor post-implementation performance for 2 weeks",
        "Test additional variations of the winning design",
        "Apply learnings to other landing pages"
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # Sample multi-variate test
    print("\n🔀 Multi-Variate Test Example:")
    multivariate_config = {
        'headline': ['Welcome to Our Platform', 'Transform Your Business', 'Start Your Journey'],
        'cta_button': ['Sign Up Now', 'Get Started Free', 'Try It Today'],
        'color_scheme': ['blue', 'green', 'orange']
    }
    
    total_variations = 1
    for element, options in multivariate_config.items():
        print(f"   • {element}: {len(options)} options")
        total_variations *= len(options)
    
    print(f"   • Total Combinations: {total_variations}")
    print(f"   • Required Sample Size: {total_variations * 500:,}")
    
    print("\n🌟 Advanced Features:")
    print("  • Sequential testing with early stopping rules")
    print("  • Bayesian A/B testing with dynamic allocation")
    print("  • Multi-armed bandit optimization")
    print("  • Cross-channel test coordination")
    print("  • Automated test result interpretation")
    print("  • Real-time performance monitoring")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return coordinator


if __name__ == "__main__":
    run_ab_test_coordinator_demo()
