"""
Database setup and connection management for ScoutAI
"""
import logging
from contextlib import contextmanager
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, Date, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .config import config

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(config.database.url, echo=config.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DatabaseManager:
    """Manages database operations for AFL data"""
    
    def __init__(self):
        self.engine = engine
        self.metadata = MetaData()
        
    def create_tables(self):
        """Create all necessary tables for AFL data"""
        try:
            # Player personal details table
            players_table = Table(
                'players', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('first_name', String(100)),
                Column('last_name', String(100)),
                Column('born_date', Date),
                Column('debut_date', Date),
                Column('height', Integer),
                Column('weight', Integer),
                Column('full_name', String(200)),
                Column('created_at', DateTime),
                Column('updated_at', DateTime)
            )
            
            # Player performance table
            player_performance_table = Table(
                'player_performance', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('player_id', Integer),
                Column('team', String(100)),
                Column('year', Integer),
                Column('games_played', Integer),
                Column('opponent', String(100)),
                Column('round', String(10)),
                Column('result', String(1)),
                Column('jersey_num', Integer),
                Column('kicks', Integer),
                Column('marks', Integer),
                Column('handballs', Integer),
                Column('disposals', Integer),
                Column('goals', Integer),
                Column('behinds', Integer),
                Column('hit_outs', Integer),
                Column('tackles', Integer),
                Column('rebound_50s', Integer),
                Column('inside_50s', Integer),
                Column('clearances', Integer),
                Column('clangers', Integer),
                Column('free_kicks_for', Integer),
                Column('free_kicks_against', Integer),
                Column('brownlow_votes', Integer),
                Column('contested_possessions', Integer),
                Column('uncontested_possessions', Integer),
                Column('contested_marks', Integer),
                Column('marks_inside_50', Integer),
                Column('one_percenters', Integer),
                Column('bounces', Integer),
                Column('goal_assist', Integer),
                Column('percentage_of_game_played', Integer)
            )
            
            # Matches table
            matches_table = Table(
                'matches', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('round_num', Integer),
                Column('venue', String(200)),
                Column('date', DateTime),
                Column('year', Integer),
                Column('attendance', String(50)),
                Column('team_1_name', String(100)),
                Column('team_1_q1_goals', Integer),
                Column('team_1_q1_behinds', Integer),
                Column('team_1_q2_goals', Integer),
                Column('team_1_q2_behinds', Integer),
                Column('team_1_q3_goals', Integer),
                Column('team_1_q3_behinds', Integer),
                Column('team_1_final_goals', Integer),
                Column('team_1_final_behinds', Integer),
                Column('team_2_name', String(100)),
                Column('team_2_q1_goals', Integer),
                Column('team_2_q1_behinds', Integer),
                Column('team_2_q2_goals', Integer),
                Column('team_2_q2_behinds', Integer),
                Column('team_2_q3_goals', Integer),
                Column('team_2_q3_behinds', Integer),
                Column('team_2_final_goals', Integer),
                Column('team_2_final_behinds', Integer)
            )
            
            # Teams table
            teams_table = Table(
                'teams', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('name', String(100), unique=True),
                Column('short_name', String(10)),
                Column('league', String(50)),  # AFLM, AFLW, VFL, SANFL, etc.
                Column('founded_year', Integer),
                Column('colors', String(100)),
                Column('is_active', Boolean, default=True)
            )
            
            # Users table for authentication
            users_table = Table(
                'users', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('username', String(50), unique=True),
                Column('email', String(100), unique=True),
                Column('hashed_password', String(255)),
                Column('role', String(20)),  # Scout, Analyst, Admin
                Column('team_access', String(500)),  # JSON array of accessible teams
                Column('is_active', Boolean, default=True),
                Column('created_at', DateTime),
                Column('last_login', DateTime)
            )
            
            # Player analysis cache table
            player_analysis_table = Table(
                'player_analysis', self.metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('player_id', Integer),
                Column('analysis_type', String(50)),
                Column('analysis_data', String),  # JSON data
                Column('llm_insights', String),  # Natural language insights
                Column('created_at', DateTime),
                Column('updated_at', DateTime)
            )
            
            # Create all tables
            self.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def load_dataframe_to_table(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """Load pandas DataFrame to database table"""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False, method='multi')
            logger.info(f"Successfully loaded {len(df)} rows to {table_name}")
        except Exception as e:
            logger.error(f"Error loading DataFrame to {table_name}: {e}")
            raise

# Global database instance
db_manager = DatabaseManager()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    with db_manager.get_session() as session:
        yield session