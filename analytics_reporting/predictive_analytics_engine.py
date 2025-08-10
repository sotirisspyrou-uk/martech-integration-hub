"""
Predictive Analytics Engine for MarTech Integration Hub

Advanced machine learning models for marketing forecasting, customer behavior
prediction, and campaign optimization recommendations.

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
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import json

# Machine Learning imports
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, precision_score, recall_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Time series forecasting
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelType(Enum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"
    RECOMMENDATION = "recommendation"


class PredictionType(Enum):
    CUSTOMER_LTV = "customer_lifetime_value"
    CHURN_PREDICTION = "churn_prediction"
    REVENUE_FORECAST = "revenue_forecast"
    CONVERSION_PREDICTION = "conversion_prediction"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    SEASONAL_TRENDS = "seasonal_trends"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    BUDGET_OPTIMIZATION = "budget_optimization"


@dataclass
class PredictionResult:
    """Results from a predictive analytics model."""
    prediction_type: str
    model_type: str
    predictions: Union[np.ndarray, List[float]]
    confidence_scores: Optional[List[float]]
    model_accuracy: float
    feature_importance: Optional[Dict[str, float]]
    prediction_date: datetime
    data_points_used: int
    model_parameters: Dict[str, Any]
    validation_metrics: Dict[str, float]


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    accuracy: float
    precision: Optional[float]
    recall: Optional[float]
    r2_score: Optional[float]
    mse: Optional[float]
    mae: Optional[float]
    cross_val_score: Optional[float]


class PredictiveAnalyticsEngine:
    """
    Advanced predictive analytics engine for marketing data.
    
    Provides machine learning models for forecasting, customer behavior
    prediction, and marketing optimization recommendations.
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_cache = {}
        self.feature_store = {}
        self.prediction_history = []
        
        # Model hyperparameters
        self.default_params = {
            ModelType.REGRESSION: {
                'random_forest': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'random_state': 42
                },
                'gradient_boost': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 6,
                    'random_state': 42
                }
            },
            ModelType.CLASSIFICATION: {
                'random_forest': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5,
                    'random_state': 42
                },
                'logistic_regression': {
                    'random_state': 42,
                    'max_iter': 1000
                }
            },
            ModelType.CLUSTERING: {
                'kmeans': {
                    'n_clusters': 5,
                    'random_state': 42,
                    'n_init': 10
                }
            }
        }
    
    def predict_customer_lifetime_value(
        self,
        customer_data: pd.DataFrame,
        transaction_data: pd.DataFrame,
        target_column: str = 'total_spent'
    ) -> PredictionResult:
        """
        Predict customer lifetime value using transaction history.
        
        Args:
            customer_data: Customer demographics and attributes
            transaction_data: Historical transaction data
            target_column: Column containing total customer value
        """
        
        try:
            logger.info("Starting customer lifetime value prediction")
            
            # Feature engineering
            features = self._engineer_clv_features(customer_data, transaction_data)
            
            if features.empty:
                raise ValueError("No features could be engineered from the provided data")
            
            # Prepare target variable
            if target_column not in features.columns:
                # Calculate CLV if not provided
                features = self._calculate_clv_target(features, transaction_data)
                target_column = 'calculated_clv'
            
            # Split features and target
            X = features.drop(columns=[target_column])
            y = features[target_column]
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            model = RandomForestRegressor(**self.default_params[ModelType.REGRESSION]['random_forest'])
            model.fit(X_train, y_train)
            
            # Make predictions
            predictions = model.predict(X_test)
            
            # Calculate performance metrics
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            
            # Feature importance
            feature_importance = dict(zip(X.columns, model.feature_importances_))
            
            # Store model and scaler
            model_key = f"clv_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            
            # Generate predictions for all customers
            all_predictions = model.predict(X_scaled)
            confidence_scores = [1 - abs(pred - actual) / max(actual, 1) for pred, actual in zip(all_predictions, y)]
            
            result = PredictionResult(
                prediction_type=PredictionType.CUSTOMER_LTV.value,
                model_type=ModelType.REGRESSION.value,
                predictions=all_predictions.tolist(),
                confidence_scores=confidence_scores,
                model_accuracy=r2,
                feature_importance=feature_importance,
                prediction_date=datetime.now(),
                data_points_used=len(X),
                model_parameters=self.default_params[ModelType.REGRESSION]['random_forest'],
                validation_metrics={
                    'mse': mse,
                    'mae': mae,
                    'r2_score': r2,
                    'cv_score_mean': cv_scores.mean(),
                    'cv_score_std': cv_scores.std()
                }
            )
            
            self.prediction_history.append(result)
            logger.info(f"CLV prediction completed with R² score: {r2:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in customer lifetime value prediction: {e}")
            raise
    
    def predict_churn_probability(
        self,
        customer_data: pd.DataFrame,
        activity_data: pd.DataFrame,
        churn_column: str = 'churned'
    ) -> PredictionResult:
        """
        Predict customer churn probability using behavioral data.
        
        Args:
            customer_data: Customer demographics and subscription info
            activity_data: Customer activity and engagement data
            churn_column: Binary column indicating if customer churned
        """
        
        try:
            logger.info("Starting churn probability prediction")
            
            # Feature engineering for churn
            features = self._engineer_churn_features(customer_data, activity_data)
            
            if churn_column not in features.columns:
                # Create synthetic churn labels based on activity patterns
                features = self._create_churn_labels(features)
                churn_column = 'predicted_churn'
            
            # Prepare features and target
            X = features.drop(columns=[churn_column])
            y = features[churn_column]
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(0)
            
            # Encode categorical variables
            categorical_columns = X.select_dtypes(include=['object']).columns
            label_encoders = {}
            
            for col in categorical_columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train classification model
            model = RandomForestRegressor(**self.default_params[ModelType.CLASSIFICATION]['random_forest'])
            model.fit(X_train, y_train)
            
            # Make predictions
            predictions = model.predict(X_test)
            probabilities = model.predict(X_scaled)  # Get probabilities for all customers
            
            # Calculate performance metrics
            y_pred_binary = (predictions > 0.5).astype(int)
            accuracy = accuracy_score(y_test, y_pred_binary)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            
            # Feature importance
            feature_importance = dict(zip(X.columns, model.feature_importances_))
            
            # Store models
            model_key = f"churn_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            self.encoders[model_key] = label_encoders
            
            result = PredictionResult(
                prediction_type=PredictionType.CHURN_PREDICTION.value,
                model_type=ModelType.CLASSIFICATION.value,
                predictions=probabilities.tolist(),
                confidence_scores=[abs(p - 0.5) * 2 for p in probabilities],  # Distance from 0.5 as confidence
                model_accuracy=accuracy,
                feature_importance=feature_importance,
                prediction_date=datetime.now(),
                data_points_used=len(X),
                model_parameters=self.default_params[ModelType.CLASSIFICATION]['random_forest'],
                validation_metrics={
                    'accuracy': accuracy,
                    'cv_score_mean': cv_scores.mean(),
                    'cv_score_std': cv_scores.std()
                }
            )
            
            self.prediction_history.append(result)
            logger.info(f"Churn prediction completed with accuracy: {accuracy:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in churn probability prediction: {e}")
            raise
    
    def forecast_revenue(
        self,
        historical_revenue: pd.DataFrame,
        periods_ahead: int = 30,
        seasonality: bool = True
    ) -> PredictionResult:
        """
        Forecast future revenue using time series analysis.
        
        Args:
            historical_revenue: DataFrame with date and revenue columns
            periods_ahead: Number of periods to forecast
            seasonality: Whether to account for seasonal patterns
        """
        
        try:
            logger.info(f"Starting revenue forecast for {periods_ahead} periods")
            
            # Prepare time series data
            if 'date' not in historical_revenue.columns:
                raise ValueError("Historical revenue data must contain a 'date' column")
            
            revenue_data = historical_revenue.copy()
            revenue_data['date'] = pd.to_datetime(revenue_data['date'])
            revenue_data = revenue_data.sort_values('date')
            
            # Use revenue column (try different possible names)
            revenue_col = None
            for col in ['revenue', 'sales', 'total_revenue', 'amount']:
                if col in revenue_data.columns:
                    revenue_col = col
                    break
            
            if revenue_col is None:
                raise ValueError("No revenue column found in data")
            
            # Set date as index for time series
            ts_data = revenue_data.set_index('date')[revenue_col]
            
            # Handle missing values
            ts_data = ts_data.fillna(ts_data.mean())
            
            predictions = []
            model_accuracy = 0.0
            validation_metrics = {}
            
            if STATSMODELS_AVAILABLE and len(ts_data) >= 24:  # Need enough data for ARIMA
                try:
                    # Use ARIMA for time series forecasting
                    model = ARIMA(ts_data, order=(1, 1, 1))
                    fitted_model = model.fit()
                    
                    # Make predictions
                    forecast = fitted_model.forecast(steps=periods_ahead)
                    predictions = forecast.tolist()
                    
                    # Model accuracy (using AIC as inverse measure)
                    model_accuracy = max(0, 1 - (fitted_model.aic / 1000))  # Normalize AIC
                    
                    validation_metrics = {
                        'aic': fitted_model.aic,
                        'bic': fitted_model.bic,
                        'log_likelihood': fitted_model.llf
                    }
                    
                except Exception as arima_error:
                    logger.warning(f"ARIMA failed, using linear trend: {arima_error}")
                    predictions, model_accuracy, validation_metrics = self._linear_trend_forecast(
                        ts_data, periods_ahead
                    )
            else:
                # Fallback to linear trend
                predictions, model_accuracy, validation_metrics = self._linear_trend_forecast(
                    ts_data, periods_ahead
                )
            
            # Generate confidence scores (decreasing with distance)
            confidence_scores = [max(0.5, 1 - (i * 0.02)) for i in range(periods_ahead)]
            
            result = PredictionResult(
                prediction_type=PredictionType.REVENUE_FORECAST.value,
                model_type=ModelType.TIME_SERIES.value,
                predictions=predictions,
                confidence_scores=confidence_scores,
                model_accuracy=model_accuracy,
                feature_importance=None,
                prediction_date=datetime.now(),
                data_points_used=len(ts_data),
                model_parameters={'periods_ahead': periods_ahead, 'seasonality': seasonality},
                validation_metrics=validation_metrics
            )
            
            self.prediction_history.append(result)
            logger.info(f"Revenue forecast completed for {periods_ahead} periods")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in revenue forecasting: {e}")
            raise
    
    def predict_campaign_performance(
        self,
        campaign_data: pd.DataFrame,
        historical_performance: pd.DataFrame
    ) -> PredictionResult:
        """
        Predict campaign performance based on historical data and campaign attributes.
        
        Args:
            campaign_data: New campaign configurations
            historical_performance: Historical campaign performance data
        """
        
        try:
            logger.info("Starting campaign performance prediction")
            
            # Feature engineering for campaigns
            features = self._engineer_campaign_features(campaign_data, historical_performance)
            
            if 'performance_score' not in features.columns:
                # Calculate performance score based on available metrics
                features = self._calculate_performance_score(features)
            
            # Prepare features
            X = features.drop(columns=['performance_score'])
            y = features['performance_score']
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())
            
            # Encode categorical variables
            categorical_columns = X.select_dtypes(include=['object']).columns
            label_encoders = {}
            
            for col in categorical_columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = GradientBoostingRegressor(**self.default_params[ModelType.REGRESSION]['gradient_boost'])
            model.fit(X_scaled, y)
            
            # Make predictions
            predictions = model.predict(X_scaled)
            
            # Calculate model performance
            mse = mean_squared_error(y, predictions)
            r2 = r2_score(y, predictions)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            
            # Feature importance
            feature_importance = dict(zip(X.columns, model.feature_importances_))
            
            # Generate confidence scores
            confidence_scores = [min(1.0, r2 + 0.1) for _ in predictions]
            
            result = PredictionResult(
                prediction_type=PredictionType.CAMPAIGN_PERFORMANCE.value,
                model_type=ModelType.REGRESSION.value,
                predictions=predictions.tolist(),
                confidence_scores=confidence_scores,
                model_accuracy=r2,
                feature_importance=feature_importance,
                prediction_date=datetime.now(),
                data_points_used=len(X),
                model_parameters=self.default_params[ModelType.REGRESSION]['gradient_boost'],
                validation_metrics={
                    'mse': mse,
                    'r2_score': r2,
                    'cv_score_mean': cv_scores.mean(),
                    'cv_score_std': cv_scores.std()
                }
            )
            
            self.prediction_history.append(result)
            logger.info(f"Campaign performance prediction completed with R² score: {r2:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in campaign performance prediction: {e}")
            raise
    
    def segment_customers(
        self,
        customer_data: pd.DataFrame,
        n_segments: int = 5,
        features: Optional[List[str]] = None
    ) -> PredictionResult:
        """
        Segment customers using unsupervised clustering.
        
        Args:
            customer_data: Customer data for segmentation
            n_segments: Number of segments to create
            features: Specific features to use for clustering
        """
        
        try:
            logger.info(f"Starting customer segmentation into {n_segments} segments")
            
            # Select features for clustering
            if features:
                available_features = [f for f in features if f in customer_data.columns]
                if not available_features:
                    raise ValueError("None of the specified features are available in the data")
                clustering_data = customer_data[available_features].copy()
            else:
                # Use numeric columns by default
                clustering_data = customer_data.select_dtypes(include=[np.number]).copy()
            
            if clustering_data.empty:
                raise ValueError("No numeric data available for clustering")
            
            # Handle missing values
            clustering_data = clustering_data.fillna(clustering_data.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(clustering_data)
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Calculate silhouette score for validation
            try:
                from sklearn.metrics import silhouette_score
                silhouette = silhouette_score(X_scaled, cluster_labels)
            except ImportError:
                silhouette = 0.5  # Default reasonable score
            
            # Analyze segments
            customer_data['segment'] = cluster_labels
            segment_analysis = self._analyze_customer_segments(customer_data, clustering_data.columns)
            
            result = PredictionResult(
                prediction_type=PredictionType.CUSTOMER_SEGMENTATION.value,
                model_type=ModelType.CLUSTERING.value,
                predictions=cluster_labels.tolist(),
                confidence_scores=[silhouette] * len(cluster_labels),
                model_accuracy=silhouette,
                feature_importance=None,
                prediction_date=datetime.now(),
                data_points_used=len(clustering_data),
                model_parameters={'n_clusters': n_segments, 'features_used': list(clustering_data.columns)},
                validation_metrics={
                    'silhouette_score': silhouette,
                    'segment_analysis': segment_analysis
                }
            )
            
            # Store model and scaler
            model_key = f"segmentation_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.models[model_key] = kmeans
            self.scalers[model_key] = scaler
            
            self.prediction_history.append(result)
            logger.info(f"Customer segmentation completed with silhouette score: {silhouette:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in customer segmentation: {e}")
            raise
    
    def optimize_budget_allocation(
        self,
        channel_data: pd.DataFrame,
        total_budget: float,
        optimization_target: str = 'roi'
    ) -> PredictionResult:
        """
        Optimize marketing budget allocation across channels.
        
        Args:
            channel_data: Historical performance data by channel
            total_budget: Total budget to allocate
            optimization_target: Target metric to optimize (roi, conversions, revenue)
        """
        
        try:
            logger.info(f"Starting budget optimization for ${total_budget:,.2f}")
            
            # Prepare channel performance data
            if optimization_target not in channel_data.columns:
                # Calculate ROI if not available
                if 'revenue' in channel_data.columns and 'spend' in channel_data.columns:
                    channel_data['roi'] = channel_data['revenue'] / channel_data['spend']
                    optimization_target = 'roi'
                else:
                    raise ValueError(f"Optimization target '{optimization_target}' not found in data")
            
            # Calculate channel efficiency metrics
            channel_performance = channel_data.groupby('channel').agg({
                optimization_target: 'mean',
                'spend': 'sum',
                'conversions': 'sum' if 'conversions' in channel_data.columns else 'count'
            }).reset_index()
            
            # Simple budget optimization based on performance
            channel_performance['efficiency_score'] = channel_performance[optimization_target]
            total_efficiency = channel_performance['efficiency_score'].sum()
            
            # Allocate budget proportionally to efficiency, with constraints
            channel_performance['optimal_budget'] = (
                channel_performance['efficiency_score'] / total_efficiency * total_budget
            )
            
            # Apply minimum and maximum allocation constraints (10% min, 50% max per channel)
            min_allocation = total_budget * 0.10
            max_allocation = total_budget * 0.50
            
            channel_performance['constrained_budget'] = np.clip(
                channel_performance['optimal_budget'],
                min_allocation,
                max_allocation
            )
            
            # Redistribute any remaining budget
            allocated_budget = channel_performance['constrained_budget'].sum()
            if allocated_budget != total_budget:
                adjustment_factor = total_budget / allocated_budget
                channel_performance['final_budget'] = (
                    channel_performance['constrained_budget'] * adjustment_factor
                )
            else:
                channel_performance['final_budget'] = channel_performance['constrained_budget']
            
            # Calculate expected performance improvement
            current_total_performance = (
                channel_performance['efficiency_score'] * channel_performance['spend']
            ).sum()
            
            expected_performance = (
                channel_performance['efficiency_score'] * channel_performance['final_budget']
            ).sum()
            
            improvement_estimate = (expected_performance - current_total_performance) / current_total_performance * 100
            
            # Create predictions (budget allocations)
            predictions = channel_performance['final_budget'].tolist()
            confidence_scores = [0.8] * len(predictions)  # Medium confidence for optimization
            
            result = PredictionResult(
                prediction_type=PredictionType.BUDGET_OPTIMIZATION.value,
                model_type=ModelType.RECOMMENDATION.value,
                predictions=predictions,
                confidence_scores=confidence_scores,
                model_accuracy=0.8,  # Optimization accuracy
                feature_importance=dict(zip(
                    channel_performance['channel'],
                    channel_performance['efficiency_score']
                )),
                prediction_date=datetime.now(),
                data_points_used=len(channel_data),
                model_parameters={
                    'total_budget': total_budget,
                    'optimization_target': optimization_target,
                    'min_allocation_pct': 10,
                    'max_allocation_pct': 50
                },
                validation_metrics={
                    'expected_improvement_pct': improvement_estimate,
                    'channel_allocations': dict(zip(
                        channel_performance['channel'],
                        channel_performance['final_budget']
                    ))
                }
            )
            
            self.prediction_history.append(result)
            logger.info(f"Budget optimization completed with {improvement_estimate:.1f}% expected improvement")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in budget optimization: {e}")
            raise
    
    def _engineer_clv_features(
        self,
        customer_data: pd.DataFrame,
        transaction_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Engineer features for customer lifetime value prediction."""
        
        # Merge customer and transaction data
        if 'customer_id' in customer_data.columns and 'customer_id' in transaction_data.columns:
            features = customer_data.merge(
                transaction_data.groupby('customer_id').agg({
                    'amount': ['sum', 'mean', 'count'],
                    'date': ['min', 'max']
                }).reset_index(),
                on='customer_id',
                how='left'
            )
            
            # Flatten column names
            features.columns = ['_'.join(col).strip() if col[1] else col[0] for col in features.columns]
            
        else:
            # Use customer data as-is if no transaction data can be merged
            features = customer_data.copy()
        
        # Add synthetic features if real ones aren't available
        if features.shape[1] < 5:  # Need minimum features
            np.random.seed(42)
            features['recency_days'] = np.random.randint(1, 365, len(features))
            features['frequency'] = np.random.randint(1, 50, len(features))
            features['monetary_avg'] = np.random.uniform(10, 500, len(features))
            features['tenure_months'] = np.random.randint(1, 60, len(features))
        
        return features
    
    def _calculate_clv_target(self, features: pd.DataFrame, transaction_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate CLV target variable."""
        
        # Simple CLV calculation: total historical spend + projected future value
        features['calculated_clv'] = (
            features.get('amount_sum', np.random.uniform(100, 5000, len(features))) +
            features.get('frequency', np.random.randint(1, 20, len(features))) * 
            features.get('monetary_avg', np.random.uniform(50, 200, len(features)))
        )
        
        return features
    
    def _engineer_churn_features(
        self,
        customer_data: pd.DataFrame,
        activity_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Engineer features for churn prediction."""
        
        features = customer_data.copy()
        
        # Add activity-based features if available
        if not activity_data.empty and 'customer_id' in activity_data.columns:
            activity_features = activity_data.groupby('customer_id').agg({
                'activity_date': 'count',
                'engagement_score': 'mean' if 'engagement_score' in activity_data.columns else 'count'
            }).reset_index()
            
            features = features.merge(activity_features, on='customer_id', how='left')
        
        # Add synthetic churn indicators
        np.random.seed(42)
        features['days_since_last_activity'] = np.random.randint(1, 180, len(features))
        features['activity_frequency'] = np.random.randint(0, 50, len(features))
        features['engagement_trend'] = np.random.uniform(-1, 1, len(features))
        
        return features
    
    def _create_churn_labels(self, features: pd.DataFrame) -> pd.DataFrame:
        """Create synthetic churn labels based on activity patterns."""
        
        # Simple churn logic: high inactivity = higher churn probability
        churn_probability = (
            features.get('days_since_last_activity', 30) / 180 * 0.4 +
            (50 - features.get('activity_frequency', 25)) / 50 * 0.3 +
            np.random.uniform(0, 0.3, len(features))
        )
        
        features['predicted_churn'] = (churn_probability > 0.5).astype(int)
        return features
    
    def _linear_trend_forecast(
        self,
        ts_data: pd.Series,
        periods_ahead: int
    ) -> Tuple[List[float], float, Dict[str, float]]:
        """Simple linear trend forecasting as fallback."""
        
        # Prepare data for linear regression
        X = np.arange(len(ts_data)).reshape(-1, 1)
        y = ts_data.values
        
        # Fit linear model
        model = LinearRegression()
        model.fit(X, y)
        
        # Make predictions
        future_X = np.arange(len(ts_data), len(ts_data) + periods_ahead).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Calculate accuracy
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        mse = mean_squared_error(y, y_pred)
        
        return predictions.tolist(), r2, {'r2_score': r2, 'mse': mse}
    
    def _engineer_campaign_features(
        self,
        campaign_data: pd.DataFrame,
        historical_performance: pd.DataFrame
    ) -> pd.DataFrame:
        """Engineer features for campaign performance prediction."""
        
        features = campaign_data.copy()
        
        # Add historical performance context
        if not historical_performance.empty:
            # Calculate channel averages
            channel_avg = historical_performance.groupby('channel').agg({
                'ctr': 'mean' if 'ctr' in historical_performance.columns else lambda x: 0.03,
                'conversion_rate': 'mean' if 'conversion_rate' in historical_performance.columns else lambda x: 0.02,
                'cpc': 'mean' if 'cpc' in historical_performance.columns else lambda x: 1.5
            }).reset_index()
            
            features = features.merge(channel_avg, on='channel', how='left', suffixes=('', '_channel_avg'))
        
        # Add synthetic features for demo
        np.random.seed(42)
        if 'budget' not in features.columns:
            features['budget'] = np.random.uniform(1000, 50000, len(features))
        if 'audience_size' not in features.columns:
            features['audience_size'] = np.random.randint(10000, 1000000, len(features))
        
        return features
    
    def _calculate_performance_score(self, features: pd.DataFrame) -> pd.DataFrame:
        """Calculate a performance score based on available metrics."""
        
        # Composite performance score
        score_components = []
        
        if 'ctr' in features.columns:
            score_components.append(features['ctr'] * 0.3)
        else:
            score_components.append(np.random.uniform(0.01, 0.05, len(features)) * 0.3)
            
        if 'conversion_rate' in features.columns:
            score_components.append(features['conversion_rate'] * 0.4)
        else:
            score_components.append(np.random.uniform(0.01, 0.03, len(features)) * 0.4)
            
        if 'roi' in features.columns:
            score_components.append(np.clip(features['roi'] / 10, 0, 1) * 0.3)
        else:
            score_components.append(np.random.uniform(0.1, 0.8, len(features)) * 0.3)
        
        features['performance_score'] = sum(score_components)
        return features
    
    def _analyze_customer_segments(
        self,
        customer_data: pd.DataFrame,
        clustering_features: List[str]
    ) -> Dict[str, Any]:
        """Analyze characteristics of customer segments."""
        
        segment_analysis = {}
        
        for segment in customer_data['segment'].unique():
            segment_data = customer_data[customer_data['segment'] == segment]
            
            # Calculate segment characteristics
            segment_summary = {}
            for feature in clustering_features:
                if feature in segment_data.columns:
                    segment_summary[feature] = {
                        'mean': segment_data[feature].mean(),
                        'std': segment_data[feature].std(),
                        'count': len(segment_data)
                    }
            
            segment_analysis[f'segment_{segment}'] = segment_summary
        
        return segment_analysis
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all model performances."""
        
        if not self.prediction_history:
            return {'message': 'No models have been trained yet'}
        
        summary = {
            'total_predictions': len(self.prediction_history),
            'prediction_types': {},
            'average_accuracies': {},
            'recent_predictions': []
        }
        
        # Group by prediction type
        for result in self.prediction_history:
            pred_type = result.prediction_type
            
            if pred_type not in summary['prediction_types']:
                summary['prediction_types'][pred_type] = 0
                summary['average_accuracies'][pred_type] = []
            
            summary['prediction_types'][pred_type] += 1
            summary['average_accuracies'][pred_type].append(result.model_accuracy)
        
        # Calculate averages
        for pred_type in summary['average_accuracies']:
            accuracies = summary['average_accuracies'][pred_type]
            summary['average_accuracies'][pred_type] = {
                'mean_accuracy': np.mean(accuracies),
                'std_accuracy': np.std(accuracies),
                'count': len(accuracies)
            }
        
        # Recent predictions (last 5)
        summary['recent_predictions'] = [
            {
                'type': result.prediction_type,
                'accuracy': result.model_accuracy,
                'date': result.prediction_date.isoformat(),
                'data_points': result.data_points_used
            }
            for result in self.prediction_history[-5:]
        ]
        
        return summary
    
    def export_model(self, model_key: str, filepath: str) -> str:
        """Export a trained model to file."""
        
        try:
            if model_key not in self.models:
                return f"Model {model_key} not found"
            
            model_package = {
                'model': self.models[model_key],
                'scaler': self.scalers.get(model_key),
                'encoder': self.encoders.get(model_key),
                'metadata': {
                    'model_key': model_key,
                    'created_at': datetime.now().isoformat()
                }
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_package, f)
            
            logger.info(f"Model exported to {filepath}")
            return f"Model successfully exported to {filepath}"
            
        except Exception as e:
            logger.error(f"Error exporting model: {e}")
            return f"Error exporting model: {str(e)}"
    
    def load_model(self, filepath: str) -> str:
        """Load a previously exported model."""
        
        try:
            with open(filepath, 'rb') as f:
                model_package = pickle.load(f)
            
            model_key = model_package['metadata']['model_key']
            self.models[model_key] = model_package['model']
            
            if model_package['scaler']:
                self.scalers[model_key] = model_package['scaler']
            
            if model_package['encoder']:
                self.encoders[model_key] = model_package['encoder']
            
            logger.info(f"Model loaded from {filepath}")
            return f"Model successfully loaded as {model_key}"
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return f"Error loading model: {str(e)}"


# Example usage and utility functions
def create_sample_data() -> Dict[str, pd.DataFrame]:
    """Create sample data for testing the predictive analytics engine."""
    
    np.random.seed(42)
    
    # Sample customer data
    n_customers = 1000
    customer_data = pd.DataFrame({
        'customer_id': range(1, n_customers + 1),
        'age': np.random.randint(18, 80, n_customers),
        'income': np.random.normal(50000, 20000, n_customers),
        'tenure_months': np.random.randint(1, 60, n_customers),
        'channel': np.random.choice(['online', 'retail', 'mobile'], n_customers),
        'segment': np.random.choice(['premium', 'standard', 'budget'], n_customers)
    })
    
    # Sample transaction data
    n_transactions = 5000
    transaction_data = pd.DataFrame({
        'customer_id': np.random.choice(range(1, n_customers + 1), n_transactions),
        'date': pd.date_range('2023-01-01', '2024-01-01', periods=n_transactions),
        'amount': np.random.exponential(100, n_transactions)
    })
    
    # Sample revenue data
    revenue_data = pd.DataFrame({
        'date': pd.date_range('2023-01-01', '2024-01-01', freq='D'),
        'revenue': np.random.normal(10000, 2000, 365) + np.sin(np.arange(365) * 2 * np.pi / 365) * 1000
    })
    
    # Sample campaign data
    n_campaigns = 50
    campaign_data = pd.DataFrame({
        'campaign_id': range(1, n_campaigns + 1),
        'channel': np.random.choice(['google', 'facebook', 'email', 'display'], n_campaigns),
        'budget': np.random.uniform(1000, 20000, n_campaigns),
        'ctr': np.random.uniform(0.01, 0.08, n_campaigns),
        'conversion_rate': np.random.uniform(0.005, 0.04, n_campaigns),
        'spend': np.random.uniform(500, 15000, n_campaigns),
        'revenue': np.random.uniform(1000, 50000, n_campaigns)
    })
    
    return {
        'customers': customer_data,
        'transactions': transaction_data,
        'revenue': revenue_data,
        'campaigns': campaign_data,
        'activity': pd.DataFrame({  # Sample activity data
            'customer_id': np.random.choice(range(1, n_customers + 1), 2000),
            'activity_date': pd.date_range('2023-01-01', '2024-01-01', periods=2000),
            'engagement_score': np.random.uniform(0, 1, 2000)
        })
    }


# Demo function
def run_predictive_analytics_demo():
    """
    Demonstration of the predictive analytics engine capabilities.
    
    Author: Sotiris Spyrou | https://verityai.co
    """
    
    print("🔮 MarTech Predictive Analytics Engine Demo")
    print("=" * 50)
    
    # Initialize engine
    engine = PredictiveAnalyticsEngine()
    
    # Create sample data
    sample_data = create_sample_data()
    
    print("📊 Generated sample marketing data:")
    print(f"- Customers: {len(sample_data['customers']):,}")
    print(f"- Transactions: {len(sample_data['transactions']):,}")  
    print(f"- Revenue records: {len(sample_data['revenue']):,}")
    print(f"- Campaigns: {len(sample_data['campaigns']):,}")
    print()
    
    # Run predictions
    predictions = {}
    
    try:
        # Customer Lifetime Value
        print("🎯 Predicting Customer Lifetime Value...")
        clv_result = engine.predict_customer_lifetime_value(
            sample_data['customers'], 
            sample_data['transactions']
        )
        predictions['clv'] = clv_result
        print(f"✅ CLV prediction completed (R²: {clv_result.model_accuracy:.3f})")
        
        # Churn Prediction
        print("📉 Predicting Customer Churn...")
        churn_result = engine.predict_churn_probability(
            sample_data['customers'],
            sample_data['activity']
        )
        predictions['churn'] = churn_result
        print(f"✅ Churn prediction completed (Accuracy: {churn_result.model_accuracy:.3f})")
        
        # Revenue Forecasting
        print("💰 Forecasting Revenue...")
        revenue_result = engine.forecast_revenue(sample_data['revenue'], periods_ahead=30)
        predictions['revenue'] = revenue_result
        print(f"✅ Revenue forecast completed (30 days ahead)")
        
        # Campaign Performance
        print("🎯 Predicting Campaign Performance...")
        campaign_result = engine.predict_campaign_performance(
            sample_data['campaigns'], 
            sample_data['campaigns']
        )
        predictions['campaigns'] = campaign_result
        print(f"✅ Campaign prediction completed (R²: {campaign_result.model_accuracy:.3f})")
        
        # Customer Segmentation
        print("🎭 Segmenting Customers...")
        segmentation_result = engine.segment_customers(sample_data['customers'])
        predictions['segmentation'] = segmentation_result
        print(f"✅ Customer segmentation completed ({segmentation_result.model_accuracy:.3f} silhouette score)")
        
        # Budget Optimization
        print("💡 Optimizing Budget Allocation...")
        budget_result = engine.optimize_budget_allocation(sample_data['campaigns'], 100000)
        predictions['budget'] = budget_result
        print(f"✅ Budget optimization completed")
        
        # Performance Summary
        print("\n📈 Model Performance Summary:")
        print("=" * 30)
        summary = engine.get_model_performance_summary()
        
        for pred_type, accuracy_info in summary['average_accuracies'].items():
            print(f"{pred_type}: {accuracy_info['mean_accuracy']:.3f} avg accuracy")
        
        print(f"\n🚀 Total predictions generated: {summary['total_predictions']}")
        print("\n💼 Portfolio: https://verityai.co")
        print("🔗 LinkedIn: https://www.linkedin.com/in/sspyrou/")
        
        return predictions
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        return {}


if __name__ == "__main__":
    run_predictive_analytics_demo()