"""
Enhanced ML Models for AFL Scouting Analytics
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import pickle
import os

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report
from sklearn.cluster import KMeans
import xgboost as xgb

from ..database import db_manager
from ..config import config

logger = logging.getLogger(__name__)

class PlayerEvaluationModel:
    """Advanced player evaluation and potential prediction model"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.is_trained = False
        
    def prepare_features(self, performance_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for player evaluation"""
        # Calculate rolling averages
        performance_data = performance_data.sort_values(['player_id', 'year', 'games_played'])
        
        # Key performance indicators
        features = []
        
        for player_id in performance_data['player_id'].unique():
            player_data = performance_data[performance_data['player_id'] == player_id].copy()
            
            # Career progression features
            player_data['career_games'] = range(1, len(player_data) + 1)
            player_data['seasons_played'] = player_data['year'] - player_data['year'].min() + 1
            
            # Rolling averages (last 10 games)
            rolling_cols = ['kicks', 'marks', 'handballs', 'disposals', 'goals', 'tackles', 
                           'inside_50s', 'clearances', 'contested_possessions']
            
            for col in rolling_cols:
                if col in player_data.columns:
                    player_data[f'{col}_avg_10'] = player_data[col].rolling(window=10, min_periods=1).mean()
                    player_data[f'{col}_trend'] = player_data[col].rolling(window=5, min_periods=1).apply(
                        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
                    )
            
            # Efficiency metrics
            if 'disposals' in player_data.columns and 'clangers' in player_data.columns:
                player_data['disposal_efficiency'] = (player_data['disposals'] - player_data['clangers']) / (player_data['disposals'] + 1)
            
            if 'goals' in player_data.columns and 'behinds' in player_data.columns:
                player_data['goal_accuracy'] = player_data['goals'] / (player_data['goals'] + player_data['behinds'] + 1)
            
            # Impact metrics
            if 'brownlow_votes' in player_data.columns:
                player_data['brownlow_rate'] = player_data['brownlow_votes'] / (player_data['career_games'] + 1)
            
            features.append(player_data)
        
        return pd.concat(features, ignore_index=True)
    
    def train_player_value_model(self, force_retrain: bool = False):
        """Train model to predict player market value/impact"""
        try:
            # Load performance data
            with db_manager.get_session() as session:
                query = """
                SELECT pp.*, p.height, p.weight, 
                       EXTRACT(YEAR FROM AGE(p.born_date)) as age
                FROM player_performance pp
                JOIN players p ON pp.player_id = p.id
                WHERE pp.year >= 2015
                """
                
                data = pd.read_sql(query, session.bind)
            
            if len(data) < 1000:
                logger.warning("Insufficient data for training. Need at least 1000 records.")
                return False
            
            # Prepare features
            features_df = self.prepare_features(data)
            
            # Define target variable (player impact score)
            # Weighted combination of key stats
            features_df['impact_score'] = (
                features_df['disposals'].fillna(0) * 0.3 +
                features_df['goals'].fillna(0) * 2.0 +
                features_df['tackles'].fillna(0) * 0.8 +
                features_df['inside_50s'].fillna(0) * 0.5 +
                features_df['brownlow_votes'].fillna(0) * 5.0
            )
            
            # Select features for training
            feature_cols = [
                'career_games', 'seasons_played', 'age', 'height', 'weight',
                'kicks_avg_10', 'marks_avg_10', 'handballs_avg_10', 'disposals_avg_10',
                'goals_avg_10', 'tackles_avg_10', 'inside_50s_avg_10', 'clearances_avg_10',
                'disposal_efficiency', 'goal_accuracy', 'brownlow_rate',
                'kicks_trend', 'disposals_trend', 'goals_trend'
            ]
            
            # Filter available columns
            feature_cols = [col for col in feature_cols if col in features_df.columns]
            self.feature_columns = feature_cols
            
            X = features_df[feature_cols].fillna(0)
            y = features_df['impact_score'].fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            self.scalers['player_value'] = StandardScaler()
            X_train_scaled = self.scalers['player_value'].fit_transform(X_train)
            X_test_scaled = self.scalers['player_value'].transform(X_test)
            
            # Train Random Forest model
            self.models['player_value'] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.models['player_value'].fit(X_train_scaled, y_train)
            
            # Evaluate model
            predictions = self.models['player_value'].predict(X_test_scaled)
            mae = mean_absolute_error(y_test, predictions)
            
            logger.info(f"Player value model trained. MAE: {mae:.2f}")
            self.is_trained = True
            
            # Save model
            self._save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training player value model: {e}")
            return False
    
    def predict_player_potential(self, player_id: int, projection_years: int = 3) -> Dict[str, Any]:
        """Predict player potential and career trajectory"""
        try:
            if not self.is_trained:
                self._load_models()
            
            # Get player data
            with db_manager.get_session() as session:
                query = """
                SELECT pp.*, p.height, p.weight, p.born_date,
                       EXTRACT(YEAR FROM AGE(p.born_date)) as age
                FROM player_performance pp
                JOIN players p ON pp.player_id = p.id
                WHERE pp.player_id = :player_id
                ORDER BY pp.year, pp.games_played
                """
                
                player_data = pd.read_sql(query, session.bind, params={'player_id': player_id})
            
            if len(player_data) == 0:
                return {"error": "No data found for player"}
            
            # Prepare features
            features_df = self.prepare_features(player_data)
            recent_form = features_df.tail(1)
            
            if len(recent_form) == 0:
                return {"error": "Unable to prepare features"}
            
            # Current impact score
            X_current = recent_form[self.feature_columns].fillna(0)
            X_current_scaled = self.scalers['player_value'].transform(X_current)
            current_impact = self.models['player_value'].predict(X_current_scaled)[0]
            
            # Project future performance
            projections = []
            current_age = recent_form['age'].iloc[0]
            current_games = recent_form['career_games'].iloc[0]
            
            for year in range(1, projection_years + 1):
                # Age progression
                projected_age = current_age + year
                projected_games = current_games + (22 * year)  # Assume 22 games per year
                
                # Create projection features
                proj_features = X_current.copy()
                proj_features['age'] = projected_age
                proj_features['career_games'] = projected_games
                proj_features['seasons_played'] = recent_form['seasons_played'].iloc[0] + year
                
                # Apply age-based performance decline/improvement
                age_factor = self._calculate_age_factor(projected_age)
                trend_cols = [col for col in proj_features.columns if 'trend' in col]
                for col in trend_cols:
                    proj_features[col] *= age_factor
                
                proj_scaled = self.scalers['player_value'].transform(proj_features)
                projected_impact = self.models['player_value'].predict(proj_scaled)[0]
                
                projections.append({
                    'year': year,
                    'age': projected_age,
                    'projected_impact': projected_impact,
                    'career_games': projected_games
                })
            
            return {
                'player_id': player_id,
                'current_impact_score': current_impact,
                'current_age': current_age,
                'career_stage': self._determine_career_stage(current_age),
                'projections': projections,
                'peak_projection': max(projections, key=lambda x: x['projected_impact']),
                'injury_risk': self._assess_injury_risk(player_data),
                'development_areas': self._identify_development_areas(features_df)
            }
            
        except Exception as e:
            logger.error(f"Error predicting player potential: {e}")
            return {"error": str(e)}
    
    def _calculate_age_factor(self, age: float) -> float:
        """Calculate age-based performance factor"""
        if age < 20:
            return 1.1  # Young players improving
        elif age < 25:
            return 1.05  # Prime development years
        elif age < 30:
            return 1.0   # Peak years
        elif age < 33:
            return 0.95  # Slight decline
        else:
            return 0.9   # Veteran years
    
    def _determine_career_stage(self, age: float) -> str:
        """Determine career stage based on age"""
        if age < 22:
            return "Developing"
        elif age < 26:
            return "Emerging"
        elif age < 30:
            return "Peak"
        elif age < 33:
            return "Experienced"
        else:
            return "Veteran"
    
    def _assess_injury_risk(self, player_data: pd.DataFrame) -> str:
        """Assess injury risk based on games played pattern"""
        recent_seasons = player_data['year'].unique()[-3:] if len(player_data['year'].unique()) >= 3 else player_data['year'].unique()
        
        games_per_season = []
        for season in recent_seasons:
            season_games = len(player_data[player_data['year'] == season])
            games_per_season.append(season_games)
        
        avg_games = np.mean(games_per_season)
        
        if avg_games >= 20:
            return "Low"
        elif avg_games >= 15:
            return "Moderate"
        else:
            return "High"
    
    def _identify_development_areas(self, features_df: pd.DataFrame) -> List[str]:
        """Identify areas for player development"""
        recent_form = features_df.tail(10)
        areas = []
        
        # Check goal accuracy
        if 'goal_accuracy' in recent_form.columns:
            avg_accuracy = recent_form['goal_accuracy'].mean()
            if avg_accuracy < 0.6:
                areas.append("Goal Accuracy")
        
        # Check disposal efficiency
        if 'disposal_efficiency' in recent_form.columns:
            avg_efficiency = recent_form['disposal_efficiency'].mean()
            if avg_efficiency < 0.7:
                areas.append("Disposal Efficiency")
        
        # Check contested possession rate
        if 'contested_possessions' in recent_form.columns and 'disposals' in recent_form.columns:
            contested_rate = recent_form['contested_possessions'].sum() / recent_form['disposals'].sum()
            if contested_rate < 0.4:
                areas.append("Contested Ball Winning")
        
        return areas
    
    def _save_models(self):
        """Save trained models and scalers"""
        try:
            model_dir = "models"
            os.makedirs(model_dir, exist_ok=True)
            
            # Save models
            for name, model in self.models.items():
                with open(f"{model_dir}/{name}_model.pkl", 'wb') as f:
                    pickle.dump(model, f)
            
            # Save scalers
            for name, scaler in self.scalers.items():
                with open(f"{model_dir}/{name}_scaler.pkl", 'wb') as f:
                    pickle.dump(scaler, f)
            
            # Save feature columns
            with open(f"{model_dir}/feature_columns.pkl", 'wb') as f:
                pickle.dump(self.feature_columns, f)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self):
        """Load trained models and scalers"""
        try:
            model_dir = "models"
            
            # Load models
            for model_file in os.listdir(model_dir):
                if model_file.endswith('_model.pkl'):
                    model_name = model_file.replace('_model.pkl', '')
                    with open(f"{model_dir}/{model_file}", 'rb') as f:
                        self.models[model_name] = pickle.load(f)
            
            # Load scalers
            for scaler_file in os.listdir(model_dir):
                if scaler_file.endswith('_scaler.pkl'):
                    scaler_name = scaler_file.replace('_scaler.pkl', '')
                    with open(f"{model_dir}/{scaler_file}", 'rb') as f:
                        self.scalers[scaler_name] = pickle.load(f)
            
            # Load feature columns
            if os.path.exists(f"{model_dir}/feature_columns.pkl"):
                with open(f"{model_dir}/feature_columns.pkl", 'rb') as f:
                    self.feature_columns = pickle.load(f)
            
            self.is_trained = True
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.is_trained = False

class TeamAnalysisModel:
    """Model for team performance analysis and prediction"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        
    def analyze_team_performance(self, team_name: str, season: int = None) -> Dict[str, Any]:
        """Comprehensive team performance analysis"""
        try:
            with db_manager.get_session() as session:
                # Get team match data
                season_filter = f"AND year = {season}" if season else "AND year >= 2020"
                
                query = f"""
                SELECT * FROM matches 
                WHERE (team_1_name = :team_name OR team_2_name = :team_name)
                {season_filter}
                ORDER BY date
                """
                
                matches = pd.read_sql(query, session.bind, params={'team_name': team_name})
            
            if len(matches) == 0:
                return {"error": "No match data found for team"}
            
            # Calculate team statistics
            team_stats = self._calculate_team_stats(matches, team_name)
            
            # Analyze recent form
            recent_matches = matches.tail(10)
            recent_form = self._analyze_recent_form(recent_matches, team_name)
            
            # Identify strengths and weaknesses
            strengths_weaknesses = self._identify_team_patterns(matches, team_name)
            
            # Calculate expected performance
            expected_performance = self._calculate_expected_performance(team_stats)
            
            return {
                'team_name': team_name,
                'season': season,
                'overall_stats': team_stats,
                'recent_form': recent_form,
                'strengths_weaknesses': strengths_weaknesses,
                'expected_performance': expected_performance,
                'recommendation': self._generate_team_recommendation(team_stats, recent_form)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team performance: {e}")
            return {"error": str(e)}
    
    def _calculate_team_stats(self, matches: pd.DataFrame, team_name: str) -> Dict[str, float]:
        """Calculate comprehensive team statistics"""
        stats = {
            'total_matches': len(matches),
            'wins': 0,
            'losses': 0,
            'avg_score_for': 0,
            'avg_score_against': 0,
            'avg_q1_score': 0,
            'avg_q2_score': 0,
            'avg_q3_score': 0,
            'avg_final_score': 0
        }
        
        team_scores = []
        opponent_scores = []
        q1_scores = []
        q2_scores = []
        q3_scores = []
        
        for _, match in matches.iterrows():
            if match['team_1_name'] == team_name:
                team_final = match['team_1_final_goals'] * 6 + match['team_1_final_behinds']
                opp_final = match['team_2_final_goals'] * 6 + match['team_2_final_behinds']
                
                q1_scores.append(match['team_1_q1_goals'] * 6 + match['team_1_q1_behinds'])
                q2_scores.append(match['team_1_q2_goals'] * 6 + match['team_1_q2_behinds'])
                q3_scores.append(match['team_1_q3_goals'] * 6 + match['team_1_q3_behinds'])
                
            else:
                team_final = match['team_2_final_goals'] * 6 + match['team_2_final_behinds']
                opp_final = match['team_1_final_goals'] * 6 + match['team_1_final_behinds']
                
                q1_scores.append(match['team_2_q1_goals'] * 6 + match['team_2_q1_behinds'])
                q2_scores.append(match['team_2_q2_goals'] * 6 + match['team_2_q2_behinds'])
                q3_scores.append(match['team_2_q3_goals'] * 6 + match['team_2_q3_behinds'])
            
            team_scores.append(team_final)
            opponent_scores.append(opp_final)
            
            if team_final > opp_final:
                stats['wins'] += 1
            else:
                stats['losses'] += 1
        
        stats['win_percentage'] = (stats['wins'] / stats['total_matches']) * 100
        stats['avg_score_for'] = np.mean(team_scores)
        stats['avg_score_against'] = np.mean(opponent_scores)
        stats['avg_margin'] = stats['avg_score_for'] - stats['avg_score_against']
        stats['avg_q1_score'] = np.mean(q1_scores)
        stats['avg_q2_score'] = np.mean(q2_scores)
        stats['avg_q3_score'] = np.mean(q3_scores)
        
        return stats
    
    def _analyze_recent_form(self, recent_matches: pd.DataFrame, team_name: str) -> Dict[str, Any]:
        """Analyze recent form"""
        recent_stats = self._calculate_team_stats(recent_matches, team_name)
        
        # Calculate form trend
        scores = []
        for _, match in recent_matches.iterrows():
            if match['team_1_name'] == team_name:
                score = match['team_1_final_goals'] * 6 + match['team_1_final_behinds']
            else:
                score = match['team_2_final_goals'] * 6 + match['team_2_final_behinds']
            scores.append(score)
        
        if len(scores) > 1:
            trend = np.polyfit(range(len(scores)), scores, 1)[0]
            form_trend = "Improving" if trend > 0 else "Declining" if trend < 0 else "Stable"
        else:
            form_trend = "Insufficient data"
        
        return {
            'recent_record': f"{recent_stats['wins']}-{recent_stats['losses']}",
            'recent_win_percentage': recent_stats['win_percentage'],
            'recent_avg_score': recent_stats['avg_score_for'],
            'form_trend': form_trend,
            'consistency': np.std(scores) if scores else 0
        }
    
    def _identify_team_patterns(self, matches: pd.DataFrame, team_name: str) -> Dict[str, List[str]]:
        """Identify team strengths and weaknesses"""
        strengths = []
        weaknesses = []
        
        team_stats = self._calculate_team_stats(matches, team_name)
        
        # Analyze scoring patterns
        if team_stats['avg_score_for'] > 100:
            strengths.append("High-scoring offense")
        elif team_stats['avg_score_for'] < 80:
            weaknesses.append("Low-scoring offense")
        
        # Analyze defensive patterns
        if team_stats['avg_score_against'] < 80:
            strengths.append("Strong defense")
        elif team_stats['avg_score_against'] > 100:
            weaknesses.append("Weak defense")
        
        # Analyze quarter-by-quarter performance
        quarters = ['q1', 'q2', 'q3']
        quarter_scores = [team_stats[f'avg_{q}_score'] for q in quarters]
        best_quarter = quarters[np.argmax(quarter_scores)]
        worst_quarter = quarters[np.argmin(quarter_scores)]
        
        strengths.append(f"Strong {best_quarter.upper()} performance")
        if min(quarter_scores) < max(quarter_scores) * 0.8:
            weaknesses.append(f"Weak {worst_quarter.upper()} performance")
        
        return {'strengths': strengths, 'weaknesses': weaknesses}
    
    def _calculate_expected_performance(self, team_stats: Dict[str, float]) -> Dict[str, float]:
        """Calculate expected performance metrics"""
        # Simple expected win percentage based on scoring differential
        margin = team_stats['avg_margin']
        expected_win_pct = 50 + (margin * 2.5)  # Rule of thumb: 1 point margin = 2.5% win probability
        expected_win_pct = max(0, min(100, expected_win_pct))
        
        return {
            'expected_win_percentage': expected_win_pct,
            'expected_wins_remaining': expected_win_pct / 100 * (22 - team_stats['total_matches']),
            'finals_probability': max(0, min(100, expected_win_pct - 30))  # Rough estimate
        }
    
    def _generate_team_recommendation(self, team_stats: Dict, recent_form: Dict) -> str:
        """Generate team strategy recommendation"""
        recommendations = []
        
        if team_stats['win_percentage'] > 70:
            recommendations.append("Strong premiership contender - focus on maintaining form")
        elif team_stats['win_percentage'] > 55:
            recommendations.append("Finals chance - consistency key to success")
        elif team_stats['win_percentage'] > 40:
            recommendations.append("Mid-table - focus on development and improvement")
        else:
            recommendations.append("Rebuilding phase - focus on youth development")
        
        if recent_form['form_trend'] == "Improving":
            recommendations.append("Positive momentum - maintain current strategies")
        elif recent_form['form_trend'] == "Declining":
            recommendations.append("Address recent form slump - tactical adjustments needed")
        
        return "; ".join(recommendations)

# Global model instances
player_model = PlayerEvaluationModel()
team_model = TeamAnalysisModel()