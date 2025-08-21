"""
Predictive Analytics Engine for Carbon Footprint Calculator
Uses machine learning to forecast future emissions and provide insights
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class PredictiveAnalytics:
    def __init__(self):
        self.models = {
            'linear': LinearRegression(),
            'forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        }
        self.scalers = {
            'linear': StandardScaler(),
            'forest': StandardScaler(),
            'gradient_boost': StandardScaler()
        }
        self.is_trained = {
            'linear': False,
            'forest': False,
            'gradient_boost': False
        }
        self.feature_importance = {}
    
    def get_model_info(self) -> Dict[str, Dict]:
        """Get information about available models"""
        return {
            'linear': {
                'name': 'Linear Regression',
                'description': 'Simple linear relationship model, fast and interpretable',
                'best_for': 'Linear trends and patterns',
                'complexity': 'Low'
            },
            'forest': {
                'name': 'Random Forest',
                'description': 'Ensemble of decision trees, handles non-linear patterns well',
                'best_for': 'Complex patterns and feature interactions',
                'complexity': 'Medium'
            },
            'gradient_boost': {
                'name': 'Gradient Boosting',
                'description': 'Sequential ensemble method, often provides highest accuracy',
                'best_for': 'High accuracy predictions with complex data',
                'complexity': 'High'
            }
        }
    
    def get_trained_models(self) -> List[str]:
        """Get list of successfully trained models"""
        return [model for model, trained in self.is_trained.items() if trained]
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning models"""
        if df.empty:
            return df
            
        # Convert date to datetime if it's not already
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
            # Extract temporal features
            df['day_of_week'] = df['date'].dt.dayofweek
            df['month'] = df['date'].dt.month
            df['day_of_year'] = df['date'].dt.dayofyear
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
        # Create category-based features
        categories = ['transport', 'food', 'appliances', 'entertainment', 'other']
        for category in categories:
            df[f'{category}_emissions'] = 0.0
            
        # Aggregate emissions by category
        if 'category' in df.columns and 'carbon_footprint' in df.columns:
            for idx, row in df.iterrows():
                category = row['category'].lower()
                if category in categories:
                    df.at[idx, f'{category}_emissions'] = row['carbon_footprint']
        
        # Rolling averages (7-day and 30-day)
        if len(df) > 1:
            df = df.sort_values('date')
            df['rolling_7d_avg'] = df['carbon_footprint'].rolling(window=7, min_periods=1).mean()
            df['rolling_30d_avg'] = df['carbon_footprint'].rolling(window=30, min_periods=1).mean()
            
            # Trend indicators
            df['trend_7d'] = df['carbon_footprint'] - df['rolling_7d_avg']
            df['emissions_volatility'] = df['carbon_footprint'].rolling(window=7, min_periods=1).std()
        else:
            df['rolling_7d_avg'] = df['carbon_footprint']
            df['rolling_30d_avg'] = df['carbon_footprint']
            df['trend_7d'] = 0
            df['emissions_volatility'] = 0
            
        return df
    
    def train_models(self, df: pd.DataFrame) -> Dict[str, float]:
        """Train predictive models on historical data"""
        if len(df) < 10:  # Need minimum data for training
            return {"error": "Insufficient data for training (minimum 10 entries required)"}
        
        # Prepare features
        df_features = self.prepare_features(df.copy())
        
        # Select feature columns
        feature_columns = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'transport_emissions', 'food_emissions', 'appliances_emissions', 
            'entertainment_emissions', 'other_emissions',
            'rolling_7d_avg', 'rolling_30d_avg', 'trend_7d', 'emissions_volatility'
        ]
        
        # Ensure all feature columns exist
        for col in feature_columns:
            if col not in df_features.columns:
                df_features[col] = 0
        
        X = df_features[feature_columns].fillna(0)
        y = df_features['carbon_footprint'].fillna(0)
        
        if len(X) < 5:
            return {"error": "Insufficient data for model training"}
        
        # Split data
        if len(X) > 20:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        else:
            X_train, X_test, y_train, y_test = X, X, y, y
        
        results = {}
        
        # Train models
        for model_name, model in self.models.items():
            try:
                # Scale features
                X_train_scaled = self.scalers[model_name].fit_transform(X_train)
                X_test_scaled = self.scalers[model_name].transform(X_test)
                
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                results[model_name] = {
                    'mae': mae,
                    'r2_score': r2,
                    'trained': True
                }
                
                self.is_trained[model_name] = True
                
                # Store feature importance for Random Forest
                if model_name == 'forest':
                    importance = dict(zip(feature_columns, model.feature_importances_))
                    self.feature_importance = importance
                    
            except Exception as e:
                results[model_name] = {'error': str(e), 'trained': False}
        
        return results
    
    def predict_future_emissions(self, df: pd.DataFrame, days_ahead: int = 30) -> Dict:
        """Predict future emissions for specified number of days"""
        if not any(self.is_trained.values()):
            return {"error": "Models not trained yet. Please train models first."}
        
        if df.empty:
            return {"error": "No historical data available for prediction"}
        
        # Prepare base data
        df_prepared = self.prepare_features(df.copy())
        latest_date = pd.to_datetime(df_prepared['date']).max()
        
        # Generate future dates
        future_dates = [latest_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # Create feature columns for future predictions
        feature_columns = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'transport_emissions', 'food_emissions', 'appliances_emissions', 
            'entertainment_emissions', 'other_emissions',
            'rolling_7d_avg', 'rolling_30d_avg', 'trend_7d', 'emissions_volatility'
        ]
        
        predictions = {}
        
        for model_name, model in self.models.items():
            if not self.is_trained[model_name]:
                continue
                
            try:
                future_predictions = []
                
                for future_date in future_dates:
                    # Create features for future date
                    future_features = {
                        'day_of_week': future_date.weekday(),
                        'month': future_date.month,
                        'day_of_year': future_date.timetuple().tm_yday,
                        'is_weekend': 1 if future_date.weekday() >= 5 else 0,
                        'transport_emissions': df_prepared['transport_emissions'].mean(),
                        'food_emissions': df_prepared['food_emissions'].mean(),
                        'appliances_emissions': df_prepared['appliances_emissions'].mean(),
                        'entertainment_emissions': df_prepared['entertainment_emissions'].mean(),
                        'other_emissions': df_prepared['other_emissions'].mean(),
                        'rolling_7d_avg': df_prepared['rolling_7d_avg'].iloc[-7:].mean(),
                        'rolling_30d_avg': df_prepared['rolling_30d_avg'].mean(),
                        'trend_7d': df_prepared['trend_7d'].mean(),
                        'emissions_volatility': df_prepared['emissions_volatility'].mean()
                    }
                    
                    # Convert to array and scale
                    X_future = np.array([[future_features[col] for col in feature_columns]])
                    X_future_scaled = self.scalers[model_name].transform(X_future)
                    
                    # Predict
                    prediction = model.predict(X_future_scaled)[0]
                    future_predictions.append(max(0, prediction))  # Ensure non-negative
                
                predictions[model_name] = {
                    'dates': [date.strftime('%Y-%m-%d') for date in future_dates],
                    'predictions': future_predictions,
                    'total_predicted': sum(future_predictions),
                    'daily_average': np.mean(future_predictions)
                }
                
            except Exception as e:
                predictions[model_name] = {'error': str(e)}
        
        return predictions
    
    def predict_with_model(self, df: pd.DataFrame, model_name: str, days_ahead: int = 30) -> Dict:
        """Predict future emissions using a specific model"""
        if model_name not in self.models:
            return {"error": f"Model '{model_name}' not available. Available models: {list(self.models.keys())}"}
        
        if not self.is_trained[model_name]:
            return {"error": f"Model '{model_name}' not trained yet. Please train models first."}
        
        if df.empty:
            return {"error": "No historical data available for prediction"}
        
        # Prepare base data
        df_prepared = self.prepare_features(df.copy())
        latest_date = pd.to_datetime(df_prepared['date']).max()
        
        # Generate future dates
        future_dates = [latest_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # Create feature columns for future predictions
        feature_columns = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'transport_emissions', 'food_emissions', 'appliances_emissions', 
            'entertainment_emissions', 'other_emissions',
            'rolling_7d_avg', 'rolling_30d_avg', 'trend_7d', 'emissions_volatility'
        ]
        
        try:
            model = self.models[model_name]
            future_predictions = []
            
            for future_date in future_dates:
                # Create features for future date
                future_features = {
                    'day_of_week': future_date.weekday(),
                    'month': future_date.month,
                    'day_of_year': future_date.timetuple().tm_yday,
                    'is_weekend': 1 if future_date.weekday() >= 5 else 0,
                    'transport_emissions': df_prepared['transport_emissions'].mean(),
                    'food_emissions': df_prepared['food_emissions'].mean(),
                    'appliances_emissions': df_prepared['appliances_emissions'].mean(),
                    'entertainment_emissions': df_prepared['entertainment_emissions'].mean(),
                    'other_emissions': df_prepared['other_emissions'].mean(),
                    'rolling_7d_avg': df_prepared['rolling_7d_avg'].iloc[-7:].mean(),
                    'rolling_30d_avg': df_prepared['rolling_30d_avg'].mean(),
                    'trend_7d': df_prepared['trend_7d'].mean(),
                    'emissions_volatility': df_prepared['emissions_volatility'].mean()
                }
                
                # Convert to array and scale
                X_future = np.array([[future_features[col] for col in feature_columns]])
                X_future_scaled = self.scalers[model_name].transform(X_future)
                
                # Predict
                prediction = model.predict(X_future_scaled)[0]
                future_predictions.append(max(0, prediction))  # Ensure non-negative
            
            model_info = self.get_model_info()[model_name]
            
            return {
                'model_name': model_name,
                'model_display_name': model_info['name'],
                'dates': [date.strftime('%Y-%m-%d') for date in future_dates],
                'predictions': future_predictions,
                'total_predicted': sum(future_predictions),
                'daily_average': np.mean(future_predictions),
                'model_description': model_info['description']
            }
            
        except Exception as e:
            return {'error': f"Error predicting with {model_name}: {str(e)}"}
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns in emission data"""
        if df.empty:
            return {"error": "No data available for pattern analysis"}
        
        df_analysis = self.prepare_features(df.copy())
        
        patterns = {
            'seasonal_patterns': self._analyze_seasonal_patterns(df_analysis),
            'weekly_patterns': self._analyze_weekly_patterns(df_analysis),
            'category_patterns': self._analyze_category_patterns(df_analysis),
            'trend_analysis': self._analyze_trends(df_analysis),
            'anomalies': self._detect_anomalies(df_analysis)
        }
        
        return patterns
    
    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze seasonal emission patterns"""
        if 'month' not in df.columns:
            return {}
        
        monthly_avg = df.groupby('month')['carbon_footprint'].agg(['mean', 'std']).round(2)
        
        return {
            'monthly_averages': monthly_avg.to_dict(),
            'highest_month': int(monthly_avg['mean'].idxmax()),
            'lowest_month': int(monthly_avg['mean'].idxmin()),
            'seasonal_variation': float(monthly_avg['mean'].std())
        }
    
    def _analyze_weekly_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze weekly emission patterns"""
        if 'day_of_week' not in df.columns:
            return {}
        
        daily_avg = df.groupby('day_of_week')['carbon_footprint'].mean()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'daily_averages': dict(zip(day_names, daily_avg.round(2))),
            'highest_day': day_names[daily_avg.idxmax()],
            'lowest_day': day_names[daily_avg.idxmin()],
            'weekend_vs_weekday': {
                'weekend_avg': float(df[df['is_weekend'] == 1]['carbon_footprint'].mean()),
                'weekday_avg': float(df[df['is_weekend'] == 0]['carbon_footprint'].mean())
            }
        }
    
    def _analyze_category_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze emission patterns by category"""
        if 'category' not in df.columns:
            return {}
        
        category_stats = df.groupby('category')['carbon_footprint'].agg(['sum', 'mean', 'count']).round(2)
        
        return {
            'category_totals': category_stats['sum'].to_dict(),
            'category_averages': category_stats['mean'].to_dict(),
            'category_frequency': category_stats['count'].to_dict(),
            'dominant_category': category_stats['sum'].idxmax()
        }
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze emission trends over time"""
        if len(df) < 7:
            return {'error': 'Insufficient data for trend analysis'}
        
        df_sorted = df.sort_values('date')
        
        # Calculate trend using linear regression
        X = np.arange(len(df_sorted)).reshape(-1, 1)
        y = df_sorted['carbon_footprint'].values
        
        trend_model = LinearRegression()
        trend_model.fit(X, y)
        
        slope = trend_model.coef_[0]
        trend_direction = 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
        
        return {
            'overall_trend': trend_direction,
            'trend_slope': float(slope),
            'recent_7d_avg': float(df_sorted['carbon_footprint'].tail(7).mean()),
            'recent_30d_avg': float(df_sorted['carbon_footprint'].tail(30).mean()),
            'improvement_rate': float(slope * -1)  # Negative slope = improvement
        }
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict:
        """Detect anomalous emission days"""
        if len(df) < 5:
            return {}
        
        mean_emission = df['carbon_footprint'].mean()
        std_emission = df['carbon_footprint'].std()
        threshold = mean_emission + 2 * std_emission
        
        anomalies = df[df['carbon_footprint'] > threshold]
        
        return {
            'anomaly_count': len(anomalies),
            'anomaly_threshold': float(threshold),
            'anomaly_dates': anomalies['date'].dt.strftime('%Y-%m-%d').tolist() if len(anomalies) > 0 else [],
            'anomaly_values': anomalies['carbon_footprint'].tolist() if len(anomalies) > 0 else []
        }
    
    def get_model_performance(self) -> Dict:
        """Get performance metrics of trained models"""
        performance = {}
        
        for model_name in self.models.keys():
            if self.is_trained[model_name]:
                performance[model_name] = {
                    'trained': True,
                    'feature_importance': self.feature_importance if model_name == 'forest' else None
                }
            else:
                performance[model_name] = {'trained': False}
        
        return performance 