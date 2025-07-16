"""
Squiggle API data scraper for AFL match results, predictions, and ladder data.
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SquiggleAPI:
    """
    Interface for Squiggle API data collection
    """
    
    def __init__(self):
        self.base_url = "https://api.squiggle.com.au"
        self.session = requests.Session()
        
    def get_games(self, year=None, round_num=None, team=None):
        """
        Fetch AFL games data
        """
        params = {'q': 'games'}
        if year:
            params['year'] = year
        if round_num:
            params['round'] = round_num
        if team:
            params['team'] = team
            
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'games' in data:
                return pd.DataFrame(data['games'])
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return pd.DataFrame()
    
    def get_ladder(self, year=None, round_num=None):
        """
        Fetch AFL ladder data
        """
        params = {'q': 'ladder'}
        if year:
            params['year'] = year
        if round_num:
            params['round'] = round_num
            
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'ladder' in data:
                return pd.DataFrame(data['ladder'])
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching ladder: {e}")
            return pd.DataFrame()
    
    def get_tips(self, year=None, round_num=None):
        """
        Fetch AFL tips/predictions
        """
        params = {'q': 'tips'}
        if year:
            params['year'] = year
        if round_num:
            params['round'] = round_num
            
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'tips' in data:
                return pd.DataFrame(data['tips'])
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching tips: {e}")
            return pd.DataFrame()
    
    def get_teams(self):
        """
        Fetch AFL teams data
        """
        params = {'q': 'teams'}
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'teams' in data:
                return pd.DataFrame(data['teams'])
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, start_year=2023, end_year=2025):
        """
        Fetch historical data for multiple years
        """
        all_games = []
        all_ladder = []
        all_tips = []
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching data for {year}")
            
            # Games
            games_df = self.get_games(year=year)
            if not games_df.empty:
                games_df['year'] = year
                all_games.append(games_df)
            
            # Ladder
            ladder_df = self.get_ladder(year=year)
            if not ladder_df.empty:
                ladder_df['year'] = year
                all_ladder.append(ladder_df)
            
            # Tips
            tips_df = self.get_tips(year=year)
            if not tips_df.empty:
                tips_df['year'] = year
                all_tips.append(tips_df)
            
            # Rate limiting
            time.sleep(1)
        
        result = {}
        if all_games:
            result['games'] = pd.concat(all_games, ignore_index=True)
        if all_ladder:
            result['ladder'] = pd.concat(all_ladder, ignore_index=True)
        if all_tips:
            result['tips'] = pd.concat(all_tips, ignore_index=True)
            
        return result

def main():
    """
    Main function to demonstrate Squiggle API usage
    """
    api = SquiggleAPI()
    
    # Fetch recent data
    logger.info("Fetching current season data...")
    current_year = datetime.now().year
    
    games = api.get_games(year=current_year)
    ladder = api.get_ladder(year=current_year)
    teams = api.get_teams()
    
    # Save to CSV
    if not games.empty:
        games.to_csv('data/raw/squiggle_games.csv', index=False)
        logger.info(f"Saved {len(games)} games to CSV")
    
    if not ladder.empty:
        ladder.to_csv('data/raw/squiggle_ladder.csv', index=False)
        logger.info(f"Saved {len(ladder)} ladder entries to CSV")
    
    if not teams.empty:
        teams.to_csv('data/raw/squiggle_teams.csv', index=False)
        logger.info(f"Saved {len(teams)} teams to CSV")

if __name__ == "__main__":
    main()