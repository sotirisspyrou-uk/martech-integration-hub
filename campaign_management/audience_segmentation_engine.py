"""
Audience Segmentation Engine for MarTech Integration Hub

Advanced audience segmentation system using machine learning, behavioral analysis,
and predictive modeling for precision marketing targeting and personalization.

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
import uuid
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.metrics import silhouette_score, accuracy_score, classification_report
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import redis
import asyncio
import aiohttp
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class SegmentationType(Enum):
    """Types of audience segmentation."""
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"
    PSYCHOGRAPHIC = "psychographic"
    GEOGRAPHIC = "geographic"
    VALUE_BASED = "value_based"
    LIFECYCLE = "lifecycle"
    ENGAGEMENT = "engagement"
    PREDICTIVE = "predictive"


class SegmentationMethod(Enum):
    """Segmentation algorithms."""
    KMEANS = "kmeans"
    HIERARCHICAL = "hierarchical"
    DBSCAN = "dbscan"
    RFM_ANALYSIS = "rfm_analysis"
    BEHAVIORAL_FLOW = "behavioral_flow"
    COHORT_ANALYSIS = "cohort_analysis"
    PREDICTIVE_CLUSTERING = "predictive_clustering"
    CUSTOM_RULES = "custom_rules"


class SegmentStatus(Enum):
    """Segment status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    UPDATING = "updating"


class EngagementLevel(Enum):
    """Customer engagement levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INACTIVE = "inactive"


class LifecycleStage(Enum):
    """Customer lifecycle stages."""
    PROSPECT = "prospect"
    NEW_CUSTOMER = "new_customer"
    ACTIVE_CUSTOMER = "active_customer"
    VIP_CUSTOMER = "vip_customer"
    AT_RISK = "at_risk"
    CHURNED = "churned"


@dataclass
class SegmentCriteria:
    """Audience segment criteria definition."""
    criteria_id: str
    name: str
    field: str
    operator: str  # equals, not_equals, greater_than, less_than, contains, in, not_in
    value: Union[str, int, float, List[Any]]
    weight: float = 1.0
    is_required: bool = False


@dataclass
class AudienceSegment:
    """Audience segment definition."""
    segment_id: str
    name: str
    description: str
    segmentation_type: SegmentationType
    segmentation_method: SegmentationMethod
    criteria: List[SegmentCriteria] = field(default_factory=list)
    size: int = 0
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)
    status: SegmentStatus = SegmentStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    targeting_channels: List[str] = field(default_factory=list)


@dataclass
class CustomerProfile:
    """Customer profile for segmentation."""
    customer_id: str
    demographics: Dict[str, Any] = field(default_factory=dict)
    behavioral_data: Dict[str, Any] = field(default_factory=dict)
    transaction_history: List[Dict[str, Any]] = field(default_factory=list)
    engagement_data: Dict[str, Any] = field(default_factory=dict)
    predicted_attributes: Dict[str, Any] = field(default_factory=dict)
    segment_assignments: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class SegmentationResult:
    """Results of audience segmentation analysis."""
    segmentation_id: str
    segments: List[AudienceSegment]
    total_audience_size: int
    segmentation_quality: Dict[str, float]
    insights: List[str]
    recommendations: List[str]
    created_date: datetime = field(default_factory=datetime.now)


@dataclass
class RFMScore:
    """RFM (Recency, Frequency, Monetary) analysis scores."""
    customer_id: str
    recency_score: int  # 1-5 scale
    frequency_score: int  # 1-5 scale
    monetary_score: int  # 1-5 scale
    rfm_segment: str
    total_score: int
    percentile_rank: float


class AudienceSegmentationEngine:
    """
    Advanced audience segmentation engine for precision marketing targeting.
    
    Features:
    - Multi-dimensional customer segmentation
    - Machine learning-based clustering
    - RFM analysis and cohort analysis
    - Predictive segment modeling
    - Real-time segment updates
    - Cross-channel segment synchronization
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Segment registry
        self.segments: Dict[str, AudienceSegment] = {}
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        
        # ML models
        self.clustering_models = {}
        self.classification_models = {}
        self.scaler = StandardScaler()
        
        # Load existing segments
        self._load_segments_from_redis()
        
        logger.info("Audience Segmentation Engine initialized successfully")
    
    def create_segment(self, segment: AudienceSegment) -> bool:
        """Create new audience segment."""
        try:
            # Store segment
            self.segments[segment.segment_id] = segment
            
            # Persist to Redis
            segment_data = {
                'name': segment.name,
                'description': segment.description,
                'segmentation_type': segment.segmentation_type.value,
                'segmentation_method': segment.segmentation_method.value,
                'criteria': json.dumps([self._serialize_criteria(c) for c in segment.criteria]),
                'size': segment.size,
                'created_date': segment.created_date.isoformat(),
                'updated_date': segment.updated_date.isoformat(),
                'status': segment.status.value,
                'metadata': json.dumps(segment.metadata),
                'performance_metrics': json.dumps(segment.performance_metrics),
                'targeting_channels': json.dumps(segment.targeting_channels)
            }
            
            self.redis_client.hset(f"segment:{segment.segment_id}", mapping=segment_data)
            
            logger.info(f"Created audience segment: {segment.name} ({segment.segment_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create segment: {e}")
            return False
    
    def segment_customers_with_ml(self, customer_data: pd.DataFrame, 
                                 method: SegmentationMethod = SegmentationMethod.KMEANS,
                                 n_clusters: int = 5,
                                 features: List[str] = None) -> SegmentationResult:
        """Segment customers using machine learning algorithms."""
        try:
            segmentation_id = str(uuid.uuid4())
            
            # Prepare features
            if features is None:
                numeric_columns = customer_data.select_dtypes(include=[np.number]).columns.tolist()
                features = [col for col in numeric_columns if col != 'customer_id']
            
            # Extract feature matrix
            X = customer_data[features].fillna(0)
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Apply clustering algorithm
            if method == SegmentationMethod.KMEANS:
                model = KMeans(n_clusters=n_clusters, random_state=42)
                cluster_labels = model.fit_predict(X_scaled)
                
            elif method == SegmentationMethod.HIERARCHICAL:
                model = AgglomerativeClustering(n_clusters=n_clusters)
                cluster_labels = model.fit_predict(X_scaled)
                
            elif method == SegmentationMethod.DBSCAN:
                model = DBSCAN(eps=0.5, min_samples=5)
                cluster_labels = model.fit_predict(X_scaled)
                n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            
            else:
                raise ValueError(f"Unsupported clustering method: {method}")
            
            # Store model
            self.clustering_models[segmentation_id] = model
            
            # Create segments
            segments = []
            for cluster_id in range(n_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_customers = customer_data[cluster_mask]
                
                # Analyze cluster characteristics
                cluster_analysis = self._analyze_cluster(cluster_customers, features)
                
                segment = AudienceSegment(
                    segment_id=f"{segmentation_id}_cluster_{cluster_id}",
                    name=f"ML Segment {cluster_id + 1}",
                    description=cluster_analysis['description'],
                    segmentation_type=SegmentationType.PREDICTIVE,
                    segmentation_method=method,
                    size=len(cluster_customers),
                    metadata=cluster_analysis['metadata'],
                    status=SegmentStatus.ACTIVE
                )
                
                segments.append(segment)
                self.segments[segment.segment_id] = segment
            
            # Calculate segmentation quality
            if n_clusters > 1:
                silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            else:
                silhouette_avg = 0
            
            quality_metrics = {
                'silhouette_score': silhouette_avg,
                'n_clusters': n_clusters,
                'inertia': getattr(model, 'inertia_', None)
            }
            
            # Generate insights
            insights = self._generate_segmentation_insights(customer_data, cluster_labels, features)
            recommendations = self._generate_segmentation_recommendations(segments, quality_metrics)
            
            result = SegmentationResult(
                segmentation_id=segmentation_id,
                segments=segments,
                total_audience_size=len(customer_data),
                segmentation_quality=quality_metrics,
                insights=insights,
                recommendations=recommendations
            )
            
            logger.info(f"Completed ML segmentation with {n_clusters} segments")
            return result
            
        except Exception as e:
            logger.error(f"Failed to perform ML segmentation: {e}")
            raise
    
    def perform_rfm_analysis(self, transaction_data: pd.DataFrame) -> List[RFMScore]:
        """Perform RFM (Recency, Frequency, Monetary) analysis."""
        try:
            # Calculate RFM metrics
            current_date = datetime.now()
            
            rfm_data = transaction_data.groupby('customer_id').agg({
                'transaction_date': lambda x: (current_date - x.max()).days,  # Recency
                'transaction_id': 'count',  # Frequency
                'amount': 'sum'  # Monetary
            }).reset_index()
            
            rfm_data.columns = ['customer_id', 'recency', 'frequency', 'monetary']
            
            # Create RFM scores (1-5 scale)
            rfm_data['R_score'] = pd.qcut(rfm_data['recency'].rank(method='first'), 
                                         q=5, labels=[5,4,3,2,1])
            rfm_data['F_score'] = pd.qcut(rfm_data['frequency'], 
                                         q=5, labels=[1,2,3,4,5])
            rfm_data['M_score'] = pd.qcut(rfm_data['monetary'], 
                                         q=5, labels=[1,2,3,4,5])
            
            # Convert to numeric
            rfm_data['R_score'] = rfm_data['R_score'].astype(int)
            rfm_data['F_score'] = rfm_data['F_score'].astype(int)
            rfm_data['M_score'] = rfm_data['M_score'].astype(int)
            
            # Create RFM segments
            rfm_data['RFM_Segment'] = rfm_data.apply(self._assign_rfm_segment, axis=1)
            rfm_data['RFM_Score'] = rfm_data['R_score'] * 100 + rfm_data['F_score'] * 10 + rfm_data['M_score']
            
            # Calculate percentile ranks
            rfm_data['percentile_rank'] = rfm_data['RFM_Score'].rank(pct=True)
            
            # Create RFMScore objects
            rfm_scores = []
            for _, row in rfm_data.iterrows():
                rfm_score = RFMScore(
                    customer_id=row['customer_id'],
                    recency_score=row['R_score'],
                    frequency_score=row['F_score'],
                    monetary_score=row['M_score'],
                    rfm_segment=row['RFM_Segment'],
                    total_score=row['RFM_Score'],
                    percentile_rank=row['percentile_rank']
                )
                rfm_scores.append(rfm_score)
            
            # Create segments based on RFM analysis
            self._create_rfm_segments(rfm_scores)
            
            logger.info(f"Completed RFM analysis for {len(rfm_scores)} customers")
            return rfm_scores
            
        except Exception as e:
            logger.error(f"Failed to perform RFM analysis: {e}")
            return []
    
    def create_behavioral_segments(self, behavior_data: pd.DataFrame) -> List[AudienceSegment]:
        """Create segments based on behavioral patterns."""
        try:
            segments = []
            
            # Define behavioral segments
            behavioral_rules = [
                {
                    'name': 'High Engagement Users',
                    'description': 'Users with high activity and engagement',
                    'rules': [
                        {'field': 'page_views', 'operator': 'greater_than', 'value': 10},
                        {'field': 'session_duration', 'operator': 'greater_than', 'value': 300},
                        {'field': 'bounce_rate', 'operator': 'less_than', 'value': 0.3}
                    ]
                },
                {
                    'name': 'Cart Abandoners',
                    'description': 'Users who add items to cart but don\'t complete purchase',
                    'rules': [
                        {'field': 'cart_additions', 'operator': 'greater_than', 'value': 0},
                        {'field': 'purchases', 'operator': 'equals', 'value': 0},
                        {'field': 'cart_abandonment_rate', 'operator': 'greater_than', 'value': 0.5}
                    ]
                },
                {
                    'name': 'Frequent Buyers',
                    'description': 'Customers with multiple purchases',
                    'rules': [
                        {'field': 'purchase_count', 'operator': 'greater_than', 'value': 5},
                        {'field': 'days_since_last_purchase', 'operator': 'less_than', 'value': 30}
                    ]
                },
                {
                    'name': 'Price Sensitive',
                    'description': 'Users who primarily purchase discounted items',
                    'rules': [
                        {'field': 'discount_usage_rate', 'operator': 'greater_than', 'value': 0.7},
                        {'field': 'avg_discount_percent', 'operator': 'greater_than', 'value': 20}
                    ]
                },
                {
                    'name': 'Mobile Users',
                    'description': 'Users who primarily use mobile devices',
                    'rules': [
                        {'field': 'mobile_session_ratio', 'operator': 'greater_than', 'value': 0.8}
                    ]
                }
            ]
            
            for rule_set in behavioral_rules:
                # Apply behavioral rules
                matching_customers = self._apply_behavioral_rules(behavior_data, rule_set['rules'])
                
                if len(matching_customers) > 0:
                    # Create segment criteria
                    criteria = []
                    for rule in rule_set['rules']:
                        criteria.append(SegmentCriteria(
                            criteria_id=str(uuid.uuid4()),
                            name=f"{rule['field']} {rule['operator']} {rule['value']}",
                            field=rule['field'],
                            operator=rule['operator'],
                            value=rule['value']
                        ))
                    
                    segment = AudienceSegment(
                        segment_id=str(uuid.uuid4()),
                        name=rule_set['name'],
                        description=rule_set['description'],
                        segmentation_type=SegmentationType.BEHAVIORAL,
                        segmentation_method=SegmentationMethod.CUSTOM_RULES,
                        criteria=criteria,
                        size=len(matching_customers),
                        status=SegmentStatus.ACTIVE
                    )
                    
                    segments.append(segment)
                    self.segments[segment.segment_id] = segment
            
            logger.info(f"Created {len(segments)} behavioral segments")
            return segments
            
        except Exception as e:
            logger.error(f"Failed to create behavioral segments: {e}")
            return []
    
    def create_lifecycle_segments(self, customer_data: pd.DataFrame) -> List[AudienceSegment]:
        """Create customer lifecycle segments."""
        try:
            segments = []
            
            # Define lifecycle rules
            lifecycle_definitions = [
                {
                    'stage': LifecycleStage.PROSPECT,
                    'name': 'Prospects',
                    'description': 'Potential customers who haven\'t made a purchase yet',
                    'condition': lambda df: (df['purchase_count'] == 0) & (df['engagement_score'] > 0)
                },
                {
                    'stage': LifecycleStage.NEW_CUSTOMER,
                    'name': 'New Customers',
                    'description': 'Recent first-time customers',
                    'condition': lambda df: (df['purchase_count'] == 1) & (df['days_since_first_purchase'] <= 90)
                },
                {
                    'stage': LifecycleStage.ACTIVE_CUSTOMER,
                    'name': 'Active Customers',
                    'description': 'Regular customers with recent activity',
                    'condition': lambda df: (df['purchase_count'] > 1) & (df['days_since_last_purchase'] <= 90)
                },
                {
                    'stage': LifecycleStage.VIP_CUSTOMER,
                    'name': 'VIP Customers',
                    'description': 'High-value customers',
                    'condition': lambda df: (df['total_revenue'] > df['total_revenue'].quantile(0.8)) & 
                                           (df['purchase_count'] > 5)
                },
                {
                    'stage': LifecycleStage.AT_RISK,
                    'name': 'At-Risk Customers',
                    'description': 'Customers showing signs of churn',
                    'condition': lambda df: (df['days_since_last_purchase'] > 90) & 
                                           (df['days_since_last_purchase'] <= 180) & 
                                           (df['purchase_count'] > 0)
                },
                {
                    'stage': LifecycleStage.CHURNED,
                    'name': 'Churned Customers',
                    'description': 'Customers who have likely churned',
                    'condition': lambda df: (df['days_since_last_purchase'] > 180) & 
                                           (df['purchase_count'] > 0)
                }
            ]
            
            for lifecycle_def in lifecycle_definitions:
                # Apply lifecycle condition
                matching_customers = customer_data[lifecycle_def['condition'](customer_data)]
                
                if len(matching_customers) > 0:
                    segment = AudienceSegment(
                        segment_id=str(uuid.uuid4()),
                        name=lifecycle_def['name'],
                        description=lifecycle_def['description'],
                        segmentation_type=SegmentationType.LIFECYCLE,
                        segmentation_method=SegmentationMethod.CUSTOM_RULES,
                        size=len(matching_customers),
                        status=SegmentStatus.ACTIVE,
                        metadata={
                            'lifecycle_stage': lifecycle_def['stage'].value,
                            'avg_clv': matching_customers['total_revenue'].mean(),
                            'avg_purchase_count': matching_customers['purchase_count'].mean()
                        }
                    )
                    
                    segments.append(segment)
                    self.segments[segment.segment_id] = segment
            
            logger.info(f"Created {len(segments)} lifecycle segments")
            return segments
            
        except Exception as e:
            logger.error(f"Failed to create lifecycle segments: {e}")
            return []
    
    def predict_customer_segments(self, training_data: pd.DataFrame, 
                                 target_column: str,
                                 new_customers: pd.DataFrame) -> Dict[str, str]:
        """Predict segment assignments for new customers."""
        try:
            # Prepare features
            feature_columns = [col for col in training_data.columns 
                             if col not in ['customer_id', target_column]]
            
            X_train = training_data[feature_columns].fillna(0)
            y_train = training_data[target_column]
            
            # Train classification model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            X_train_scaled = self.scaler.fit_transform(X_train)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            logger.info(f"Model accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            # Predict segments for new customers
            X_new = new_customers[feature_columns].fillna(0)
            X_new_scaled = self.scaler.transform(X_new)
            predictions = model.predict(X_new_scaled)
            
            # Create prediction mapping
            segment_predictions = {}
            for i, customer_id in enumerate(new_customers['customer_id']):
                segment_predictions[customer_id] = predictions[i]
            
            # Store model
            model_id = str(uuid.uuid4())
            self.classification_models[model_id] = {
                'model': model,
                'scaler': self.scaler,
                'features': feature_columns,
                'target': target_column
            }
            
            logger.info(f"Predicted segments for {len(segment_predictions)} customers")
            return segment_predictions
            
        except Exception as e:
            logger.error(f"Failed to predict customer segments: {e}")
            return {}
    
    def get_segment_performance(self, segment_id: str, 
                               performance_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate segment performance metrics."""
        try:
            segment = self.segments.get(segment_id)
            if not segment:
                return {}
            
            # Get segment members
            segment_customers = self._get_segment_customers(segment_id)
            segment_performance = performance_data[
                performance_data['customer_id'].isin(segment_customers)
            ]
            
            if segment_performance.empty:
                return {'error': 'No performance data for segment'}
            
            # Calculate metrics
            metrics = {
                'segment_size': len(segment_performance),
                'total_revenue': segment_performance['revenue'].sum(),
                'avg_revenue_per_customer': segment_performance['revenue'].mean(),
                'conversion_rate': (segment_performance['conversions'] > 0).mean(),
                'avg_order_value': segment_performance['order_value'].mean(),
                'customer_lifetime_value': segment_performance['clv'].mean(),
                'engagement_rate': segment_performance['engagement_score'].mean(),
                'retention_rate': (segment_performance['days_since_last_purchase'] <= 90).mean(),
                'churn_risk': (segment_performance['churn_probability'] > 0.5).mean()
            }
            
            # Compare to overall population
            overall_metrics = {
                'avg_revenue_per_customer': performance_data['revenue'].mean(),
                'conversion_rate': (performance_data['conversions'] > 0).mean(),
                'avg_order_value': performance_data['order_value'].mean(),
                'engagement_rate': performance_data['engagement_score'].mean()
            }
            
            # Calculate performance ratios
            performance_ratios = {}
            for metric in ['avg_revenue_per_customer', 'conversion_rate', 'avg_order_value', 'engagement_rate']:
                if overall_metrics[metric] > 0:
                    performance_ratios[f"{metric}_ratio"] = metrics[metric] / overall_metrics[metric]
            
            metrics['performance_vs_average'] = performance_ratios
            metrics['segment_quality_score'] = self._calculate_segment_quality_score(metrics)
            
            # Update segment performance
            segment.performance_metrics = metrics
            self._update_segment_in_redis(segment)
            
            logger.info(f"Calculated performance metrics for segment: {segment_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate segment performance: {e}")
            return {}
    
    def optimize_segment_targeting(self, segment_id: str, 
                                  channel_performance: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Optimize channel targeting for a segment."""
        try:
            segment = self.segments.get(segment_id)
            if not segment:
                return {'error': 'Segment not found'}
            
            # Calculate channel efficiency scores
            channel_scores = {}
            for channel, metrics in channel_performance.items():
                # Weighted score based on multiple metrics
                score = (
                    metrics.get('conversion_rate', 0) * 0.3 +
                    metrics.get('engagement_rate', 0) * 0.2 +
                    metrics.get('roas', 0) * 0.25 +  # Return on Ad Spend
                    (1 / max(metrics.get('cost_per_acquisition', 1), 1)) * 0.25
                )
                channel_scores[channel] = score
            
            # Rank channels
            ranked_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Generate targeting recommendations
            recommendations = []
            top_channels = [channel for channel, score in ranked_channels[:3]]
            
            recommendations.append(f"Focus on top 3 channels: {', '.join(top_channels)}")
            
            # Budget allocation suggestions
            total_score = sum(channel_scores.values())
            budget_allocation = {}
            for channel, score in channel_scores.items():
                budget_allocation[channel] = (score / total_score) * 100
            
            optimization_result = {
                'segment_id': segment_id,
                'channel_rankings': ranked_channels,
                'recommended_channels': top_channels,
                'budget_allocation': budget_allocation,
                'recommendations': recommendations,
                'optimization_score': max(channel_scores.values()) if channel_scores else 0
            }
            
            logger.info(f"Optimized targeting for segment: {segment_id}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Failed to optimize segment targeting: {e}")
            return {}
    
    def _assign_rfm_segment(self, row) -> str:
        """Assign RFM segment based on RFM scores."""
        r, f, m = row['R_score'], row['F_score'], row['M_score']
        
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "New Customers"
        elif r >= 3 and f <= 2 and m >= 3:
            return "Potential Loyalists"
        elif r >= 4 and f >= 3 and m <= 2:
            return "Big Spenders"
        elif r <= 2 and f >= 4 and m >= 4:
            return "At Risk"
        elif r <= 2 and f <= 2 and m >= 4:
            return "Can't Lose Them"
        elif r <= 2 and f >= 3:
            return "Hibernating"
        else:
            return "Others"
    
    def _create_rfm_segments(self, rfm_scores: List[RFMScore]):
        """Create segments based on RFM analysis."""
        try:
            # Group by RFM segment
            segment_groups = {}
            for score in rfm_scores:
                if score.rfm_segment not in segment_groups:
                    segment_groups[score.rfm_segment] = []
                segment_groups[score.rfm_segment].append(score)
            
            # Create segments
            for segment_name, customers in segment_groups.items():
                avg_scores = {
                    'avg_recency': np.mean([c.recency_score for c in customers]),
                    'avg_frequency': np.mean([c.frequency_score for c in customers]),
                    'avg_monetary': np.mean([c.monetary_score for c in customers]),
                    'avg_total_score': np.mean([c.total_score for c in customers])
                }
                
                segment = AudienceSegment(
                    segment_id=str(uuid.uuid4()),
                    name=f"RFM - {segment_name}",
                    description=f"RFM segment: {segment_name}",
                    segmentation_type=SegmentationType.VALUE_BASED,
                    segmentation_method=SegmentationMethod.RFM_ANALYSIS,
                    size=len(customers),
                    status=SegmentStatus.ACTIVE,
                    metadata=avg_scores
                )
                
                self.segments[segment.segment_id] = segment
                self.create_segment(segment)
                
        except Exception as e:
            logger.error(f"Failed to create RFM segments: {e}")
    
    def _analyze_cluster(self, cluster_data: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
        """Analyze cluster characteristics."""
        try:
            # Calculate feature means
            feature_means = cluster_data[features].mean().to_dict()
            
            # Find distinguishing characteristics
            distinguishing_features = []
            for feature in features:
                feature_mean = feature_means[feature]
                if abs(feature_mean) > 0.5:  # Threshold for significance
                    distinguishing_features.append(f"{feature}: {feature_mean:.2f}")
            
            description = f"Cluster characterized by: {', '.join(distinguishing_features[:3])}"
            
            metadata = {
                'feature_means': feature_means,
                'cluster_size': len(cluster_data),
                'distinguishing_features': distinguishing_features
            }
            
            return {
                'description': description,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze cluster: {e}")
            return {'description': 'Cluster analysis failed', 'metadata': {}}
    
    def _apply_behavioral_rules(self, data: pd.DataFrame, rules: List[Dict[str, Any]]) -> List[str]:
        """Apply behavioral rules to identify matching customers."""
        try:
            mask = pd.Series([True] * len(data), index=data.index)
            
            for rule in rules:
                field = rule['field']
                operator = rule['operator']
                value = rule['value']
                
                if field not in data.columns:
                    continue
                
                if operator == 'equals':
                    mask &= (data[field] == value)
                elif operator == 'not_equals':
                    mask &= (data[field] != value)
                elif operator == 'greater_than':
                    mask &= (data[field] > value)
                elif operator == 'less_than':
                    mask &= (data[field] < value)
                elif operator == 'greater_than_or_equal':
                    mask &= (data[field] >= value)
                elif operator == 'less_than_or_equal':
                    mask &= (data[field] <= value)
                elif operator == 'contains':
                    mask &= data[field].str.contains(str(value), na=False)
                elif operator == 'in':
                    mask &= data[field].isin(value if isinstance(value, list) else [value])
                elif operator == 'not_in':
                    mask &= ~data[field].isin(value if isinstance(value, list) else [value])
            
            matching_customers = data[mask]['customer_id'].tolist()
            return matching_customers
            
        except Exception as e:
            logger.error(f"Failed to apply behavioral rules: {e}")
            return []
    
    def _generate_segmentation_insights(self, data: pd.DataFrame, 
                                       labels: np.ndarray, 
                                       features: List[str]) -> List[str]:
        """Generate insights from segmentation results."""
        try:
            insights = []
            
            # Calculate segment sizes
            unique_labels, counts = np.unique(labels, return_counts=True)
            n_segments = len(unique_labels)
            
            insights.append(f"Created {n_segments} distinct customer segments")
            
            # Analyze segment size distribution
            largest_segment = np.max(counts)
            smallest_segment = np.min(counts)
            size_ratio = largest_segment / smallest_segment if smallest_segment > 0 else 0
            
            if size_ratio > 5:
                insights.append("Segments have highly uneven sizes - consider adjusting parameters")
            elif size_ratio < 2:
                insights.append("Segments are well-balanced in size")
            
            # Feature importance analysis
            for feature in features[:3]:  # Top 3 features
                feature_variance = data[feature].var()
                if feature_variance > data[feature].mean():
                    insights.append(f"High variance in {feature} suggests it's a key differentiator")
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return ["Unable to generate insights"]
    
    def _generate_segmentation_recommendations(self, segments: List[AudienceSegment],
                                              quality_metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations based on segmentation results."""
        try:
            recommendations = []
            
            # Quality-based recommendations
            silhouette = quality_metrics.get('silhouette_score', 0)
            if silhouette < 0.3:
                recommendations.append("Low silhouette score - consider adjusting clustering parameters")
            elif silhouette > 0.7:
                recommendations.append("Excellent segmentation quality - proceed with targeting")
            
            # Size-based recommendations
            segment_sizes = [s.size for s in segments]
            if min(segment_sizes) < 100:
                recommendations.append("Some segments are very small - consider merging or different parameters")
            
            # Channel recommendations
            if len(segments) <= 3:
                recommendations.append("Consider email marketing for all segments")
            elif len(segments) <= 5:
                recommendations.append("Implement multi-channel approach with segment-specific messaging")
            else:
                recommendations.append("Focus on top-performing segments to avoid over-segmentation")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations"]
    
    def _calculate_segment_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall segment quality score."""
        try:
            score_components = []
            
            # Revenue performance
            if 'performance_vs_average' in metrics:
                revenue_ratio = metrics['performance_vs_average'].get('avg_revenue_per_customer_ratio', 1)
                score_components.append(min(revenue_ratio, 2) * 25)  # Cap at 2x, worth 25 points
            
            # Conversion performance  
            if 'conversion_rate' in metrics:
                conversion_rate = metrics['conversion_rate']
                score_components.append(conversion_rate * 30)  # Worth 30 points
            
            # Engagement
            if 'engagement_rate' in metrics:
                engagement_rate = metrics['engagement_rate']
                score_components.append(engagement_rate * 20)  # Worth 20 points
            
            # Retention
            if 'retention_rate' in metrics:
                retention_rate = metrics['retention_rate']
                score_components.append(retention_rate * 25)  # Worth 25 points
            
            return sum(score_components) if score_components else 0
            
        except Exception as e:
            logger.error(f"Failed to calculate quality score: {e}")
            return 0
    
    def _get_segment_customers(self, segment_id: str) -> List[str]:
        """Get list of customer IDs in a segment."""
        try:
            # In a real implementation, this would query the database
            # For demo purposes, return mock customer IDs
            segment = self.segments.get(segment_id)
            if not segment:
                return []
            
            # Generate mock customer IDs based on segment size
            return [f"customer_{i}" for i in range(segment.size)]
            
        except Exception as e:
            logger.error(f"Failed to get segment customers: {e}")
            return []
    
    def _serialize_criteria(self, criteria: SegmentCriteria) -> Dict[str, Any]:
        """Serialize segment criteria for storage."""
        return {
            'criteria_id': criteria.criteria_id,
            'name': criteria.name,
            'field': criteria.field,
            'operator': criteria.operator,
            'value': criteria.value,
            'weight': criteria.weight,
            'is_required': criteria.is_required
        }
    
    def _load_segments_from_redis(self):
        """Load existing segments from Redis."""
        try:
            segment_keys = self.redis_client.keys("segment:*")
            
            for key in segment_keys:
                segment_id = key.split(":")[1]
                segment_data = self.redis_client.hgetall(key)
                
                if segment_data:
                    criteria_data = json.loads(segment_data.get('criteria', '[]'))
                    criteria = [SegmentCriteria(**c) for c in criteria_data]
                    
                    segment = AudienceSegment(
                        segment_id=segment_id,
                        name=segment_data['name'],
                        description=segment_data['description'],
                        segmentation_type=SegmentationType(segment_data['segmentation_type']),
                        segmentation_method=SegmentationMethod(segment_data['segmentation_method']),
                        criteria=criteria,
                        size=int(segment_data['size']),
                        created_date=datetime.fromisoformat(segment_data['created_date']),
                        updated_date=datetime.fromisoformat(segment_data['updated_date']),
                        status=SegmentStatus(segment_data['status']),
                        metadata=json.loads(segment_data.get('metadata', '{}')),
                        performance_metrics=json.loads(segment_data.get('performance_metrics', '{}')),
                        targeting_channels=json.loads(segment_data.get('targeting_channels', '[]'))
                    )
                    
                    self.segments[segment_id] = segment
            
            logger.info(f"Loaded {len(self.segments)} segments from Redis")
            
        except Exception as e:
            logger.error(f"Failed to load segments from Redis: {e}")
    
    def _update_segment_in_redis(self, segment: AudienceSegment):
        """Update segment in Redis."""
        try:
            updates = {
                'updated_date': segment.updated_date.isoformat(),
                'size': segment.size,
                'performance_metrics': json.dumps(segment.performance_metrics)
            }
            
            self.redis_client.hset(f"segment:{segment.segment_id}", mapping=updates)
            
        except Exception as e:
            logger.error(f"Failed to update segment in Redis: {e}")


def create_sample_segmentation_data() -> pd.DataFrame:
    """Create sample customer data for segmentation."""
    
    np.random.seed(42)
    n_customers = 1000
    
    data = {
        'customer_id': [f'cust_{i:04d}' for i in range(n_customers)],
        'age': np.random.randint(18, 80, n_customers),
        'income': np.random.lognormal(10.5, 0.5, n_customers),
        'purchase_count': np.random.poisson(3, n_customers),
        'total_revenue': np.random.lognormal(6, 1, n_customers),
        'days_since_last_purchase': np.random.exponential(45, n_customers),
        'days_since_first_purchase': np.random.exponential(200, n_customers),
        'page_views': np.random.poisson(15, n_customers),
        'session_duration': np.random.exponential(180, n_customers),
        'bounce_rate': np.random.beta(2, 8, n_customers),
        'engagement_score': np.random.beta(5, 3, n_customers),
        'churn_probability': np.random.beta(2, 8, n_customers),
        'mobile_session_ratio': np.random.beta(3, 2, n_customers),
        'discount_usage_rate': np.random.beta(3, 7, n_customers),
        'cart_additions': np.random.poisson(5, n_customers),
        'purchases': np.random.poisson(2, n_customers)
    }
    
    # Add derived features
    df = pd.DataFrame(data)
    df['order_value'] = df['total_revenue'] / np.maximum(df['purchase_count'], 1)
    df['cart_abandonment_rate'] = (df['cart_additions'] - df['purchases']) / np.maximum(df['cart_additions'], 1)
    df['clv'] = df['total_revenue'] * 1.2  # Simple CLV estimate
    df['avg_discount_percent'] = df['discount_usage_rate'] * 30  # Assume max 30% discount
    
    return df


def run_audience_segmentation_demo():
    """
    Run the audience segmentation engine demonstration.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("👥 Audience Segmentation Engine Demo")
    print("=" * 50)
    
    print("🎯 Key Features:")
    print("  • Multi-dimensional customer segmentation")
    print("  • Machine learning-based clustering")
    print("  • RFM analysis and cohort analysis")
    print("  • Predictive segment modeling")
    print("  • Real-time segment updates")
    print("  • Cross-channel segment synchronization")
    
    print("\n📊 Segmentation Types:")
    for seg_type in SegmentationType:
        print(f"  • {seg_type.value}")
    
    print("\n🔬 Segmentation Methods:")
    for method in SegmentationMethod:
        print(f"  • {method.value}")
    
    # Initialize engine
    print("\n🚀 Initializing segmentation engine...")
    try:
        engine = AudienceSegmentationEngine()
        print("✅ Engine initialized successfully")
    except:
        engine = None
        print("ℹ️  Demo mode - engine requires Redis connection")
    
    # Create sample data
    print("\n📋 Generating sample customer data...")
    sample_data = create_sample_segmentation_data()
    print(f"✅ Generated data for {len(sample_data)} customers")
    print(f"   • Features: {list(sample_data.columns)}")
    
    # Sample segmentation features
    segmentation_features = ['age', 'income', 'purchase_count', 'total_revenue', 
                           'engagement_score', 'days_since_last_purchase']
    
    print(f"\n🔍 Segmentation Features: {segmentation_features}")
    
    # Sample ML segmentation results
    print("\n🤖 Sample ML Segmentation Results:")
    sample_segments = [
        {
            'name': 'High-Value Customers',
            'size': 180,
            'characteristics': ['High income', 'High purchase frequency', 'High engagement'],
            'avg_clv': '$2,450'
        },
        {
            'name': 'Price-Conscious Shoppers',
            'size': 320,
            'characteristics': ['Moderate income', 'High discount usage', 'Mobile-first'],
            'avg_clv': '$890'
        },
        {
            'name': 'Occasional Buyers',
            'size': 280,
            'characteristics': ['Low purchase frequency', 'High order value', 'Desktop users'],
            'avg_clv': '$1,200'
        },
        {
            'name': 'New Customers',
            'size': 150,
            'characteristics': ['Recent first purchase', 'High engagement', 'Exploring'],
            'avg_clv': '$650'
        },
        {
            'name': 'At-Risk Customers',
            'size': 70,
            'characteristics': ['Decreasing engagement', 'Long time since purchase', 'Low retention'],
            'avg_clv': '$340'
        }
    ]
    
    for i, segment in enumerate(sample_segments, 1):
        print(f"   Segment {i}: {segment['name']}")
        print(f"     • Size: {segment['size']} customers")
        print(f"     • Avg CLV: {segment['avg_clv']}")
        print(f"     • Characteristics: {', '.join(segment['characteristics'])}")
        print()
    
    # Sample RFM Analysis
    print("📈 Sample RFM Analysis Results:")
    rfm_segments = [
        {'name': 'Champions', 'count': 98, 'description': 'Best customers - high R, F, M'},
        {'name': 'Loyal Customers', 'count': 156, 'description': 'Regular customers - consistent purchases'},
        {'name': 'New Customers', 'count': 124, 'description': 'Recent customers - high recency, low frequency'},
        {'name': 'At Risk', 'count': 87, 'description': 'Previously valuable, now inactive'},
        {'name': 'Can\'t Lose Them', 'count': 45, 'description': 'High value but haven\'t purchased recently'},
        {'name': 'Others', 'count': 490, 'description': 'Various other segments'}
    ]
    
    for rfm_seg in rfm_segments:
        print(f"   • {rfm_seg['name']}: {rfm_seg['count']} customers")
        print(f"     {rfm_seg['description']}")
    
    # Sample Performance Metrics
    print("\n📊 Sample Segment Performance:")
    performance_metrics = {
        'High-Value Customers': {
            'conversion_rate': 0.18,
            'avg_order_value': 185,
            'engagement_rate': 0.76,
            'retention_rate': 0.89,
            'quality_score': 92
        },
        'Price-Conscious Shoppers': {
            'conversion_rate': 0.12,
            'avg_order_value': 67,
            'engagement_rate': 0.54,
            'retention_rate': 0.65,
            'quality_score': 74
        },
        'At-Risk Customers': {
            'conversion_rate': 0.04,
            'avg_order_value': 45,
            'engagement_rate': 0.23,
            'retention_rate': 0.12,
            'quality_score': 34
        }
    }
    
    for segment_name, metrics in performance_metrics.items():
        print(f"   {segment_name}:")
        print(f"     • Conversion Rate: {metrics['conversion_rate']:.1%}")
        print(f"     • Avg Order Value: ${metrics['avg_order_value']}")
        print(f"     • Engagement Rate: {metrics['engagement_rate']:.1%}")
        print(f"     • Retention Rate: {metrics['retention_rate']:.1%}")
        print(f"     • Quality Score: {metrics['quality_score']}/100")
        print()
    
    # Channel Optimization
    print("📢 Sample Channel Optimization:")
    channel_recommendations = [
        "High-Value Customers: Focus on premium email campaigns and VIP programs",
        "Price-Conscious Shoppers: Mobile-first approach with discount notifications",
        "New Customers: Welcome series and onboarding email sequences",
        "At-Risk Customers: Re-engagement campaigns and win-back offers"
    ]
    
    for i, rec in enumerate(channel_recommendations, 1):
        print(f"   {i}. {rec}")
    
    print("\n🌟 Advanced Features:")
    print("  • Real-time segment updates with streaming data")
    print("  • Predictive segmentation using machine learning")
    print("  • Cross-channel segment synchronization")
    print("  • A/B testing integration for segment validation")
    print("  • Custom behavioral rules and triggers")
    print("  • Lifecycle-based segment transitions")
    
    print(f"\n💼 Portfolio: https://verityai.co")
    print(f"🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
    print("⚠️  DISCLAIMER: This is demonstration code for portfolio purposes.")
    
    return engine


if __name__ == "__main__":
    run_audience_segmentation_demo()
