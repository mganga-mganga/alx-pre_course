"""
ScoutAI Enterprise - Enhanced Streamlit Dashboard
Enterprise-Grade AFL Scouting Intelligence System with Authentication and Advanced Features
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import io
import sys
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent / "app"))

# Import enterprise modules
try:
    from app.config import config
    from app.database import db_manager
    from app.auth.auth_service import auth_service, UserRole
    from app.services.data_ingestion import afl_data_service
    from app.services.llm_service import llm_service
    from app.models.enhanced_ml_models import player_model, team_model
    from app.reports.report_generator import report_generator
    ENTERPRISE_MODE = True
except ImportError as e:
    st.error(f"Enterprise modules not available: {e}")
    ENTERPRISE_MODE = False

# Page configuration
st.set_page_config(
    page_title="ScoutAI Enterprise - AFL Scouting Platform",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enterprise styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Roboto', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #003f7f 0%, #cc2e3a 50%, #ffcd00 100%);
        padding: 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #003f7f;
        margin: 1rem 0;
    }
    
    .enterprise-badge {
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0;
    }
    
    .user-info {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #003f7f, #cc2e3a);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    .success-message {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: linear-gradient(135deg, #ff9a9e, #fecfef);
        color: #333;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

def login_page():
    """Display login page"""
    st.markdown("""
    <div class="main-header">
        <h1>🏈 ScoutAI Enterprise</h1>
        <h3>AFL Scouting Intelligence System</h3>
        <div class="enterprise-badge">Enterprise Edition</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 User Authentication")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if username and password:
                    try:
                        # Authenticate with enterprise backend
                        if ENTERPRISE_MODE:
                            user = auth_service.authenticate_user(username, password)
                            if user:
                                token = auth_service.create_access_token(user)
                                permissions = auth_service.get_user_permissions(user['role'])
                                
                                st.session_state.authenticated = True
                                st.session_state.user_data = user
                                st.session_state.access_token = token
                                st.session_state.permissions = permissions
                                
                                st.success("✅ Login successful!")
                                st.rerun()
                            else:
                                st.error("❌ Invalid credentials")
                        else:
                            st.error("❌ Enterprise mode not available")
                    except Exception as e:
                        st.error(f"❌ Login failed: {str(e)}")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Demo credentials info
        if ENTERPRISE_MODE:
            st.markdown("""
            <div class="warning-message">
                <strong>Demo Credentials:</strong><br>
                Username: admin<br>
                Password: (check console output for auto-generated password)
            </div>
            """, unsafe_allow_html=True)

def main_dashboard():
    """Main dashboard for authenticated users"""
    user_data = st.session_state.user_data
    permissions = st.session_state.permissions
    
    # Header with user info
    st.markdown(f"""
    <div class="main-header">
        <h1>🏈 ScoutAI Enterprise Dashboard</h1>
        <div class="user-info">
            <strong>Welcome, {user_data['username']}!</strong> | 
            Role: {user_data['role'].title()} | 
            <span style="color: #ffcd00;">● Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        # Logout button
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.access_token = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigation options based on permissions
        pages = []
        if permissions.get('view_players'):
            pages.append("👤 Player Analysis")
        if permissions.get('view_teams'):
            pages.append("🏟️ Team Analysis")
        if permissions.get('access_analytics'):
            pages.append("📊 Advanced Analytics")
        if permissions.get('generate_reports'):
            pages.append("📋 Reports")
        if permissions.get('access_llm'):
            pages.append("🤖 AI Chat")
        if permissions.get('manage_data'):
            pages.append("💾 Data Management")
        if permissions.get('manage_users'):
            pages.append("👥 User Management")
        
        selected_page = st.selectbox("Select Page", pages)
        
        # System status
        st.markdown("### 📊 System Status")
        if ENTERPRISE_MODE:
            try:
                status = afl_data_service.get_ingestion_status()
                st.metric("Players", status.get('players', 0))
                st.metric("Matches", status.get('matches', 0))
                st.metric("Teams", status.get('teams', 0))
            except Exception as e:
                st.error(f"Status unavailable: {e}")
    
    # Main content area
    if selected_page == "👤 Player Analysis":
        player_analysis_page()
    elif selected_page == "🏟️ Team Analysis":
        team_analysis_page()
    elif selected_page == "📊 Advanced Analytics":
        advanced_analytics_page()
    elif selected_page == "📋 Reports":
        reports_page()
    elif selected_page == "🤖 AI Chat":
        ai_chat_page()
    elif selected_page == "💾 Data Management":
        data_management_page()
    elif selected_page == "👥 User Management":
        user_management_page()

def player_analysis_page():
    """Player analysis and scouting page"""
    st.markdown("## 👤 Player Analysis & Scouting")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🔍 Search Players")
        
        # Player search
        search_term = st.text_input("Search players", placeholder="Enter player name...")
        
        if search_term or st.button("Load All Players"):
            try:
                with db_manager.get_session() as session:
                    if search_term:
                        query = """
                        SELECT id, first_name, last_name, height, weight, born_date
                        FROM players 
                        WHERE LOWER(first_name || ' ' || last_name) LIKE LOWER(:search)
                        ORDER BY last_name, first_name
                        LIMIT 50
                        """
                        result = session.execute(query, {'search': f'%{search_term}%'}).fetchall()
                    else:
                        query = """
                        SELECT id, first_name, last_name, height, weight, born_date
                        FROM players 
                        ORDER BY last_name, first_name
                        LIMIT 100
                        """
                        result = session.execute(query).fetchall()
                    
                    if result:
                        players_df = pd.DataFrame([dict(row._mapping) for row in result])
                        players_df['display_name'] = players_df['first_name'] + ' ' + players_df['last_name']
                        
                        selected_player = st.selectbox(
                            "Select Player",
                            options=players_df['id'].tolist(),
                            format_func=lambda x: players_df[players_df['id'] == x]['display_name'].iloc[0]
                        )
                        
                        if selected_player:
                            st.session_state.selected_player_id = selected_player
                    else:
                        st.warning("No players found")
            except Exception as e:
                st.error(f"Error loading players: {e}")
    
    with col2:
        if hasattr(st.session_state, 'selected_player_id'):
            display_player_analysis(st.session_state.selected_player_id)

def display_player_analysis(player_id):
    """Display detailed player analysis"""
    try:
        with db_manager.get_session() as session:
            # Get player details
            player_query = "SELECT * FROM players WHERE id = :player_id"
            player_result = session.execute(player_query, {'player_id': player_id}).fetchone()
            
            if not player_result:
                st.error("Player not found")
                return
            
            player_data = dict(player_result._mapping)
            
            # Player header
            st.markdown(f"### 🏈 {player_data['first_name']} {player_data['last_name']}")
            
            # Basic info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Height", f"{player_data.get('height', 'N/A')} cm")
            with col2:
                st.metric("Weight", f"{player_data.get('weight', 'N/A')} kg")
            with col3:
                if player_data.get('born_date'):
                    age = (datetime.now().date() - player_data['born_date']).days // 365
                    st.metric("Age", f"{age} years")
            with col4:
                st.metric("Debut", str(player_data.get('debut_date', 'N/A'))[:10] if player_data.get('debut_date') else 'N/A')
            
            # Get performance data
            performance_query = """
            SELECT * FROM player_performance 
            WHERE player_id = :player_id 
            ORDER BY year DESC, games_played DESC
            """
            performance_result = session.execute(performance_query, {'player_id': player_id}).fetchall()
            
            if performance_result:
                performance_df = pd.DataFrame([dict(row._mapping) for row in performance_result])
                
                # Performance trends
                st.markdown("#### 📈 Performance Trends")
                
                # Key stats over time
                if len(performance_df) > 1:
                    fig = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=('Disposals per Game', 'Goals per Game', 'Tackles per Game', 'Marks per Game')
                    )
                    
                    # Disposals
                    fig.add_trace(
                        go.Scatter(x=performance_df['year'], y=performance_df['disposals'], name='Disposals'),
                        row=1, col=1
                    )
                    
                    # Goals
                    fig.add_trace(
                        go.Scatter(x=performance_df['year'], y=performance_df['goals'], name='Goals'),
                        row=1, col=2
                    )
                    
                    # Tackles
                    fig.add_trace(
                        go.Scatter(x=performance_df['year'], y=performance_df['tackles'], name='Tackles'),
                        row=2, col=1
                    )
                    
                    # Marks
                    fig.add_trace(
                        go.Scatter(x=performance_df['year'], y=performance_df['marks'], name='Marks'),
                        row=2, col=2
                    )
                    
                    fig.update_layout(height=500, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                # AI Analysis
                if st.session_state.permissions.get('access_analytics'):
                    st.markdown("#### 🤖 AI Analysis")
                    
                    if st.button("Generate AI Analysis"):
                        with st.spinner("Generating AI analysis..."):
                            try:
                                # ML Predictions
                                ml_analysis = player_model.predict_player_potential(player_id)
                                
                                if 'error' not in ml_analysis:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Impact Score", f"{ml_analysis.get('current_impact_score', 0):.2f}")
                                    with col2:
                                        st.metric("Career Stage", ml_analysis.get('career_stage', 'Unknown'))
                                    with col3:
                                        st.metric("Injury Risk", ml_analysis.get('injury_risk', 'Unknown'))
                                    
                                    # Future projections
                                    if 'projections' in ml_analysis:
                                        st.markdown("##### 📊 Performance Projections")
                                        projections_df = pd.DataFrame(ml_analysis['projections'])
                                        
                                        fig = px.line(projections_df, x='year', y='projected_impact', 
                                                     title='Projected Impact Score')
                                        st.plotly_chart(fig, use_container_width=True)
                                
                                # LLM Analysis
                                if st.session_state.permissions.get('access_llm'):
                                    performance_data = [dict(row._mapping) for row in performance_result[:20]]
                                    llm_analysis = llm_service.generate_player_analysis(player_data, performance_data)
                                    
                                    st.markdown("##### 📝 Expert Analysis")
                                    st.write(llm_analysis)
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                
                # Performance table
                st.markdown("#### 📊 Recent Performance")
                recent_performance = performance_df.head(10)
                st.dataframe(recent_performance[['year', 'team', 'games_played', 'disposals', 'goals', 'tackles', 'marks']], use_container_width=True)
            
            else:
                st.warning("No performance data available for this player")
                
    except Exception as e:
        st.error(f"Error loading player analysis: {e}")

def team_analysis_page():
    """Team analysis page"""
    st.markdown("## 🏟️ Team Analysis")
    
    try:
        with db_manager.get_session() as session:
            # Get teams
            teams_query = "SELECT DISTINCT name FROM teams WHERE is_active = true ORDER BY name"
            teams_result = session.execute(teams_query).fetchall()
            teams = [row[0] for row in teams_result]
            
            if teams:
                selected_team = st.selectbox("Select Team", teams)
                season = st.selectbox("Select Season", [2024, 2023, 2022, 2021, 2020])
                
                if st.button("Analyze Team"):
                    with st.spinner("Analyzing team performance..."):
                        try:
                            # Get ML analysis
                            ml_analysis = team_model.analyze_team_performance(selected_team, season)
                            
                            if 'error' not in ml_analysis:
                                st.markdown(f"### 📊 {selected_team} - {season} Season Analysis")
                                
                                # Key metrics
                                stats = ml_analysis.get('overall_stats', {})
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Matches Played", stats.get('total_matches', 0))
                                with col2:
                                    st.metric("Wins", stats.get('wins', 0))
                                with col3:
                                    st.metric("Win %", f"{stats.get('win_percentage', 0):.1f}%")
                                with col4:
                                    st.metric("Avg Margin", f"{stats.get('avg_margin', 0):.1f}")
                                
                                # Form analysis
                                if 'recent_form' in ml_analysis:
                                    form = ml_analysis['recent_form']
                                    st.markdown("#### 📈 Recent Form")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Recent Record", form.get('recent_record', 'N/A'))
                                    with col2:
                                        st.metric("Form Trend", form.get('form_trend', 'N/A'))
                                    with col3:
                                        st.metric("Recent Win %", f"{form.get('recent_win_percentage', 0):.1f}%")
                                
                                # Strengths and weaknesses
                                if 'strengths_weaknesses' in ml_analysis:
                                    sw = ml_analysis['strengths_weaknesses']
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("#### ✅ Strengths")
                                        for strength in sw.get('strengths', []):
                                            st.write(f"• {strength}")
                                    
                                    with col2:
                                        st.markdown("#### ⚠️ Areas for Improvement")
                                        for weakness in sw.get('weaknesses', []):
                                            st.write(f"• {weakness}")
                                
                                # LLM Analysis
                                if st.session_state.permissions.get('access_llm'):
                                    llm_analysis = llm_service.generate_team_analysis({'name': selected_team}, [])
                                    st.markdown("#### 🤖 AI Insights")
                                    st.write(llm_analysis)
                            
                            else:
                                st.error(f"Analysis failed: {ml_analysis.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.error(f"Team analysis failed: {e}")
            else:
                st.warning("No teams found in database")
                
    except Exception as e:
        st.error(f"Error loading teams: {e}")

def advanced_analytics_page():
    """Advanced analytics page"""
    st.markdown("## 📊 Advanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["🏆 League Overview", "📈 Player Comparisons", "🎯 Draft Analysis"])
    
    with tab1:
        st.markdown("### 🏆 League Performance Overview")
        
        try:
            with db_manager.get_session() as session:
                # League statistics
                season = st.selectbox("Select Season", [2024, 2023, 2022, 2021], key="league_season")
                
                # Get league data
                query = f"""
                SELECT 
                    CASE 
                        WHEN team_1_name = t.name THEN 
                            CASE WHEN team_1_final_goals * 6 + team_1_final_behinds > team_2_final_goals * 6 + team_2_final_behinds THEN 1 ELSE 0 END
                        ELSE 
                            CASE WHEN team_2_final_goals * 6 + team_2_final_behinds > team_1_final_goals * 6 + team_1_final_behinds THEN 1 ELSE 0 END
                    END as wins,
                    CASE 
                        WHEN team_1_name = t.name THEN team_1_final_goals * 6 + team_1_final_behinds
                        ELSE team_2_final_goals * 6 + team_2_final_behinds
                    END as points_for,
                    CASE 
                        WHEN team_1_name = t.name THEN team_2_final_goals * 6 + team_2_final_behinds
                        ELSE team_1_final_goals * 6 + team_1_final_behinds
                    END as points_against,
                    t.name as team
                FROM matches m
                JOIN teams t ON (t.name = m.team_1_name OR t.name = m.team_2_name)
                WHERE m.year = :season AND t.is_active = true
                """
                
                result = session.execute(query, {'season': season}).fetchall()
                
                if result:
                    league_df = pd.DataFrame([dict(row._mapping) for row in result])
                    
                    # Calculate team standings
                    standings = league_df.groupby('team').agg({
                        'wins': 'sum',
                        'points_for': 'mean',
                        'points_against': 'mean'
                    }).reset_index()
                    
                    standings['matches'] = league_df.groupby('team').size().values
                    standings['win_pct'] = (standings['wins'] / standings['matches'] * 100).round(1)
                    standings['margin'] = (standings['points_for'] - standings['points_against']).round(1)
                    standings = standings.sort_values('win_pct', ascending=False).reset_index(drop=True)
                    standings.index += 1
                    
                    st.markdown(f"#### 🏆 {season} Ladder")
                    st.dataframe(standings[['team', 'matches', 'wins', 'win_pct', 'points_for', 'points_against', 'margin']], use_container_width=True)
                    
                    # Visualizations
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(standings.head(10), x='team', y='win_pct', 
                                   title='Top 10 Teams by Win Percentage')
                        fig.update_xaxis(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.scatter(standings, x='points_for', y='points_against', 
                                       text='team', title='Offensive vs Defensive Performance')
                        fig.update_traces(textposition="top center")
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.warning(f"No match data available for {season}")
                    
        except Exception as e:
            st.error(f"Error loading league analytics: {e}")
    
    with tab2:
        st.markdown("### 📈 Player Comparison Tool")
        st.info("Player comparison feature - Enterprise functionality")
        
        # Placeholder for player comparison
        st.markdown("""
        **Features:**
        - Side-by-side player statistics comparison
        - Radar charts for multi-dimensional analysis
        - Historical performance trends
        - Position-specific metrics
        """)
    
    with tab3:
        st.markdown("### 🎯 Draft Analysis")
        st.info("Draft analysis feature - Advanced analytics")
        
        # Placeholder for draft analysis
        st.markdown("""
        **Features:**
        - Young player development tracking
        - Draft pick value analysis
        - Potential assessment models
        - Club recruitment recommendations
        """)

def reports_page():
    """Reports generation page"""
    st.markdown("## 📋 Reports & Export")
    
    tab1, tab2, tab3 = st.tabs(["👤 Player Reports", "🏟️ Team Reports", "📊 League Reports"])
    
    with tab1:
        st.markdown("### 📄 Player Scouting Reports")
        
        # Player selection for report
        search_term = st.text_input("Search player for report", key="report_player_search")
        
        if search_term:
            try:
                with db_manager.get_session() as session:
                    query = """
                    SELECT id, first_name, last_name
                    FROM players 
                    WHERE LOWER(first_name || ' ' || last_name) LIKE LOWER(:search)
                    ORDER BY last_name, first_name
                    LIMIT 20
                    """
                    result = session.execute(query, {'search': f'%{search_term}%'}).fetchall()
                    
                    if result:
                        players_df = pd.DataFrame([dict(row._mapping) for row in result])
                        players_df['display_name'] = players_df['first_name'] + ' ' + players_df['last_name']
                        
                        selected_player = st.selectbox(
                            "Select Player for Report",
                            options=players_df['id'].tolist(),
                            format_func=lambda x: players_df[players_df['id'] == x]['display_name'].iloc[0]
                        )
                        
                        format_option = st.selectbox("Report Format", ["PDF", "Excel", "Word"])
                        
                        if st.button("Generate Player Report"):
                            with st.spinner("Generating report..."):
                                try:
                                    filename = report_generator.generate_player_scouting_report(
                                        selected_player, format_option.lower()
                                    )
                                    st.success(f"✅ Report generated: {filename}")
                                    
                                    # Download button
                                    with open(filename, "rb") as file:
                                        st.download_button(
                                            label="📥 Download Report",
                                            data=file.read(),
                                            file_name=filename.split('/')[-1],
                                            mime='application/octet-stream'
                                        )
                                except Exception as e:
                                    st.error(f"Report generation failed: {e}")
            except Exception as e:
                st.error(f"Error searching players: {e}")
    
    with tab2:
        st.markdown("### 📊 Team Analysis Reports")
        
        try:
            with db_manager.get_session() as session:
                teams_query = "SELECT DISTINCT name FROM teams WHERE is_active = true ORDER BY name"
                teams_result = session.execute(teams_query).fetchall()
                teams = [row[0] for row in teams_result]
                
                if teams:
                    selected_team = st.selectbox("Select Team for Report", teams, key="report_team")
                    season = st.selectbox("Season", [2024, 2023, 2022, 2021], key="report_season")
                    format_option = st.selectbox("Report Format", ["PDF", "Excel", "Word"], key="team_format")
                    
                    if st.button("Generate Team Report"):
                        with st.spinner("Generating team report..."):
                            try:
                                filename = report_generator.generate_team_analysis_report(
                                    selected_team, season, format_option.lower()
                                )
                                st.success(f"✅ Team report generated: {filename}")
                                
                                # Download button
                                with open(filename, "rb") as file:
                                    st.download_button(
                                        label="📥 Download Team Report",
                                        data=file.read(),
                                        file_name=filename.split('/')[-1],
                                        mime='application/octet-stream'
                                    )
                            except Exception as e:
                                st.error(f"Team report generation failed: {e}")
        except Exception as e:
            st.error(f"Error loading teams: {e}")
    
    with tab3:
        st.markdown("### 🏆 League Summary Reports")
        
        season = st.selectbox("Select Season for League Report", [2024, 2023, 2022, 2021], key="league_report_season")
        format_option = st.selectbox("Report Format", ["PDF", "Excel"], key="league_format")
        
        if st.button("Generate League Report"):
            with st.spinner("Generating league report..."):
                try:
                    filename = report_generator.generate_league_summary_report(season, format_option.lower())
                    st.success(f"✅ League report generated: {filename}")
                    
                    # Download button
                    with open(filename, "rb") as file:
                        st.download_button(
                            label="📥 Download League Report",
                            data=file.read(),
                            file_name=filename.split('/')[-1],
                            mime='application/octet-stream'
                        )
                except Exception as e:
                    st.error(f"League report generation failed: {e}")

def ai_chat_page():
    """AI chat interface page"""
    st.markdown("## 🤖 AI Chat Assistant")
    
    st.markdown("""
    Ask natural language questions about AFL players, teams, and statistics.
    The AI assistant can help with analysis and insights.
    """)
    
    # Chat interface
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about AFL players, teams, or statistics..."):
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = llm_service.chat_query(prompt)
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_messages = []
        st.rerun()

def data_management_page():
    """Data management page for analysts and admins"""
    st.markdown("## 💾 Data Management")
    
    tab1, tab2, tab3 = st.tabs(["📥 Data Ingestion", "📊 Data Status", "🔧 Data Operations"])
    
    with tab1:
        st.markdown("### 📥 Data Ingestion")
        
        st.info("Ingest AFL data from the comprehensive dataset repository")
        
        force_reload = st.checkbox("Force reload (overwrites existing data)")
        
        if st.button("🚀 Start Data Ingestion"):
            with st.spinner("Starting data ingestion process..."):
                try:
                    afl_data_service.ingest_all_data(force_reload)
                    st.success("✅ Data ingestion completed successfully!")
                except Exception as e:
                    st.error(f"❌ Data ingestion failed: {e}")
    
    with tab2:
        st.markdown("### 📊 Current Data Status")
        
        try:
            status = afl_data_service.get_ingestion_status()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Players", status.get('players', 0))
            with col2:
                st.metric("Performance Records", status.get('player_performance', 0))
            with col3:
                st.metric("Matches", status.get('matches', 0))
            with col4:
                st.metric("Teams", status.get('teams', 0))
            
            # Database connection test
            if st.button("🔍 Test Database Connection"):
                if db_manager.test_connection():
                    st.success("✅ Database connection successful")
                else:
                    st.error("❌ Database connection failed")
                    
        except Exception as e:
            st.error(f"Error getting data status: {e}")
    
    with tab3:
        st.markdown("### 🔧 Data Operations")
        
        st.warning("⚠️ These operations affect the entire system. Use with caution.")
        
        if st.button("🧹 Clean Temporary Files"):
            st.info("Temporary file cleanup completed")
        
        if st.button("🔄 Refresh ML Models"):
            with st.spinner("Refreshing ML models..."):
                try:
                    player_model.train_player_value_model(force_retrain=True)
                    st.success("✅ ML models refreshed")
                except Exception as e:
                    st.error(f"❌ Model refresh failed: {e}")

def user_management_page():
    """User management page for admins"""
    st.markdown("## 👥 User Management")
    
    tab1, tab2 = st.tabs(["📋 User List", "➕ Add User"])
    
    with tab1:
        st.markdown("### 📋 Current Users")
        
        try:
            users = auth_service.get_all_users()
            
            if users:
                users_df = pd.DataFrame(users)
                users_df['created_at'] = pd.to_datetime(users_df['created_at']).dt.strftime('%Y-%m-%d')
                users_df['last_login'] = pd.to_datetime(users_df['last_login']).dt.strftime('%Y-%m-%d %H:%M') if 'last_login' in users_df.columns else 'Never'
                
                st.dataframe(
                    users_df[['username', 'email', 'role', 'is_active', 'created_at', 'last_login']], 
                    use_container_width=True
                )
            else:
                st.info("No users found")
                
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with tab2:
        st.markdown("### ➕ Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", [UserRole.VIEWER, UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN])
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                if new_username and new_email and new_password:
                    try:
                        result = auth_service.create_user(new_username, new_email, new_password, new_role)
                        st.success(f"✅ User '{new_username}' created successfully!")
                    except Exception as e:
                        st.error(f"❌ User creation failed: {e}")
                else:
                    st.error("Please fill in all fields")

# Main application logic
def main():
    """Main application entry point"""
    if not ENTERPRISE_MODE:
        st.error("❌ Enterprise modules not available. Please check your installation.")
        return
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()