"""
Natural Language Processing module for Scout AI queries.
Processes natural language queries and converts them to data filters and analysis requests.
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AFLQueryProcessor:
    """
    Natural language query processor for AFL scouting queries
    """
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # AFL-specific keywords and mappings
        self.position_keywords = {
            'defender': ['defender', 'defence', 'back', 'backman', 'fullback', 'halfback'],
            'midfielder': ['midfielder', 'midfield', 'mid', 'centre', 'wing', 'winger'],
            'forward': ['forward', 'forwards', 'key forward', 'small forward', 'fullforward'],
            'ruck': ['ruck', 'ruckman', 'big man']
        }
        
        self.stat_keywords = {
            'disposals': ['disposal', 'disposals', 'possession', 'possessions', 'touch', 'touches'],
            'marks': ['mark', 'marks', 'marking', 'catch', 'catches'],
            'tackles': ['tackle', 'tackles', 'tackling', 'pressure'],
            'goals': ['goal', 'goals', 'scoring', 'kicking goals'],
            'contested_possessions': ['contested', 'contested possession', 'hard ball', 'contest'],
            'clearances': ['clearance', 'clearances', 'clearing'],
            'goal_accuracy': ['accuracy', 'goal accuracy', 'kicking accuracy', 'accurate'],
            'kicks': ['kick', 'kicks', 'kicking'],
            'handballs': ['handball', 'handballs', 'handpass']
        }
        
        self.team_keywords = {
            'adelaide': ['adelaide', 'crows'],
            'brisbane': ['brisbane', 'lions'],
            'carlton': ['carlton', 'blues'],
            'collingwood': ['collingwood', 'magpies', 'pies'],
            'essendon': ['essendon', 'bombers'],
            'fremantle': ['fremantle', 'dockers', 'freo'],
            'geelong': ['geelong', 'cats'],
            'gold_coast': ['gold coast', 'suns'],
            'gws': ['gws', 'giants', 'greater western sydney'],
            'hawthorn': ['hawthorn', 'hawks'],
            'melbourne': ['melbourne', 'demons', 'dees'],
            'north_melbourne': ['north melbourne', 'kangaroos', 'roos'],
            'port_adelaide': ['port adelaide', 'power', 'port'],
            'richmond': ['richmond', 'tigers'],
            'st_kilda': ['st kilda', 'saints'],
            'sydney': ['sydney', 'swans'],
            'west_coast': ['west coast', 'eagles'],
            'western_bulldogs': ['western bulldogs', 'bulldogs', 'dogs']
        }
        
        self.league_keywords = {
            'afl': ['afl', 'australian football league'],
            'vfl': ['vfl', 'victorian football league'],
            'sanfl': ['sanfl', 'south australian national football league'],
            'wafl': ['wafl', 'west australian football league'],
            'neafl': ['neafl', 'north east australian football league']
        }
        
        self.comparison_keywords = {
            'high': ['high', 'top', 'best', 'excellent', 'great', 'good', 'above'],
            'low': ['low', 'bottom', 'worst', 'poor', 'below'],
            'medium': ['medium', 'average', 'moderate']
        }
        
        self.age_keywords = {
            'young': ['young', 'youth', 'junior', 'under'],
            'experienced': ['experienced', 'veteran', 'old', 'senior', 'over']
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query and extract structured filters
        """
        logger.info(f"Processing query: {query}")
        
        # Normalize query
        query_lower = query.lower()
        tokens = word_tokenize(query_lower)
        
        # Extract components
        filters = {
            'positions': self._extract_positions(query_lower),
            'teams': self._extract_teams(query_lower),
            'leagues': self._extract_leagues(query_lower),
            'stats': self._extract_stats(query_lower),
            'age_range': self._extract_age_range(query_lower),
            'comparisons': self._extract_comparisons(query_lower, tokens),
            'sort_by': self._extract_sort_criteria(query_lower),
            'limit': self._extract_limit(query_lower)
        }
        
        # Determine query type
        query_type = self._determine_query_type(query_lower)
        
        result = {
            'original_query': query,
            'query_type': query_type,
            'filters': filters,
            'confidence': self._calculate_confidence(filters)
        }
        
        logger.info(f"Extracted filters: {filters}")
        return result
    
    def _extract_positions(self, query: str) -> List[str]:
        """Extract position filters from query"""
        positions = []
        for position, keywords in self.position_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    positions.append(position)
                    break
        return list(set(positions))  # Remove duplicates
    
    def _extract_teams(self, query: str) -> List[str]:
        """Extract team filters from query"""
        teams = []
        for team, keywords in self.team_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    teams.append(team)
                    break
        return list(set(teams))
    
    def _extract_leagues(self, query: str) -> List[str]:
        """Extract league filters from query"""
        leagues = []
        for league, keywords in self.league_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    leagues.append(league)
                    break
        return list(set(leagues))
    
    def _extract_stats(self, query: str) -> List[str]:
        """Extract statistical metrics from query"""
        stats = []
        for stat, keywords in self.stat_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    stats.append(stat)
                    break
        return list(set(stats))
    
    def _extract_age_range(self, query: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract age range from query"""
        # Look for specific age numbers
        age_pattern = r'(?:under|over|above|below)?\s*(\d{1,2})'
        matches = re.findall(age_pattern, query)
        
        min_age, max_age = None, None
        
        if matches:
            for match in matches:
                age = int(match)
                if 'under' in query or 'below' in query:
                    max_age = age
                elif 'over' in query or 'above' in query:
                    min_age = age
                else:
                    # Exact age or range
                    if min_age is None:
                        min_age = age
                    else:
                        max_age = age
        
        # Look for age-related keywords
        if any(keyword in query for keyword in self.age_keywords['young']):
            if max_age is None:
                max_age = 23
        
        if any(keyword in query for keyword in self.age_keywords['experienced']):
            if min_age is None:
                min_age = 28
        
        return (min_age, max_age)
    
    def _extract_comparisons(self, query: str, tokens: List[str]) -> Dict[str, str]:
        """Extract comparison criteria (high, low, etc.)"""
        comparisons = {}
        
        for stat, keywords in self.stat_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    # Look for comparison words near the stat
                    for comp_type, comp_keywords in self.comparison_keywords.items():
                        for comp_keyword in comp_keywords:
                            if comp_keyword in query:
                                # Simple proximity check
                                if abs(query.find(keyword) - query.find(comp_keyword)) < 50:
                                    comparisons[stat] = comp_type
                                    break
        
        return comparisons
    
    def _extract_sort_criteria(self, query: str) -> Optional[str]:
        """Extract sorting criteria from query"""
        sort_keywords = ['best', 'top', 'highest', 'most', 'leading']
        
        for keyword in sort_keywords:
            if keyword in query:
                # Find what stat to sort by
                for stat, stat_keywords in self.stat_keywords.items():
                    for stat_keyword in stat_keywords:
                        if stat_keyword in query:
                            return stat
        
        return None
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract result limit from query"""
        # Look for "top N", "best N", etc.
        limit_pattern = r'(?:top|best|first)\s*(\d+)'
        match = re.search(limit_pattern, query)
        
        if match:
            return int(match.group(1))
        
        # Default limits based on query type
        if any(word in query for word in ['top', 'best', 'leading']):
            return 10
        
        return None
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query being asked"""
        if any(word in query for word in ['find', 'show', 'list', 'get']):
            return 'search'
        elif any(word in query for word in ['compare', 'vs', 'versus']):
            return 'comparison'
        elif any(word in query for word in ['analyze', 'analysis', 'breakdown']):
            return 'analysis'
        elif any(word in query for word in ['rank', 'ranking', 'top', 'best']):
            return 'ranking'
        elif any(word in query for word in ['predict', 'forecast', 'potential']):
            return 'prediction'
        else:
            return 'search'  # Default
    
    def _calculate_confidence(self, filters: Dict[str, Any]) -> float:
        """Calculate confidence score for query parsing"""
        confidence = 0.0
        total_weight = 0.0
        
        # Weight different filter types
        weights = {
            'positions': 0.2,
            'teams': 0.15,
            'leagues': 0.1,
            'stats': 0.3,
            'age_range': 0.1,
            'comparisons': 0.1,
            'sort_by': 0.05
        }
        
        for filter_type, weight in weights.items():
            total_weight += weight
            if filters.get(filter_type):
                if isinstance(filters[filter_type], list):
                    if filters[filter_type]:  # Non-empty list
                        confidence += weight
                elif isinstance(filters[filter_type], tuple):
                    if any(filters[filter_type]):  # At least one value in tuple
                        confidence += weight
                elif filters[filter_type]:  # Non-empty/non-None value
                    confidence += weight
        
        return confidence / total_weight if total_weight > 0 else 0.0
    
    def apply_filters_to_dataframe(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply extracted filters to a pandas DataFrame
        """
        filtered_df = df.copy()
        
        try:
            # Position filter
            if filters['positions'] and 'Position' in filtered_df.columns:
                position_mask = filtered_df['Position'].str.lower().isin(
                    [pos.lower() for pos in filters['positions']]
                )
                filtered_df = filtered_df[position_mask]
            
            # Team filter
            if filters['teams'] and 'Team' in filtered_df.columns:
                team_mask = filtered_df['Team'].str.lower().str.contains(
                    '|'.join(filters['teams']), case=False, na=False
                )
                filtered_df = filtered_df[team_mask]
            
            # Age range filter
            min_age, max_age = filters['age_range']
            if 'Age' in filtered_df.columns:
                if min_age is not None:
                    filtered_df = filtered_df[filtered_df['Age'] >= min_age]
                if max_age is not None:
                    filtered_df = filtered_df[filtered_df['Age'] <= max_age]
            
            # Statistical comparisons
            for stat, comparison in filters['comparisons'].items():
                if stat in filtered_df.columns:
                    if comparison == 'high':
                        threshold = filtered_df[stat].quantile(0.75)
                        filtered_df = filtered_df[filtered_df[stat] >= threshold]
                    elif comparison == 'low':
                        threshold = filtered_df[stat].quantile(0.25)
                        filtered_df = filtered_df[filtered_df[stat] <= threshold]
                    elif comparison == 'medium':
                        q25 = filtered_df[stat].quantile(0.25)
                        q75 = filtered_df[stat].quantile(0.75)
                        filtered_df = filtered_df[
                            (filtered_df[stat] >= q25) & (filtered_df[stat] <= q75)
                        ]
            
            # Sorting
            if filters['sort_by'] and filters['sort_by'] in filtered_df.columns:
                filtered_df = filtered_df.sort_values(filters['sort_by'], ascending=False)
            
            # Limit results
            if filters['limit']:
                filtered_df = filtered_df.head(filters['limit'])
            
            logger.info(f"Applied filters, {len(filtered_df)} records remaining")
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return df

def main():
    """
    Main function to demonstrate query processing
    """
    processor = AFLQueryProcessor()
    
    # Example queries
    test_queries = [
        "Find midfielders under 23 with high clearance rates in the VFL",
        "Show me the top 10 key forwards with best goal accuracy",
        "Compare Carlton players vs Richmond players for contested possessions",
        "List young defenders with good marking ability"
    ]
    
    for query in test_queries:
        result = processor.process_query(query)
        print(f"\nQuery: {query}")
        print(f"Type: {result['query_type']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Filters: {result['filters']}")

if __name__ == "__main__":
    main()