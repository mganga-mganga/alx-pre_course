"""
Machine Learning models for AFL player analysis and scouting insights.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, accuracy_score, silhouette_score
import joblib
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AFLPlayerAnalyzer:
    """
    Machine learning analyzer for AFL player performance and potential
    """
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        self.performance_model = None
        self.potential_model = None
        self.injury_model = None
        self.team_fit_model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # AFL-specific feature definitions
        self.key_features = [
            'Disposals', 'Marks', 'Tackles', 'Goals', 'Behinds',
            'Kicks', 'Handballs', 'Contested Possessions', 'Uncontested Possessions',
            'Mark_Disposal_Ratio', 'Contested_Rate', 'Goal_Accuracy', 'Tackle_Efficiency'
        ]
        
        self.physical_features = ['Age', 'Height', 'Weight']
        
    def prepare_features(self, df: pd.DataFrame, target_col: str = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features for machine learning
        """
        # Select available features
        available_features = [col for col in self.key_features + self.physical_features 
                            if col in df.columns]
        
        if not available_features:
            raise ValueError("No suitable features found in DataFrame")
        
        X = df[available_features].fillna(0)
        
        y = None
        if target_col and target_col in df.columns:
            y = df[target_col].fillna(0)
        
        return X.values, y.values if y is not None else None
    
    def train_performance_model(self, df: pd.DataFrame, target_metric: str = 'Disposals') -> Dict:
        """
        Train a model to predict player performance metrics
        """
        logger.info(f"Training performance model for {target_metric}")
        
        try:
            X, y = self.prepare_features(df, target_metric)
            
            if len(X) < 10:
                logger.warning("Insufficient data for training")
                return {"error": "Insufficient data"}
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train Random Forest model
            self.performance_model = RandomForestRegressor(
                n_estimators=100, 
                random_state=42,
                max_depth=10
            )
            
            self.performance_model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.performance_model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(self.performance_model, X_scaled, y, cv=5)
            
            # Feature importance
            feature_names = [col for col in self.key_features + self.physical_features 
                           if col in df.columns]
            feature_importance = dict(zip(feature_names, self.performance_model.feature_importances_))
            
            # Save model
            self._save_model(self.performance_model, 'performance_model.pkl')
            self._save_model(self.scaler, 'scaler.pkl')
            
            results = {
                "mse": mse,
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "feature_importance": feature_importance,
                "model_saved": True
            }
            
            logger.info(f"Performance model trained successfully. MSE: {mse:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error training performance model: {e}")
            return {"error": str(e)}
    
    def predict_player_potential(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict player potential based on age and current performance
        """
        if self.performance_model is None:
            logger.error("Performance model not trained")
            return df
        
        try:
            X, _ = self.prepare_features(df)
            X_scaled = self.scaler.transform(X)
            
            # Predict current performance level
            current_performance = self.performance_model.predict(X_scaled)
            
            # Calculate potential based on age curve
            ages = df['Age'].fillna(25)
            
            # AFL peak age is typically 26-28
            age_factor = np.where(ages < 26, 1.2 - 0.02 * (26 - ages), 
                                1.0 - 0.03 * (ages - 26))
            
            predicted_potential = current_performance * age_factor
            
            df_result = df.copy()
            df_result['Predicted_Performance'] = current_performance
            df_result['Potential_Rating'] = predicted_potential
            df_result['Development_Factor'] = age_factor
            
            return df_result
            
        except Exception as e:
            logger.error(f"Error predicting potential: {e}")
            return df
    
    def cluster_players_by_style(self, df: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
        """
        Cluster players by playing style for team fit analysis
        """
        logger.info(f"Clustering players into {n_clusters} playing styles")
        
        try:
            # Use ratio metrics for clustering
            cluster_features = [
                'Mark_Disposal_Ratio', 'Contested_Rate', 'Goal_Accuracy', 
                'Tackle_Efficiency'
            ]
            
            available_features = [col for col in cluster_features if col in df.columns]
            
            if len(available_features) < 2:
                logger.warning("Insufficient features for clustering")
                return df
            
            X = df[available_features].fillna(0)
            X_scaled = StandardScaler().fit_transform(X)
            
            # K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Calculate silhouette score
            sil_score = silhouette_score(X_scaled, clusters)
            logger.info(f"Clustering silhouette score: {sil_score:.3f}")
            
            # Add cluster labels
            df_result = df.copy()
            df_result['Playing_Style_Cluster'] = clusters
            
            # Assign style names based on cluster characteristics
            cluster_centers = kmeans.cluster_centers_
            style_names = self._assign_style_names(cluster_centers, available_features)
            
            df_result['Playing_Style'] = df_result['Playing_Style_Cluster'].map(style_names)
            
            return df_result
            
        except Exception as e:
            logger.error(f"Error clustering players: {e}")
            return df
    
    def _assign_style_names(self, centers: np.ndarray, features: List[str]) -> Dict[int, str]:
        """
        Assign descriptive names to player style clusters
        """
        style_names = {}
        
        for i, center in enumerate(centers):
            # Analyze cluster characteristics
            if 'Mark_Disposal_Ratio' in features:
                mark_idx = features.index('Mark_Disposal_Ratio')
                if center[mark_idx] > 0.5:
                    if 'Goal_Accuracy' in features:
                        goal_idx = features.index('Goal_Accuracy')
                        if center[goal_idx] > 0.5:
                            style_names[i] = "Key Forward"
                        else:
                            style_names[i] = "Marking Defender"
                    else:
                        style_names[i] = "Strong Marker"
                elif 'Contested_Rate' in features:
                    cont_idx = features.index('Contested_Rate')
                    if center[cont_idx] > 0.4:
                        style_names[i] = "Inside Midfielder"
                    else:
                        style_names[i] = "Outside Runner"
                else:
                    style_names[i] = f"Style_{i+1}"
            else:
                style_names[i] = f"Style_{i+1}"
        
        return style_names
    
    def evaluate_team_fit(self, player_df: pd.DataFrame, team_style: str) -> pd.DataFrame:
        """
        Evaluate how well players fit a team's playing style
        """
        team_requirements = {
            "possession_based": {
                "Uncontested Possessions": 0.3,
                "Mark_Disposal_Ratio": 0.2,
                "Contested_Rate": -0.1
            },
            "pressure_based": {
                "Tackles": 0.4,
                "Contested Possessions": 0.3,
                "Tackle_Efficiency": 0.3
            },
            "attacking": {
                "Goals": 0.4,
                "Goal_Accuracy": 0.3,
                "Forward_Pressure": 0.3
            },
            "defensive": {
                "Tackles": 0.3,
                "Contested_Rate": 0.3,
                "Mark_Disposal_Ratio": 0.2
            }
        }
        
        if team_style not in team_requirements:
            logger.warning(f"Unknown team style: {team_style}")
            return player_df
        
        requirements = team_requirements[team_style]
        df_result = player_df.copy()
        
        # Calculate fit score
        fit_scores = []
        for _, player in player_df.iterrows():
            score = 0
            for stat, weight in requirements.items():
                if stat in player_df.columns:
                    # Normalize stat value (0-1 scale)
                    stat_value = player[stat] if pd.notna(player[stat]) else 0
                    max_value = player_df[stat].max() if player_df[stat].max() > 0 else 1
                    normalized_value = stat_value / max_value
                    score += weight * normalized_value
            
            fit_scores.append(max(0, score))  # Ensure non-negative
        
        df_result[f'{team_style}_fit_score'] = fit_scores
        df_result = df_result.sort_values(f'{team_style}_fit_score', ascending=False)
        
        return df_result
    
    def _save_model(self, model, filename: str) -> None:
        """
        Save trained model to disk
        """
        try:
            model_path = self.models_dir / filename
            joblib.dump(model, model_path)
            logger.info(f"Model saved to {model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self, filename: str):
        """
        Load trained model from disk
        """
        try:
            model_path = self.models_dir / filename
            if model_path.exists():
                model = joblib.load(model_path)
                logger.info(f"Model loaded from {model_path}")
                return model
            else:
                logger.warning(f"Model file not found: {model_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def get_player_rankings(self, df: pd.DataFrame, position: str = None, 
                          metric: str = 'Disposals', top_n: int = 20) -> pd.DataFrame:
        """
        Get top player rankings by position and metric
        """
        df_filtered = df.copy()
        
        # Filter by position if specified
        if position and 'Position' in df.columns:
            df_filtered = df_filtered[df_filtered['Position'] == position]
        
        # Sort by metric
        if metric in df_filtered.columns:
            df_filtered = df_filtered.sort_values(metric, ascending=False)
        
        # Return top N
        return df_filtered.head(top_n)

def main():
    """
    Main function to demonstrate ML analysis
    """
    analyzer = AFLPlayerAnalyzer()
    logger.info("AFL Player Analyzer initialized")
    
    # Example usage would go here with actual data

if __name__ == "__main__":
    main()