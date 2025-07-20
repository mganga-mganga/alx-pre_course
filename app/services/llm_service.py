"""
LLM Integration Service for Natural Language Insights
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..config import config
from ..database import db_manager

logger = logging.getLogger(__name__)

class LLMInsightService:
    """Service for generating natural language insights using LLM"""
    
    def __init__(self):
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            openai.api_key = config.llm.api_key
        
    def generate_player_analysis(self, player_data: Dict[str, Any], performance_data: List[Dict[str, Any]]) -> str:
        """Generate comprehensive player analysis"""
        try:
            # Prepare player context
            player_context = self._prepare_player_context(player_data, performance_data)
            
            prompt = f"""
            As an expert AFL scout, analyze the following player data and provide comprehensive insights:

            PLAYER PROFILE:
            {json.dumps(player_context, indent=2)}

            Please provide a detailed scouting report covering:
            1. Overall Performance Assessment
            2. Key Strengths and Weaknesses
            3. Positional Analysis
            4. Career Trajectory and Development
            5. Comparison to League Averages
            6. Injury Risk Assessment (if applicable)
            7. Recruitment Recommendation

            Format your response as a professional scouting report suitable for AFL recruiters and coaches.
            """
            
            return self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Error generating player analysis: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def generate_team_analysis(self, team_data: Dict[str, Any], recent_matches: List[Dict[str, Any]]) -> str:
        """Generate team performance analysis"""
        try:
            team_context = self._prepare_team_context(team_data, recent_matches)
            
            prompt = f"""
            As an expert AFL analyst, analyze the following team data and provide strategic insights:

            TEAM ANALYSIS:
            {json.dumps(team_context, indent=2)}

            Please provide a comprehensive team analysis covering:
            1. Current Form and Performance Trends
            2. Tactical Strengths and Weaknesses
            3. Key Player Dependencies
            4. Matchup Analysis
            5. Areas for Improvement
            6. Strategic Recommendations
            7. Finals/Championship Prospects

            Format your response as a professional team analysis suitable for coaches and analysts.
            """
            
            return self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Error generating team analysis: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def generate_match_preview(self, team1_data: Dict, team2_data: Dict, historical_matchups: List[Dict]) -> str:
        """Generate match preview and prediction"""
        try:
            match_context = {
                "team1": team1_data,
                "team2": team2_data,
                "historical_matchups": historical_matchups
            }
            
            prompt = f"""
            As an expert AFL analyst, provide a detailed match preview based on the following data:

            MATCH PREVIEW DATA:
            {json.dumps(match_context, indent=2)}

            Please provide a comprehensive match preview covering:
            1. Team Form Comparison
            2. Key Matchups to Watch
            3. Tactical Battle Areas
            4. X-Factor Players
            5. Venue and Conditions Impact
            6. Historical Head-to-Head Analysis
            7. Match Prediction with Reasoning

            Format as an engaging match preview suitable for fans, media, and betting analysis.
            """
            
            return self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Error generating match preview: {e}")
            return f"Error generating preview: {str(e)}"
    
    def explain_statistics(self, stat_name: str, value: float, context: str = "") -> str:
        """Explain what a statistic means in AFL context"""
        try:
            prompt = f"""
            As an AFL expert, explain the statistic "{stat_name}" with value {value} in simple terms.
            
            Context: {context}
            
            Please explain:
            1. What this statistic measures
            2. Whether this value is good, average, or poor
            3. How it impacts team performance
            4. What fans should know about this metric
            
            Keep the explanation concise and accessible to casual AFL fans.
            """
            
            return self._call_llm(prompt, max_tokens=300)
            
        except Exception as e:
            logger.error(f"Error explaining statistic: {e}")
            return f"Unable to explain statistic: {stat_name}"
    
    def generate_draft_recommendation(self, player_data: Dict, draft_context: Dict) -> str:
        """Generate draft recommendation for young players"""
        try:
            prompt = f"""
            As an AFL draft expert, evaluate this draft prospect:

            PLAYER DATA:
            {json.dumps(player_data, indent=2)}

            DRAFT CONTEXT:
            {json.dumps(draft_context, indent=2)}

            Provide a draft recommendation covering:
            1. Overall Draft Rating (1-100)
            2. Best Position Projection
            3. Development Timeline
            4. Risk Assessment
            5. Comparison to Similar Players
            6. Team Fit Analysis
            7. Draft Round Recommendation

            Format as a professional draft report.
            """
            
            return self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Error generating draft recommendation: {e}")
            return f"Error generating draft recommendation: {str(e)}"
    
    def chat_query(self, query: str, context_data: Dict = None) -> str:
        """Handle natural language queries about AFL data"""
        try:
            context_str = ""
            if context_data:
                context_str = f"\nCONTEXT DATA:\n{json.dumps(context_data, indent=2)}"
            
            prompt = f"""
            You are an expert AFL analyst assistant. Answer the following query about AFL data:

            QUERY: {query}
            {context_str}

            Provide a comprehensive, accurate answer based on AFL knowledge and the provided data.
            If you cannot answer definitively, explain what additional information would be needed.
            """
            
            return self._call_llm(prompt)
            
        except Exception as e:
            logger.error(f"Error processing chat query: {e}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}"
    
    def _call_llm(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call the configured LLM service"""
        if not max_tokens:
            max_tokens = self.max_tokens
        
        try:
            if self.provider == "openai" and OPENAI_AVAILABLE and config.llm.api_key:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert AFL analyst and scout with deep knowledge of Australian Football League statistics, tactics, and player development."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "local":
                # Placeholder for local LLM integration (Ollama, etc.)
                return "Local LLM integration not implemented yet. Please configure OpenAI API key for full functionality."
            
            else:
                return "LLM service not properly configured. Please check your API keys and settings."
                
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return f"Unable to generate analysis at this time. Error: {str(e)}"
    
    def _prepare_player_context(self, player_data: Dict, performance_data: List[Dict]) -> Dict:
        """Prepare player data context for LLM analysis"""
        if not performance_data:
            return {"player": player_data, "note": "No performance data available"}
        
        # Calculate key statistics
        recent_games = performance_data[-20:] if len(performance_data) > 20 else performance_data
        career_stats = self._calculate_career_stats(performance_data)
        recent_stats = self._calculate_career_stats(recent_games)
        
        return {
            "player": player_data,
            "career_summary": {
                "total_games": len(performance_data),
                "career_averages": career_stats,
                "recent_form": recent_stats,
                "years_active": list(set(p.get('year', 0) for p in performance_data if p.get('year')))
            },
            "recent_performances": recent_games[-5:] if len(recent_games) >= 5 else recent_games
        }
    
    def _prepare_team_context(self, team_data: Dict, recent_matches: List[Dict]) -> Dict:
        """Prepare team data context for LLM analysis"""
        return {
            "team": team_data,
            "recent_matches": recent_matches,
            "form_analysis": self._analyze_team_form(recent_matches)
        }
    
    def _calculate_career_stats(self, performance_data: List[Dict]) -> Dict:
        """Calculate average career statistics"""
        if not performance_data:
            return {}
        
        stats = {}
        numeric_fields = ['kicks', 'marks', 'handballs', 'disposals', 'goals', 'behinds', 
                         'tackles', 'inside_50s', 'clearances', 'contested_possessions']
        
        for field in numeric_fields:
            values = [p.get(field, 0) for p in performance_data if p.get(field) is not None]
            if values:
                stats[f"avg_{field}"] = round(sum(values) / len(values), 2)
        
        return stats
    
    def _analyze_team_form(self, recent_matches: List[Dict]) -> Dict:
        """Analyze team form from recent matches"""
        if not recent_matches:
            return {"note": "No recent match data available"}
        
        wins = sum(1 for match in recent_matches if match.get('result') == 'W')
        losses = sum(1 for match in recent_matches if match.get('result') == 'L')
        
        return {
            "recent_record": f"{wins}-{losses}",
            "win_percentage": round((wins / len(recent_matches)) * 100, 1) if recent_matches else 0,
            "form_trend": "Improving" if wins > losses else "Declining" if losses > wins else "Stable"
        }
    
    def cache_analysis(self, entity_id: int, analysis_type: str, analysis_data: Dict, llm_insights: str):
        """Cache analysis results in database"""
        try:
            with db_manager.get_session() as session:
                cache_record = {
                    'player_id': entity_id,
                    'analysis_type': analysis_type,
                    'analysis_data': json.dumps(analysis_data),
                    'llm_insights': llm_insights,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Insert cache record
                session.execute(
                    "INSERT INTO player_analysis (player_id, analysis_type, analysis_data, llm_insights, created_at, updated_at) VALUES (:player_id, :analysis_type, :analysis_data, :llm_insights, :created_at, :updated_at)",
                    cache_record
                )
                session.commit()
                
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")

# Global LLM service instance
llm_service = LLMInsightService()