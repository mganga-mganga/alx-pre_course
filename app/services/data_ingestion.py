"""
Enhanced data ingestion service for AFL dataset
"""
import logging
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from pathlib import Path

from ..database import db_manager
from ..config import config

logger = logging.getLogger(__name__)

class AFLDataIngestionService:
    """Enhanced service for ingesting AFL data from the comprehensive dataset"""
    
    def __init__(self):
        self.data_path = Path(config.data_source_path)
        self.players_path = self.data_path / "data" / "players"
        self.matches_path = self.data_path / "data" / "matches"
        self.lineups_path = self.data_path / "data" / "lineups"
        
    def ingest_all_data(self, force_reload: bool = False):
        """Ingest all AFL data into the database"""
        logger.info("Starting comprehensive AFL data ingestion...")
        
        try:
            # Create database tables if they don't exist
            db_manager.create_tables()
            
            # Ingest data in order
            self.ingest_teams_data()
            self.ingest_players_data(force_reload)
            self.ingest_matches_data(force_reload)
            
            logger.info("Data ingestion completed successfully")
            
        except Exception as e:
            logger.error(f"Error during data ingestion: {e}")
            raise
    
    def ingest_teams_data(self):
        """Ingest teams data with AFL, AFLW, VFL, SANFL classifications"""
        logger.info("Ingesting teams data...")
        
        # Define AFL teams with league classifications
        teams_data = [
            # AFL Men's teams
            {"name": "Adelaide", "short_name": "ADE", "league": "AFLM", "founded_year": 1991, "colors": "Navy Blue, Red, Gold", "is_active": True},
            {"name": "Brisbane Lions", "short_name": "BL", "league": "AFLM", "founded_year": 1996, "colors": "Maroon, Blue, Gold", "is_active": True},
            {"name": "Carlton", "short_name": "CAR", "league": "AFLM", "founded_year": 1864, "colors": "Navy Blue, White", "is_active": True},
            {"name": "Collingwood", "short_name": "COL", "league": "AFLM", "founded_year": 1892, "colors": "Black, White", "is_active": True},
            {"name": "Essendon", "short_name": "ESS", "league": "AFLM", "founded_year": 1872, "colors": "Red, Black", "is_active": True},
            {"name": "Fremantle", "short_name": "FRE", "league": "AFLM", "founded_year": 1994, "colors": "Purple, White, Green", "is_active": True},
            {"name": "Geelong", "short_name": "GEE", "league": "AFLM", "founded_year": 1859, "colors": "Navy Blue, White", "is_active": True},
            {"name": "Gold Coast", "short_name": "GCS", "league": "AFLM", "founded_year": 2009, "colors": "Red, Gold, Blue", "is_active": True},
            {"name": "Greater Western Sydney", "short_name": "GWS", "league": "AFLM", "founded_year": 2009, "colors": "Orange, Charcoal, White", "is_active": True},
            {"name": "Hawthorn", "short_name": "HAW", "league": "AFLM", "founded_year": 1902, "colors": "Brown, Gold", "is_active": True},
            {"name": "Melbourne", "short_name": "MEL", "league": "AFLM", "founded_year": 1858, "colors": "Red, Blue", "is_active": True},
            {"name": "North Melbourne", "short_name": "NM", "league": "AFLM", "founded_year": 1869, "colors": "Blue, White", "is_active": True},
            {"name": "Port Adelaide", "short_name": "PA", "league": "AFLM", "founded_year": 1870, "colors": "Black, White, Teal", "is_active": True},
            {"name": "Richmond", "short_name": "RIC", "league": "AFLM", "founded_year": 1885, "colors": "Black, Yellow", "is_active": True},
            {"name": "St Kilda", "short_name": "STK", "league": "AFLM", "founded_year": 1873, "colors": "Red, Black, White", "is_active": True},
            {"name": "Sydney", "short_name": "SYD", "league": "AFLM", "founded_year": 1874, "colors": "Red, White", "is_active": True},
            {"name": "West Coast", "short_name": "WCE", "league": "AFLM", "founded_year": 1986, "colors": "Royal Blue, Gold", "is_active": True},
            {"name": "Western Bulldogs", "short_name": "WB", "league": "AFLM", "founded_year": 1877, "colors": "Red, White, Blue", "is_active": True},
            
            # Historical teams
            {"name": "Fitzroy", "short_name": "FIT", "league": "AFLM", "founded_year": 1883, "colors": "Maroon, Blue, Gold", "is_active": False},
            {"name": "South Melbourne", "short_name": "SM", "league": "AFLM", "founded_year": 1874, "colors": "Red, White", "is_active": False},
            {"name": "Brisbane Bears", "short_name": "BB", "league": "AFLM", "founded_year": 1987, "colors": "Maroon, Gold", "is_active": False},
            {"name": "Footscray", "short_name": "FOO", "league": "AFLM", "founded_year": 1877, "colors": "Red, White, Blue", "is_active": False},
            {"name": "Kangaroos", "short_name": "KAN", "league": "AFLM", "founded_year": 1869, "colors": "Blue, White", "is_active": False},
        ]
        
        # Add AFLW teams (many same as AFL but separate classification)
        for team in teams_data:
            if team["is_active"]:
                aflw_team = team.copy()
                aflw_team["league"] = "AFLW"
                teams_data.append(aflw_team)
        
        teams_df = pd.DataFrame(teams_data)
        db_manager.load_dataframe_to_table(teams_df, 'teams', if_exists='replace')
        logger.info(f"Loaded {len(teams_df)} teams into database")
    
    def ingest_players_data(self, force_reload: bool = False):
        """Ingest player data from individual player files"""
        logger.info("Ingesting players data...")
        
        if not self.players_path.exists():
            logger.error(f"Players data path not found: {self.players_path}")
            return
        
        players_data = []
        performance_data = []
        
        # Get all player personal detail files
        personal_files = list(self.players_path.glob("*_personal_details.csv"))
        
        logger.info(f"Found {len(personal_files)} player files to process")
        
        for i, personal_file in enumerate(personal_files):
            try:
                # Extract player identifier from filename
                player_name = personal_file.stem.replace("_personal_details", "")
                
                # Read personal details
                personal_df = pd.read_csv(personal_file)
                if len(personal_df) > 0:
                    player_info = personal_df.iloc[0]
                    
                    # Create player record
                    player_record = {
                        'first_name': player_info.get('first_name', ''),
                        'last_name': player_info.get('last_name', ''),
                        'born_date': pd.to_datetime(player_info.get('born_date', None), errors='coerce'),
                        'debut_date': pd.to_datetime(player_info.get('debut_date', None), errors='coerce'),
                        'height': pd.to_numeric(player_info.get('height', None), errors='coerce'),
                        'weight': pd.to_numeric(player_info.get('weight', None), errors='coerce'),
                        'full_name': f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip(),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    players_data.append(player_record)
                    
                    # Read performance details if file exists
                    performance_file = personal_file.parent / f"{player_name}_performance_details.csv"
                    if performance_file.exists():
                        try:
                            perf_df = pd.read_csv(performance_file)
                            
                            # Add player_id reference (will be updated after players are inserted)
                            perf_df['player_id'] = len(players_data)  # Temporary ID
                            
                            # Clean and standardize performance data
                            perf_df = self._clean_performance_data(perf_df)
                            performance_data.extend(perf_df.to_dict('records'))
                            
                        except Exception as e:
                            logger.warning(f"Error reading performance file for {player_name}: {e}")
                
                # Progress logging
                if (i + 1) % 1000 == 0:
                    logger.info(f"Processed {i + 1}/{len(personal_files)} players")
                    
            except Exception as e:
                logger.warning(f"Error processing player file {personal_file}: {e}")
                continue
        
        # Load players data
        if players_data:
            players_df = pd.DataFrame(players_data)
            db_manager.load_dataframe_to_table(players_df, 'players', if_exists='replace' if force_reload else 'append')
            logger.info(f"Loaded {len(players_df)} players into database")
        
        # Load performance data
        if performance_data:
            performance_df = pd.DataFrame(performance_data)
            db_manager.load_dataframe_to_table(performance_df, 'player_performance', if_exists='replace' if force_reload else 'append')
            logger.info(f"Loaded {len(performance_df)} performance records into database")
    
    def ingest_matches_data(self, force_reload: bool = False):
        """Ingest match data from yearly match files"""
        logger.info("Ingesting matches data...")
        
        if not self.matches_path.exists():
            logger.error(f"Matches data path not found: {self.matches_path}")
            return
        
        matches_data = []
        
        # Get all match files
        match_files = list(self.matches_path.glob("matches_*.csv"))
        logger.info(f"Found {len(match_files)} match files to process")
        
        for match_file in match_files:
            try:
                year = match_file.stem.split('_')[1]
                matches_df = pd.read_csv(match_file)
                
                # Clean and standardize match data
                matches_df = self._clean_matches_data(matches_df, int(year))
                matches_data.extend(matches_df.to_dict('records'))
                
            except Exception as e:
                logger.warning(f"Error processing match file {match_file}: {e}")
                continue
        
        # Load matches data
        if matches_data:
            matches_df = pd.DataFrame(matches_data)
            db_manager.load_dataframe_to_table(matches_df, 'matches', if_exists='replace' if force_reload else 'append')
            logger.info(f"Loaded {len(matches_df)} matches into database")
    
    def _clean_performance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize player performance data"""
        # Convert numeric columns
        numeric_cols = [
            'games_played', 'jersey_num', 'kicks', 'marks', 'handballs', 'disposals',
            'goals', 'behinds', 'hit_outs', 'tackles', 'rebound_50s', 'inside_50s',
            'clearances', 'clangers', 'free_kicks_for', 'free_kicks_against',
            'brownlow_votes', 'contested_possessions', 'uncontested_possessions',
            'contested_marks', 'marks_inside_50', 'one_percenters', 'bounces',
            'goal_assist', 'percentage_of_game_played'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean team names and opponents
        if 'team' in df.columns:
            df['team'] = df['team'].astype(str).str.strip()
        if 'opponent' in df.columns:
            df['opponent'] = df['opponent'].astype(str).str.strip()
        
        return df
    
    def _clean_matches_data(self, df: pd.DataFrame, year: int) -> pd.DataFrame:
        """Clean and standardize match data"""
        # Ensure year is set
        df['year'] = year
        
        # Parse date
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Clean team names
        team_cols = ['team_1_team_name', 'team_2_team_name']
        for col in team_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Convert score columns to numeric
        score_cols = [col for col in df.columns if any(x in col for x in ['goals', 'behinds', 'q1', 'q2', 'q3', 'final'])]
        for col in score_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Rename columns to match database schema
        column_mapping = {
            'team_1_team_name': 'team_1_name',
            'team_2_team_name': 'team_2_name'
        }
        df = df.rename(columns=column_mapping)
        
        return df
    
    def get_ingestion_status(self) -> Dict[str, int]:
        """Get current ingestion status from database"""
        try:
            with db_manager.get_session() as session:
                # Count records in each table
                players_count = session.execute("SELECT COUNT(*) FROM players").scalar()
                performance_count = session.execute("SELECT COUNT(*) FROM player_performance").scalar()
                matches_count = session.execute("SELECT COUNT(*) FROM matches").scalar()
                teams_count = session.execute("SELECT COUNT(*) FROM teams").scalar()
                
                return {
                    'players': players_count,
                    'player_performance': performance_count,
                    'matches': matches_count,
                    'teams': teams_count
                }
        except Exception as e:
            logger.error(f"Error getting ingestion status: {e}")
            return {}

# Global service instance
afl_data_service = AFLDataIngestionService()