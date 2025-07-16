"""
Data processing and cleaning module for AFL Scout AI platform.
Handles data standardization, cleaning, and preparation for analysis.
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AFLDataProcessor:
    """
    Comprehensive data processor for AFL scouting data
    """
    
    def __init__(self, db_path: str = "data/afl_data.db"):
        self.db_path = db_path
        self.team_mappings = self._get_team_mappings()
        self.position_mappings = self._get_position_mappings()
        
    def _get_team_mappings(self) -> Dict[str, str]:
        """
        Standard team name mappings for different data sources
        """
        return {
            # AFL Teams
            'Adelaide': 'Adelaide Crows',
            'Adelaide Crows': 'Adelaide Crows',
            'Crows': 'Adelaide Crows',
            'Brisbane': 'Brisbane Lions',
            'Brisbane Lions': 'Brisbane Lions',
            'Lions': 'Brisbane Lions',
            'Carlton': 'Carlton Blues',
            'Carlton Blues': 'Carlton Blues',
            'Blues': 'Carlton Blues',
            'Collingwood': 'Collingwood Magpies',
            'Collingwood Magpies': 'Collingwood Magpies',
            'Magpies': 'Collingwood Magpies',
            'Essendon': 'Essendon Bombers',
            'Essendon Bombers': 'Essendon Bombers',
            'Bombers': 'Essendon Bombers',
            'Fremantle': 'Fremantle Dockers',
            'Fremantle Dockers': 'Fremantle Dockers',
            'Dockers': 'Fremantle Dockers',
            'Geelong': 'Geelong Cats',
            'Geelong Cats': 'Geelong Cats',
            'Cats': 'Geelong Cats',
            'Gold Coast': 'Gold Coast Suns',
            'Gold Coast Suns': 'Gold Coast Suns',
            'Suns': 'Gold Coast Suns',
            'GWS': 'GWS Giants',
            'GWS Giants': 'GWS Giants',
            'Giants': 'GWS Giants',
            'Hawthorn': 'Hawthorn Hawks',
            'Hawthorn Hawks': 'Hawthorn Hawks',
            'Hawks': 'Hawthorn Hawks',
            'Melbourne': 'Melbourne Demons',
            'Melbourne Demons': 'Melbourne Demons',
            'Demons': 'Melbourne Demons',
            'North Melbourne': 'North Melbourne Kangaroos',
            'North Melbourne Kangaroos': 'North Melbourne Kangaroos',
            'Kangaroos': 'North Melbourne Kangaroos',
            'Port Adelaide': 'Port Adelaide Power',
            'Port Adelaide Power': 'Port Adelaide Power',
            'Power': 'Port Adelaide Power',
            'Richmond': 'Richmond Tigers',
            'Richmond Tigers': 'Richmond Tigers',
            'Tigers': 'Richmond Tigers',
            'St Kilda': 'St Kilda Saints',
            'St Kilda Saints': 'St Kilda Saints',
            'Saints': 'St Kilda Saints',
            'Sydney': 'Sydney Swans',
            'Sydney Swans': 'Sydney Swans',
            'Swans': 'Sydney Swans',
            'West Coast': 'West Coast Eagles',
            'West Coast Eagles': 'West Coast Eagles',
            'Eagles': 'West Coast Eagles',
            'Western Bulldogs': 'Western Bulldogs',
            'Bulldogs': 'Western Bulldogs',
        }
    
    def _get_position_mappings(self) -> Dict[str, str]:
        """
        Standard position mappings
        """
        return {
            'FB': 'Defender',
            'CHB': 'Defender',
            'BP': 'Defender',
            'HBF': 'Defender',
            'B': 'Defender',
            'DEF': 'Defender',
            'M': 'Midfielder',
            'MID': 'Midfielder',
            'C': 'Midfielder',
            'W': 'Midfielder',
            'HFF': 'Forward',
            'CHF': 'Forward',
            'FF': 'Forward',
            'FP': 'Forward',
            'F': 'Forward',
            'FWD': 'Forward',
            'R': 'Ruck',
            'RK': 'Ruck',
            'RUCK': 'Ruck',
        }
    
    def standardize_team_names(self, df: pd.DataFrame, team_column: str) -> pd.DataFrame:
        """
        Standardize team names across different data sources
        """
        df_copy = df.copy()
        
        if team_column in df_copy.columns:
            df_copy[team_column] = df_copy[team_column].map(
                lambda x: self.team_mappings.get(str(x).strip(), str(x).strip()) 
                if pd.notna(x) else x
            )
        
        return df_copy
    
    def standardize_positions(self, df: pd.DataFrame, position_column: str) -> pd.DataFrame:
        """
        Standardize player positions
        """
        df_copy = df.copy()
        
        if position_column in df_copy.columns:
            df_copy[position_column] = df_copy[position_column].map(
                lambda x: self.position_mappings.get(str(x).strip().upper(), str(x).strip()) 
                if pd.notna(x) else x
            )
        
        return df_copy
    
    def clean_numeric_columns(self, df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
        """
        Clean and convert numeric columns
        """
        df_copy = df.copy()
        
        for col in numeric_columns:
            if col in df_copy.columns:
                # Remove non-numeric characters except decimals
                df_copy[col] = df_copy[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
        
        return df_copy
    
    def add_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived AFL-specific metrics
        """
        df_copy = df.copy()
        
        # Disposal efficiency
        if 'Kicks' in df_copy.columns and 'Handballs' in df_copy.columns:
            df_copy['Total_Disposals'] = df_copy['Kicks'].fillna(0) + df_copy['Handballs'].fillna(0)
        
        # Mark to disposal ratio
        if 'Marks' in df_copy.columns and 'Total_Disposals' in df_copy.columns:
            df_copy['Mark_Disposal_Ratio'] = df_copy['Marks'] / (df_copy['Total_Disposals'] + 1)
        
        # Contested possession rate
        if 'Contested Possessions' in df_copy.columns and 'Total_Disposals' in df_copy.columns:
            df_copy['Contested_Rate'] = df_copy['Contested Possessions'] / (df_copy['Total_Disposals'] + 1)
        
        # Goal accuracy
        if 'Goals' in df_copy.columns and 'Behinds' in df_copy.columns:
            total_shots = df_copy['Goals'].fillna(0) + df_copy['Behinds'].fillna(0)
            df_copy['Goal_Accuracy'] = df_copy['Goals'] / (total_shots + 1)
        
        # Tackle efficiency (tackles per contested possession)
        if 'Tackles' in df_copy.columns and 'Contested Possessions' in df_copy.columns:
            df_copy['Tackle_Efficiency'] = df_copy['Tackles'] / (df_copy['Contested Possessions'] + 1)
        
        return df_copy
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in AFL data
        """
        df_copy = df.copy()
        
        # Numeric columns - fill with 0 for stats, median for physical attributes
        numeric_stat_cols = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Behinds', 
                           'Kicks', 'Handballs', 'Contested Possessions', 'Uncontested Possessions']
        
        physical_cols = ['Height', 'Weight', 'Age']
        
        for col in numeric_stat_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna(0)
        
        for col in physical_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna(df_copy[col].median())
        
        # Categorical columns - fill with 'Unknown'
        categorical_cols = ['Position', 'Team', 'League']
        for col in categorical_cols:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].fillna('Unknown')
        
        return df_copy
    
    def process_squiggle_data(self, games_df: pd.DataFrame, ladder_df: pd.DataFrame, 
                            tips_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Process Squiggle API data
        """
        processed_data = {}
        
        # Process games
        if not games_df.empty:
            games_clean = games_df.copy()
            games_clean = self.standardize_team_names(games_clean, 'hteam')
            games_clean = self.standardize_team_names(games_clean, 'ateam')
            
            # Convert date
            if 'date' in games_clean.columns:
                games_clean['date'] = pd.to_datetime(games_clean['date'], errors='coerce')
            
            # Clean numeric columns
            numeric_cols = ['hscore', 'ascore', 'round']
            games_clean = self.clean_numeric_columns(games_clean, numeric_cols)
            
            processed_data['games'] = games_clean
        
        # Process ladder
        if not ladder_df.empty:
            ladder_clean = ladder_df.copy()
            ladder_clean = self.standardize_team_names(ladder_clean, 'name')
            
            numeric_cols = ['wins', 'losses', 'draws', 'points', 'percentage']
            ladder_clean = self.clean_numeric_columns(ladder_clean, numeric_cols)
            
            processed_data['ladder'] = ladder_clean
        
        # Process tips
        if not tips_df.empty:
            tips_clean = tips_df.copy()
            tips_clean = self.standardize_team_names(tips_clean, 'hteam')
            tips_clean = self.standardize_team_names(tips_clean, 'ateam')
            
            numeric_cols = ['hconfidence', 'aconfidence', 'margin']
            tips_clean = self.clean_numeric_columns(tips_clean, numeric_cols)
            
            processed_data['tips'] = tips_clean
        
        return processed_data
    
    def process_footywire_data(self, player_df: pd.DataFrame, team_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Process FootyWire data
        """
        processed_data = {}
        
        # Process player data
        if not player_df.empty:
            player_clean = player_df.copy()
            
            # Standardize team names
            if 'Team' in player_clean.columns:
                player_clean = self.standardize_team_names(player_clean, 'Team')
            
            # Standardize positions
            if 'Position' in player_clean.columns:
                player_clean = self.standardize_positions(player_clean, 'Position')
            
            # Clean numeric columns
            numeric_cols = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Behinds', 
                          'Kicks', 'Handballs', 'Contested Possessions', 'Uncontested Possessions',
                          'Age', 'Height', 'Weight']
            
            player_clean = self.clean_numeric_columns(player_clean, numeric_cols)
            
            # Add derived metrics
            player_clean = self.add_derived_metrics(player_clean)
            
            # Handle missing values
            player_clean = self.handle_missing_values(player_clean)
            
            processed_data['players'] = player_clean
        
        # Process team data
        if not team_df.empty:
            team_clean = team_df.copy()
            
            if 'Team' in team_clean.columns:
                team_clean = self.standardize_team_names(team_clean, 'Team')
            
            # Clean all numeric columns (assume all non-Team columns are numeric)
            numeric_cols = [col for col in team_clean.columns if col != 'Team']
            team_clean = self.clean_numeric_columns(team_clean, numeric_cols)
            
            processed_data['teams'] = team_clean
        
        return processed_data
    
    def save_to_database(self, processed_data: Dict[str, pd.DataFrame]) -> None:
        """
        Save processed data to SQLite database
        """
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            for table_name, df in processed_data.items():
                if not df.empty:
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Saved {len(df)} records to {table_name} table")
    
    def load_from_database(self, table_name: str) -> pd.DataFrame:
        """
        Load data from SQLite database
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                return df
        except Exception as e:
            logger.error(f"Error loading {table_name}: {e}")
            return pd.DataFrame()
    
    def get_player_summary_stats(self) -> pd.DataFrame:
        """
        Get summary statistics for all players
        """
        players_df = self.load_from_database('players')
        
        if players_df.empty:
            return pd.DataFrame()
        
        # Calculate per-game averages if games played is available
        stat_cols = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Behinds']
        
        summary_stats = players_df.groupby(['Player', 'Team', 'Position']).agg({
            **{col: ['mean', 'sum', 'count'] for col in stat_cols if col in players_df.columns},
            'Age': 'first'
        }).round(2)
        
        # Flatten column names
        summary_stats.columns = ['_'.join(col).strip() for col in summary_stats.columns]
        summary_stats = summary_stats.reset_index()
        
        return summary_stats

def main():
    """
    Main function to demonstrate data processing
    """
    processor = AFLDataProcessor()
    
    # Example: Load and process sample data
    logger.info("Data processor initialized")
    
    # You would typically load your scraped data here
    # processed_data = processor.process_squiggle_data(games_df, ladder_df, tips_df)
    # processor.save_to_database(processed_data)

if __name__ == "__main__":
    main()