"""
Scout AI - Main Streamlit Dashboard
AFL Scouting Platform with Natural Language Queries, ML Analysis, and Interactive Visualizations
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any, List

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

# Import our modules
from data_collection.squiggle_scraper import SquiggleAPI
from data_collection.footywire_scraper import FootyWireScraper
from data_collection.data_processor import AFLDataProcessor
from analysis.ml_models import AFLPlayerAnalyzer
from nlp.query_processor import AFLQueryProcessor
from visualization.charts import AFLVisualizer
from reporting.report_generator import AFLReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Scout AI - AFL Scouting Platform",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for AFL-themed styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .main-header {
        background: linear-gradient(135deg, #003f7f 0%, #cc2e3a 50%, #ffcd00 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 3px solid #ffffff;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="3" fill="rgba(255,255,255,0.1)"/></svg>') repeat;
        animation: float 20s infinite linear;
        pointer-events: none;
    }
    
    @keyframes float {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-family: 'Roboto', sans-serif;
        font-weight: 900;
        font-size: 3rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        position: relative;
        z-index: 1;
    }
    
    .main-header p {
        color: white;
        text-align: center;
        margin: 1rem 0 0 0;
        font-family: 'Roboto', sans-serif;
        font-size: 1.2rem;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    .feature-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #003f7f;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #003f7f 0%, #0056b3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,63,127,0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
    }
    
    .query-box {
        background: linear-gradient(145deg, #e8f4f8 0%, #d1ecf1 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #003f7f;
        border-right: 5px solid #cc2e3a;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stats-highlight {
        background: linear-gradient(45deg, #ffcd00 0%, #ffd700 100%);
        color: #003f7f;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
        box-shadow: 0 3px 10px rgba(255,205,0,0.3);
    }
    
    .afl-ball {
        width: 60px;
        height: 40px;
        background: #8B4513;
        border-radius: 50%;
        margin: 0 auto;
        position: relative;
        box-shadow: inset 0 -10px 0 rgba(0,0,0,0.2);
    }
    
    .afl-ball::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 2px;
        height: 80%;
        background: white;
        border-radius: 1px;
    }
    
    .team-colors {
        display: flex;
        justify-content: center;
        gap: 3px;
        margin: 1rem 0;
    }
    
    .team-color {
        width: 15px;
        height: 15px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .welcome-section {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 2px solid #e3f2fd;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #003f7f 0%, #cc2e3a 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9ff 0%, #e3f2fd 100%);
    }
    
    /* AFL Team Color Indicators */
    .adelaide { background: #002B5C; }
    .brisbane { background: #8B2635; }
    .carlton { background: #0F1B3C; }
    .collingwood { background: #000000; }
    .essendon { background: #CC2E3A; }
    .fremantle { background: #2E0A4F; }
    .geelong { background: #1B5299; }
    .goldcoast { background: #FFC72C; }
    .gws { background: #F47920; }
    .hawthorn { background: #4A2C17; }
    .melbourne { background: #CC2E3A; }
    .north { background: #0F1B3C; }
    .portadelaide { background: #008A97; }
    .richmond { background: #FFCD00; }
    .stkilda { background: #CC2E3A; }
    .sydney { background: #CC2E3A; }
    .westcoast { background: #003F7F; }
    .bulldogs { background: #015BAE; }
    
</style>
""", unsafe_allow_html=True)

class ScoutAIDashboard:
    """
    Main Scout AI Dashboard class
    """
    
    def __init__(self):
        # Initialize components
        self.data_processor = AFLDataProcessor()
        self.player_analyzer = AFLPlayerAnalyzer()
        self.query_processor = AFLQueryProcessor()
        self.visualizer = AFLVisualizer()
        self.report_generator = AFLReportGenerator()
        
        # Initialize session state
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'player_data' not in st.session_state:
            st.session_state.player_data = pd.DataFrame()
        if 'team_data' not in st.session_state:
            st.session_state.team_data = pd.DataFrame()
        if 'games_data' not in st.session_state:
            st.session_state.games_data = pd.DataFrame()
    
    def create_welcome_section(self):
        """
        Create an AFL-themed welcome section with graphics and information
        """
        # Create AFL team colors display
        team_colors_html = """
        <div class="team-colors">
            <div class="team-color adelaide" title="Adelaide Crows"></div>
            <div class="team-color brisbane" title="Brisbane Lions"></div>
            <div class="team-color carlton" title="Carlton Blues"></div>
            <div class="team-color collingwood" title="Collingwood Magpies"></div>
            <div class="team-color essendon" title="Essendon Bombers"></div>
            <div class="team-color fremantle" title="Fremantle Dockers"></div>
            <div class="team-color geelong" title="Geelong Cats"></div>
            <div class="team-color goldcoast" title="Gold Coast Suns"></div>
            <div class="team-color gws" title="GWS Giants"></div>
            <div class="team-color hawthorn" title="Hawthorn Hawks"></div>
            <div class="team-color melbourne" title="Melbourne Demons"></div>
            <div class="team-color north" title="North Melbourne Kangaroos"></div>
            <div class="team-color portadelaide" title="Port Adelaide Power"></div>
            <div class="team-color richmond" title="Richmond Tigers"></div>
            <div class="team-color stkilda" title="St Kilda Saints"></div>
            <div class="team-color sydney" title="Sydney Swans"></div>
            <div class="team-color westcoast" title="West Coast Eagles"></div>
            <div class="team-color bulldogs" title="Western Bulldogs"></div>
        </div>
        """
        
        # Welcome section
        st.markdown(f"""
        <div class="welcome-section">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div class="afl-ball"></div>
                <h2 style="color: #003f7f; margin: 1rem 0; font-family: 'Roboto', sans-serif;">
                    Welcome to Scout AI
                </h2>
                <p style="color: #666; font-size: 1.1rem; line-height: 1.6;">
                    The most advanced AI-powered scouting platform for Australian Football League analysis.
                    Discover talent, analyze performance, and make data-driven decisions.
                </p>
                {team_colors_html}
                <p style="color: #888; font-size: 0.9rem; margin-top: 1rem;">
                    Covering all 18 AFL teams • VFL • SANFL • WAFL • Junior Competitions
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        if not st.session_state.data_loaded:
            self.create_feature_highlights()
        else:
            self.create_quick_stats_overview()
    
    def create_feature_highlights(self):
        """
        Create feature highlights for new users
        """
        st.markdown("### 🚀 Platform Capabilities")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4 style="color: #003f7f; margin-bottom: 1rem;">🗣️ Natural Language Queries</h4>
                <p style="color: #666; line-height: 1.5;">
                    Ask questions in plain English like "Find midfielders under 23 with high disposal counts" 
                    and get instant insights.
                </p>
                <div style="margin-top: 1rem; padding: 0.5rem; background: #f0f8ff; border-radius: 5px; font-size: 0.8rem; color: #003f7f;">
                    💡 Try: "Show me the best key forwards"
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4 style="color: #cc2e3a; margin-bottom: 1rem;">🤖 AI-Powered Analysis</h4>
                <p style="color: #666; line-height: 1.5;">
                    Machine learning models analyze player performance, predict potential, 
                    and identify playing styles automatically.
                </p>
                <div style="margin-top: 1rem; padding: 0.5rem; background: #fff0f0; border-radius: 5px; font-size: 0.8rem; color: #cc2e3a;">
                    📊 Performance prediction & clustering
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <h4 style="color: #ffcd00; margin-bottom: 1rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">📋 Professional Reports</h4>
                <p style="color: #666; line-height: 1.5;">
                    Generate publication-quality reports in PDF, Excel, and HTML formats 
                    with interactive charts and AI insights.
                </p>
                <div style="margin-top: 1rem; padding: 0.5rem; background: #fffaf0; border-radius: 5px; font-size: 0.8rem; color: #b8860b;">
                    📄 Player profiles & team analysis
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick start section
        st.markdown("### ⚡ Quick Start")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Load Sample Data", key="welcome_sample_data", help="Load sample AFL player data to explore the platform"):
                self.load_sample_data()
                st.rerun()
        
        with col2:
            if st.button("🔄 Fetch Live Data", key="welcome_live_data", help="Scrape latest AFL data from online sources"):
                with st.spinner("Fetching latest AFL data..."):
                    self.refresh_data()
                st.rerun()
    
    def create_quick_stats_overview(self):
        """
        Create quick stats overview when data is loaded
        """
        st.markdown("### 📊 Current Dataset Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin: 0; font-size: 2rem;">👥</h3>
                <h4 style="margin: 0.5rem 0;">Players</h4>
                <h2 style="margin: 0;">{}</h2>
            </div>
            """.format(len(st.session_state.player_data) if not st.session_state.player_data.empty else 0), 
            unsafe_allow_html=True)
        
        with col2:
            teams_count = st.session_state.player_data['Team'].nunique() if 'Team' in st.session_state.player_data.columns else 0
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin: 0; font-size: 2rem;">🏟️</h3>
                <h4 style="margin: 0.5rem 0;">Teams</h4>
                <h2 style="margin: 0;">{}</h2>
            </div>
            """.format(teams_count), unsafe_allow_html=True)
        
        with col3:
            positions_count = st.session_state.player_data['Position'].nunique() if 'Position' in st.session_state.player_data.columns else 0
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin: 0; font-size: 2rem;">⚽</h3>
                <h4 style="margin: 0.5rem 0;">Positions</h4>
                <h2 style="margin: 0;">{}</h2>
            </div>
            """.format(positions_count), unsafe_allow_html=True)
        
        with col4:
            avg_age = st.session_state.player_data['Age'].mean() if 'Age' in st.session_state.player_data.columns else 0
            st.markdown("""
            <div class="metric-card">
                <h3 style="margin: 0; font-size: 2rem;">📅</h3>
                <h4 style="margin: 0.5rem 0;">Avg Age</h4>
                <h2 style="margin: 0;">{:.1f}</h2>
            </div>
            """.format(avg_age), unsafe_allow_html=True)
        
        # Quick insights
        if not st.session_state.player_data.empty:
            st.markdown("""
            <div class="stats-highlight">
                ⚡ Dataset Ready! Explore using the tabs above or try natural language queries.
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """
        Main dashboard runner
        """
        # Enhanced AFL-themed header
        st.markdown("""
        <div class="main-header">
            <h1>🏈 Scout AI</h1>
            <p>AI-Powered AFL Scouting Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Welcome section with AFL graphics
        self.create_welcome_section()
        
        # Sidebar navigation
        self.create_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Natural Language Queries", 
            "📊 Player Analysis", 
            "🏟️ Team Analysis",
            "📈 Data Visualization",
            "📋 Reports"
        ])
        
        with tab1:
            self.natural_language_interface()
        
        with tab2:
            self.player_analysis_interface()
        
        with tab3:
            self.team_analysis_interface()
        
        with tab4:
            self.visualization_interface()
        
        with tab5:
            self.reporting_interface()
    
    def create_sidebar(self):
        """
        Create AFL-themed sidebar with data management and settings
        """
        # Enhanced sidebar header
        st.sidebar.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #003f7f 0%, #cc2e3a 100%); 
                   border-radius: 10px; margin-bottom: 1rem; color: white;">
            <h3 style="margin: 0; color: white;">🏈 Scout AI</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; opacity: 0.9;">Control Panel</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Data Management Section
        st.sidebar.markdown("### 📥 Data Management")
        
        # Data status with enhanced visuals
        if st.session_state.data_loaded:
            st.sidebar.markdown("""
            <div style="background: linear-gradient(145deg, #d4edda 0%, #c3e6cb 100%); 
                       padding: 1rem; border-radius: 8px; margin: 1rem 0; 
                       border-left: 4px solid #28a745;">
                <h4 style="color: #155724; margin: 0; font-size: 0.9rem;">✅ Data Status: Active</h4>
            </div>
            """, unsafe_allow_html=True)
            
            if not st.session_state.player_data.empty:
                players_count = len(st.session_state.player_data)
                teams_count = st.session_state.player_data['Team'].nunique() if 'Team' in st.session_state.player_data.columns else 0
                
                st.sidebar.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                    <span style="color: #666;">👥 Players:</span>
                    <strong style="color: #003f7f;">{players_count}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                    <span style="color: #666;">🏟️ Teams:</span>
                    <strong style="color: #cc2e3a;">{teams_count}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            if not st.session_state.games_data.empty:
                st.sidebar.markdown(f"""
                <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                    <span style="color: #666;">🏈 Games:</span>
                    <strong style="color: #ffcd00; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">{len(st.session_state.games_data)}</strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown("""
            <div style="background: linear-gradient(145deg, #f8d7da 0%, #f5c6cb 100%); 
                       padding: 1rem; border-radius: 8px; margin: 1rem 0; 
                       border-left: 4px solid #dc3545;">
                <h4 style="color: #721c24; margin: 0; font-size: 0.9rem;">⚠️ No Data Loaded</h4>
                <p style="color: #721c24; margin: 0.5rem 0 0 0; font-size: 0.8rem;">
                    Load data to start analyzing
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons with enhanced styling
        st.sidebar.markdown("---")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Refresh", key="sidebar_refresh", help="Scrape latest AFL data from sources"):
                with st.spinner("Fetching AFL data..."):
                    self.refresh_data()
        
        with col2:
            if st.button("🚀 Sample", key="sidebar_sample", help="Load sample data for demo"):
                self.load_sample_data()
        
        # ML Model settings
        st.sidebar.markdown("### 🤖 AI Models")
        
        if st.sidebar.button("🧠 Train Models", help="Train machine learning models on current data"):
            if not st.session_state.player_data.empty:
                with st.spinner("Training AI models..."):
                    self.train_models()
            else:
                st.sidebar.error("No player data available for training")
        
        # Quick analysis shortcuts
        st.sidebar.markdown("### ⚡ Quick Analysis")
        
        if not st.session_state.player_data.empty:
            # Top performers shortcut
            if st.sidebar.button("🏆 Top Performers", help="View top performing players"):
                st.session_state.quick_analysis = "top_performers"
            
            # Team overview shortcut
            if st.sidebar.button("🏟️ Team Overview", help="Quick team analysis"):
                st.session_state.quick_analysis = "team_overview"
            
            # Recent form shortcut
            if st.sidebar.button("📈 Performance Trends", help="Analyze performance trends"):
                st.session_state.quick_analysis = "trends"
        
        # Export options
        st.sidebar.markdown("### 📤 Export Data")
        
        export_col1, export_col2 = st.sidebar.columns(2)
        
        with export_col1:
            if st.button("📊 Excel", key="sidebar_excel", help="Export data to Excel"):
                self.export_data()
        
        with export_col2:
            if st.button("📄 PDF", key="sidebar_pdf", help="Generate PDF report"):
                if not st.session_state.player_data.empty:
                    st.sidebar.info("Select a player in the Player Analysis tab to generate PDF")
        
        # AFL-themed footer
        st.sidebar.markdown("---")
        st.sidebar.markdown("""
        <div style="text-align: center; padding: 1rem; color: #666; font-size: 0.8rem;">
            <div style="margin-bottom: 0.5rem;">🏈 AFL Scout AI</div>
            <div style="font-size: 0.7rem; opacity: 0.7;">
                Powered by Machine Learning<br/>
                Australian Football Analytics
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def natural_language_interface(self):
        """
        Enhanced natural language query interface
        """
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h2 style="color: #003f7f; font-family: 'Roboto', sans-serif; margin-bottom: 0.5rem;">
                🗣️ Ask Scout AI Anything
            </h2>
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
                Use natural language to discover AFL insights instantly
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # AFL-themed query examples with visual enhancement
        with st.expander("💡 Example Queries - Try These!", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #f0f8ff 0%, #e6f3ff 100%); 
                           padding: 1rem; border-radius: 10px; border-left: 4px solid #003f7f;">
                    <h4 style="color: #003f7f; margin-bottom: 1rem;">🎯 Player Discovery</h4>
                    <div style="font-size: 0.9rem; line-height: 1.5;">
                        • "Find midfielders under 23 with high disposal counts"<br/>
                        • "Show me the best key forwards with goal accuracy"<br/>
                        • "List young defenders with good marking ability"<br/>
                        • "Who are the top ruckmen for contested work?"
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #fff0f0 0%, #ffe6e6 100%); 
                           padding: 1rem; border-radius: 10px; border-left: 4px solid #cc2e3a;">
                    <h4 style="color: #cc2e3a; margin-bottom: 1rem;">⚖️ Team Comparisons</h4>
                    <div style="font-size: 0.9rem; line-height: 1.5;">
                        • "Compare Carlton vs Richmond for contested possessions"<br/>
                        • "Which team has the youngest midfielder group?"<br/>
                        • "Show Collingwood's forward line efficiency"<br/>
                        • "Analyze Melbourne's defensive structure"
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Quick query buttons
            st.markdown("### 🚀 Quick Queries")
            quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
            
            with quick_col1:
                if st.button("🏆 Top Scorers", help="Find the leading goal scorers"):
                    st.session_state.quick_query = "Show me the top 10 players for goals"
            
            with quick_col2:
                if st.button("🛡️ Best Defenders", help="Find top defensive players"):
                    st.session_state.quick_query = "Find defenders with high tackle and mark counts"
            
            with quick_col3:
                if st.button("⚡ Young Talent", help="Discover emerging young players"):
                    st.session_state.quick_query = "Find players under 22 with high potential"
            
            with quick_col4:
                if st.button("📊 All-Rounders", help="Find versatile players"):
                    st.session_state.quick_query = "Show midfielders with high disposals and tackles"
        
        # Query input with enhanced styling
        st.markdown('<div class="query-box">', unsafe_allow_html=True)
        
        # Check for quick queries
        default_query = ""
        if hasattr(st.session_state, 'quick_query') and st.session_state.quick_query:
            default_query = st.session_state.quick_query
            st.session_state.quick_query = ""  # Clear after use
        
        user_query = st.text_input(
            "🔍 Enter your scouting query:",
            value=default_query,
            placeholder="e.g., Find the best young midfielders with high disposal counts",
            help="Use natural language to describe what you're looking for"
        )
        
        # Add AFL-specific suggestions
        st.markdown("""
        <div style="margin-top: 1rem; font-size: 0.8rem; color: #666;">
            💡 <strong>Tips:</strong> Mention positions (midfielder, forward, defender), 
            age ranges (under 25), stats (high marks, good tackles), 
            or teams (Carlton, Richmond) for best results
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if user_query:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("🔍 Query Analysis")
            
            with col2:
                if st.button("🔍 Process Query", type="primary"):
                    self.process_natural_language_query(user_query)
            
            # Show query processing results
            if user_query and st.session_state.get('last_query') == user_query:
                self.display_query_results()
    
    def process_natural_language_query(self, query: str):
        """
        Process natural language query and show results
        """
        try:
            # Process the query
            query_result = self.query_processor.process_query(query)
            st.session_state.last_query = query
            st.session_state.query_result = query_result
            
            # Apply filters to data
            if not st.session_state.player_data.empty:
                filtered_data = self.query_processor.apply_filters_to_dataframe(
                    st.session_state.player_data, 
                    query_result['filters']
                )
                st.session_state.filtered_data = filtered_data
            
        except Exception as e:
            st.error(f"Error processing query: {e}")
    
    def display_query_results(self):
        """
        Display the results of natural language query processing
        """
        if 'query_result' not in st.session_state:
            return
        
        query_result = st.session_state.query_result
        
        # Query analysis
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Query Type", query_result['query_type'].title())
        
        with col2:
            st.metric("Confidence", f"{query_result['confidence']:.0%}")
        
        with col3:
            filters_count = sum(1 for f in query_result['filters'].values() if f)
            st.metric("Filters Applied", filters_count)
        
        # Filters breakdown
        st.subheader("🎯 Extracted Filters")
        
        filters = query_result['filters']
        filter_cols = st.columns(4)
        
        with filter_cols[0]:
            if filters['positions']:
                st.info(f"**Positions:** {', '.join(filters['positions'])}")
            if filters['teams']:
                st.info(f"**Teams:** {', '.join(filters['teams'])}")
        
        with filter_cols[1]:
            if filters['stats']:
                st.info(f"**Stats:** {', '.join(filters['stats'])}")
            if filters['leagues']:
                st.info(f"**Leagues:** {', '.join(filters['leagues'])}")
        
        with filter_cols[2]:
            min_age, max_age = filters['age_range']
            if min_age or max_age:
                age_str = f"{min_age or '?'} - {max_age or '?'}"
                st.info(f"**Age Range:** {age_str}")
        
        with filter_cols[3]:
            if filters['sort_by']:
                st.info(f"**Sort By:** {filters['sort_by']}")
            if filters['limit']:
                st.info(f"**Limit:** {filters['limit']}")
        
        # Enhanced results display
        if 'filtered_data' in st.session_state and not st.session_state.filtered_data.empty:
            result_data = st.session_state.filtered_data
            
            # Success header with AFL styling
            st.markdown("""
            <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                       padding: 1.5rem; border-radius: 15px; margin: 2rem 0; 
                       border-left: 5px solid #28a745; text-align: center;">
                <h3 style="color: #155724; margin: 0;">🎯 Query Results Found!</h3>
                <p style="color: #155724; margin: 0.5rem 0 0 0; opacity: 0.8;">
                    Your AFL scouting search returned valuable insights
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced summary metrics with AFL theming
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">👥</h3>
                    <h4 style="margin: 0.5rem 0;">Players Found</h4>
                    <h2 style="margin: 0;">{}</h2>
                </div>
                """.format(len(result_data)), unsafe_allow_html=True)
            
            with col2:
                teams_count = result_data['Team'].nunique() if 'Team' in result_data.columns else 0
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">🏟️</h3>
                    <h4 style="margin: 0.5rem 0;">Teams</h4>
                    <h2 style="margin: 0;">{}</h2>
                </div>
                """.format(teams_count), unsafe_allow_html=True)
            
            with col3:
                positions_count = result_data['Position'].nunique() if 'Position' in result_data.columns else 0
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">⚽</h3>
                    <h4 style="margin: 0.5rem 0;">Positions</h4>
                    <h2 style="margin: 0;">{}</h2>
                </div>
                """.format(positions_count), unsafe_allow_html=True)
            
            with col4:
                avg_age = result_data['Age'].mean() if 'Age' in result_data.columns else 0
                st.markdown("""
                <div class="metric-card">
                    <h3 style="margin: 0; font-size: 2rem;">📅</h3>
                    <h4 style="margin: 0.5rem 0;">Avg Age</h4>
                    <h2 style="margin: 0;">{:.1f}</h2>
                </div>
                """.format(avg_age), unsafe_allow_html=True)
            
            # Enhanced data table with action buttons
            st.markdown("### 📋 Player Details")
            
            # Add action buttons above the table
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("📊 Generate Report", key="query_report"):
                    st.info("Navigate to the Reports tab to generate detailed reports for these players")
            
            with action_col2:
                if st.button("📈 Visualize Data", key="query_viz"):
                    st.info("Check out the Data Visualization tab for more chart options")
            
            with action_col3:
                if st.button("🔍 Analyze Further", key="query_analyze"):
                    st.info("Use the Player Analysis tab to dive deeper into individual players")
            
            # Enhanced data table
            st.dataframe(
                result_data.head(20),
                use_container_width=True,
                height=400
            )
            
            # AFL-themed quick visualization
            if len(result_data) > 1:
                st.markdown("### 📈 Quick Insights")
                
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    if 'Position' in result_data.columns:
                        st.markdown("#### 🎯 Position Breakdown")
                        position_counts = result_data['Position'].value_counts()
                        st.bar_chart(position_counts)
                        
                        # Add position insights
                        top_position = position_counts.index[0]
                        st.markdown(f"""
                        <div style="background: #f0f8ff; padding: 0.5rem; border-radius: 5px; margin-top: 0.5rem;">
                            <small style="color: #003f7f;">
                                💡 Most common: <strong>{top_position}</strong> ({position_counts.iloc[0]} players)
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                
                with viz_col2:
                    if 'Team' in result_data.columns:
                        st.markdown("#### 🏟️ Team Distribution")
                        team_counts = result_data['Team'].value_counts().head(8)
                        st.bar_chart(team_counts)
                        
                        # Add team insights
                        top_team = team_counts.index[0]
                        st.markdown(f"""
                        <div style="background: #fff0f0; padding: 0.5rem; border-radius: 5px; margin-top: 0.5rem;">
                            <small style="color: #cc2e3a;">
                                🏆 Leading team: <strong>{top_team}</strong> ({team_counts.iloc[0]} players)
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # Enhanced "no results" message
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); 
                       padding: 2rem; border-radius: 15px; margin: 2rem 0; 
                       border-left: 5px solid #dc3545; text-align: center;">
                <h3 style="color: #721c24; margin: 0;">🔍 No Players Found</h3>
                <p style="color: #721c24; margin: 1rem 0; line-height: 1.5;">
                    No players matched your search criteria. Try adjusting your query or being less specific.
                </p>
                <div style="background: rgba(255,255,255,0.3); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                    <h4 style="color: #721c24; margin: 0; font-size: 0.9rem;">💡 Suggestions:</h4>
                    <ul style="color: #721c24; text-align: left; margin: 0.5rem 0; font-size: 0.85rem;">
                        <li>Try broader age ranges (e.g., "under 25" instead of "under 20")</li>
                        <li>Use general terms (e.g., "good defenders" instead of specific stats)</li>
                        <li>Check if player names or team names are spelled correctly</li>
                        <li>Consider using the quick query buttons above</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def player_analysis_interface(self):
        """
        Player analysis interface
        """
        st.header("🏃‍♂️ Player Analysis")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available. Please load data first.")
            return
        
        # Player selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_player = st.selectbox(
                "Select Player for Analysis:",
                options=st.session_state.player_data['Player'].unique() if 'Player' in st.session_state.player_data.columns else [],
                help="Choose a player to view detailed analysis"
            )
        
        with col2:
            analysis_type = st.selectbox(
                "Analysis Type:",
                ["Performance Overview", "Potential Analysis", "Team Fit", "Comparison"]
            )
        
        if selected_player:
            player_data = st.session_state.player_data[
                st.session_state.player_data['Player'] == selected_player
            ].iloc[0].to_dict()
            
            if analysis_type == "Performance Overview":
                self.show_player_performance(player_data)
            elif analysis_type == "Potential Analysis":
                self.show_player_potential(player_data)
            elif analysis_type == "Team Fit":
                self.show_team_fit_analysis(player_data)
            elif analysis_type == "Comparison":
                self.show_player_comparison(selected_player)
    
    def show_player_performance(self, player_data: Dict[str, Any]):
        """
        Show detailed player performance analysis
        """
        st.subheader(f"📊 Performance Analysis: {player_data.get('Player', 'Unknown')}")
        
        # Basic info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Team", player_data.get('Team', 'N/A'))
        with col2:
            st.metric("Position", player_data.get('Position', 'N/A'))
        with col3:
            st.metric("Age", player_data.get('Age', 'N/A'))
        with col4:
            st.metric("Experience", "5 years")  # Placeholder
        
        # Performance metrics
        st.subheader("🎯 Key Statistics")
        
        metric_cols = st.columns(5)
        metrics = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Contested Possessions']
        
        for i, metric in enumerate(metrics):
            with metric_cols[i]:
                value = player_data.get(metric, 0)
                st.metric(metric, f"{value:.1f}" if isinstance(value, float) else str(value))
        
        # Radar chart
        if any(metric in player_data for metric in metrics):
            st.subheader("🔄 Performance Radar")
            radar_fig = self.visualizer.create_player_radar(
                player_data, 
                metrics, 
                title=f"{player_data.get('Player', 'Player')} Performance"
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        
        # Strengths and weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💪 Strengths")
            strengths = self.analyze_player_strengths(player_data)
            for strength in strengths:
                st.success(f"✅ {strength}")
        
        with col2:
            st.subheader("📈 Areas for Improvement")
            improvements = self.analyze_player_improvements(player_data)
            for improvement in improvements:
                st.info(f"🎯 {improvement}")
    
    def show_player_potential(self, player_data: Dict[str, Any]):
        """
        Show player potential analysis
        """
        st.subheader(f"🚀 Potential Analysis: {player_data.get('Player', 'Unknown')}")
        
        # Create a single-row DataFrame for ML analysis
        player_df = pd.DataFrame([player_data])
        
        # Predict potential using ML model
        potential_df = self.player_analyzer.predict_player_potential(player_df)
        
        if not potential_df.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                current_perf = potential_df.iloc[0].get('Predicted_Performance', 0)
                st.metric("Current Performance Level", f"{current_perf:.1f}")
            
            with col2:
                potential = potential_df.iloc[0].get('Potential_Rating', 0)
                st.metric("Potential Rating", f"{potential:.1f}")
            
            with col3:
                development = potential_df.iloc[0].get('Development_Factor', 1.0)
                st.metric("Development Factor", f"{development:.2f}x")
            
            # Age curve visualization
            age = player_data.get('Age', 25)
            if isinstance(age, (int, float)):
                st.subheader("📈 Career Projection")
                
                ages = np.arange(18, 35)
                performance_curve = []
                
                for a in ages:
                    if a < 26:
                        factor = 1.2 - 0.02 * (26 - a)
                    else:
                        factor = 1.0 - 0.03 * (a - 26)
                    performance_curve.append(current_perf * factor)
                
                curve_df = pd.DataFrame({
                    'Age': ages,
                    'Projected_Performance': performance_curve
                })
                
                st.line_chart(curve_df.set_index('Age'))
                st.caption("Projected performance curve based on age and current ability")
    
    def team_analysis_interface(self):
        """
        Team analysis interface
        """
        st.header("🏟️ Team Analysis")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available. Please load data first.")
            return
        
        # Team selection
        if 'Team' in st.session_state.player_data.columns:
            teams = st.session_state.player_data['Team'].unique()
            selected_team = st.selectbox("Select Team:", teams)
            
            if selected_team:
                team_data = st.session_state.player_data[
                    st.session_state.player_data['Team'] == selected_team
                ]
                
                self.show_team_analysis(team_data, selected_team)
        else:
            st.error("No team data available")
    
    def show_team_analysis(self, team_data: pd.DataFrame, team_name: str):
        """
        Show comprehensive team analysis
        """
        st.subheader(f"📊 Team Analysis: {team_name}")
        
        # Team overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Squad Size", len(team_data))
        with col2:
            avg_age = team_data['Age'].mean() if 'Age' in team_data.columns else 0
            st.metric("Average Age", f"{avg_age:.1f}")
        with col3:
            if 'Position' in team_data.columns:
                st.metric("Positions Covered", team_data['Position'].nunique())
        with col4:
            avg_disposals = team_data['Disposals'].mean() if 'Disposals' in team_data.columns else 0
            st.metric("Avg Disposals", f"{avg_disposals:.1f}")
        
        # Position breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Position' in team_data.columns:
                st.subheader("👥 Squad Composition")
                position_counts = team_data['Position'].value_counts()
                st.bar_chart(position_counts)
        
        with col2:
            if 'Age' in team_data.columns:
                st.subheader("📅 Age Distribution")
                age_bins = pd.cut(team_data['Age'], bins=[18, 23, 28, 35], labels=['Young (18-23)', 'Prime (24-28)', 'Veteran (29+)'])
                age_dist = age_bins.value_counts()
                st.bar_chart(age_dist)
        
        # Top performers
        st.subheader("⭐ Top Performers")
        
        metrics = ['Disposals', 'Marks', 'Tackles', 'Goals']
        metric_cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            if metric in team_data.columns:
                with metric_cols[i]:
                    top_player = team_data.nlargest(1, metric)
                    if not top_player.empty:
                        player_name = top_player.iloc[0].get('Player', 'Unknown')
                        value = top_player.iloc[0].get(metric, 0)
                        st.metric(
                            f"Top {metric}",
                            f"{player_name}\n{value:.1f}",
                            help=f"Leader in {metric}"
                        )
        
        # Team comparison chart
        if len(metrics) > 0:
            st.subheader("📊 Team vs League Average")
            team_avg = team_data[metrics].mean()
            
            # Create comparison chart
            comparison_fig = self.visualizer.create_team_comparison(
                st.session_state.player_data, 
                'Disposals',  # Example metric
                [team_name]
            )
            st.plotly_chart(comparison_fig, use_container_width=True)
    
    def visualization_interface(self):
        """
        Data visualization interface
        """
        st.header("📈 Data Visualization")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available. Please load data first.")
            return
        
        # Visualization type selection
        viz_type = st.selectbox(
            "Select Visualization Type:",
            [
                "Player Scatter Plot",
                "Position Distribution",
                "Team Comparison",
                "Correlation Heatmap",
                "Age vs Performance",
                "Player Rankings"
            ]
        )
        
        # Configuration based on visualization type
        if viz_type == "Player Scatter Plot":
            self.create_scatter_plot_interface()
        elif viz_type == "Position Distribution":
            self.create_position_distribution_interface()
        elif viz_type == "Team Comparison":
            self.create_team_comparison_interface()
        elif viz_type == "Correlation Heatmap":
            self.create_heatmap_interface()
        elif viz_type == "Age vs Performance":
            self.create_age_performance_interface()
        elif viz_type == "Player Rankings":
            self.create_rankings_interface()
    
    def create_scatter_plot_interface(self):
        """
        Create scatter plot configuration interface
        """
        st.subheader("🔸 Player Scatter Plot")
        
        numeric_columns = self.get_numeric_columns()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_metric = st.selectbox("X-Axis Metric:", numeric_columns, index=0)
        with col2:
            y_metric = st.selectbox("Y-Axis Metric:", numeric_columns, index=1 if len(numeric_columns) > 1 else 0)
        with col3:
            color_by = st.selectbox("Color By:", ['Position', 'Team', 'Age'], index=0)
        
        if x_metric and y_metric:
            scatter_fig = self.visualizer.create_player_scatter(
                st.session_state.player_data,
                x_metric,
                y_metric,
                color_by
            )
            st.plotly_chart(scatter_fig, use_container_width=True)
    
    def reporting_interface(self):
        """
        Report generation interface
        """
        st.header("📋 Report Generation")
        
        report_type = st.selectbox(
            "Select Report Type:",
            ["Player Profile", "Team Analysis", "Scouting Shortlist", "Custom Report"]
        )
        
        if report_type == "Player Profile":
            self.generate_player_report_interface()
        elif report_type == "Team Analysis":
            self.generate_team_report_interface()
        elif report_type == "Scouting Shortlist":
            self.generate_shortlist_interface()
        elif report_type == "Custom Report":
            self.generate_custom_report_interface()
    
    def generate_player_report_interface(self):
        """
        Interface for generating player profile reports
        """
        st.subheader("👤 Player Profile Report")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available.")
            return
        
        # Player selection
        player_name = st.selectbox(
            "Select Player:",
            st.session_state.player_data['Player'].unique() if 'Player' in st.session_state.player_data.columns else []
        )
        
        # Report format
        format_type = st.selectbox("Report Format:", ["PDF", "Excel", "HTML"])
        
        if st.button("📄 Generate Report") and player_name:
            with st.spinner("Generating player profile report..."):
                try:
                    player_data = st.session_state.player_data[
                        st.session_state.player_data['Player'] == player_name
                    ].iloc[0].to_dict()
                    
                    if format_type == "PDF":
                        # Generate charts for the report
                        charts = {
                            'radar': self.visualizer.create_player_radar(player_data),
                            'performance': self.visualizer.create_age_performance_scatter(
                                st.session_state.player_data[st.session_state.player_data['Player'] == player_name]
                            )
                        }
                        
                        report_path = self.report_generator.generate_player_profile_pdf(
                            player_data, charts
                        )
                        st.success(f"✅ PDF report generated: {report_path}")
                        
                        # Provide download link
                        with open(report_path, "rb") as file:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=file.read(),
                                file_name=f"{player_name.replace(' ', '_')}_profile.pdf",
                                mime="application/pdf"
                            )
                    
                    elif format_type == "HTML":
                        report_data = {
                            "Player Information": player_data,
                            "Performance Metrics": {
                                k: v for k, v in player_data.items() 
                                if k in ['Disposals', 'Marks', 'Tackles', 'Goals']
                            }
                        }
                        
                        report_path = self.report_generator.generate_web_report(report_data)
                        st.success(f"✅ HTML report generated: {report_path}")
                        
                        # Show preview
                        with open(report_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        st.components.v1.html(html_content, height=600, scrolling=True)
                
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    def refresh_data(self):
        """
        Refresh data from all sources
        """
        try:
            # Squiggle API data
            squiggle_api = SquiggleAPI()
            current_year = pd.Timestamp.now().year
            
            games = squiggle_api.get_games(year=current_year)
            ladder = squiggle_api.get_ladder(year=current_year)
            teams = squiggle_api.get_teams()
            
            # Process Squiggle data
            squiggle_processed = self.data_processor.process_squiggle_data(games, ladder, pd.DataFrame())
            
            # FootyWire data (with error handling)
            try:
                footywire_scraper = FootyWireScraper(headless=True)
                player_stats = footywire_scraper.get_player_stats()
                team_stats = footywire_scraper.get_team_stats()
                footywire_scraper.close_driver()
                
                footywire_processed = self.data_processor.process_footywire_data(player_stats, team_stats)
            except Exception as e:
                logger.warning(f"FootyWire scraping failed: {e}")
                footywire_processed = {}
            
            # Combine and save data
            all_data = {**squiggle_processed, **footywire_processed}
            self.data_processor.save_to_database(all_data)
            
            # Update session state
            if 'players' in all_data:
                st.session_state.player_data = all_data['players']
            if 'teams' in all_data:
                st.session_state.team_data = all_data['teams']
            if 'games' in all_data:
                st.session_state.games_data = all_data['games']
            
            st.session_state.data_loaded = True
            st.success("✅ Data refreshed successfully!")
            
        except Exception as e:
            st.error(f"Error refreshing data: {e}")
            logger.error(f"Data refresh error: {e}")
    
    def load_sample_data(self):
        """
        Load sample data for demonstration
        """
        try:
            # Create sample player data
            sample_players = pd.DataFrame({
                'Player': ['Marcus Bontempelli', 'Clayton Oliver', 'Lachie Neale', 'Patrick Cripps', 'Max Gawn'],
                'Team': ['Western Bulldogs', 'Melbourne Demons', 'Brisbane Lions', 'Carlton Blues', 'Melbourne Demons'],
                'Position': ['Midfielder', 'Midfielder', 'Midfielder', 'Midfielder', 'Ruck'],
                'Age': [28, 26, 30, 28, 32],
                'Disposals': [28.5, 31.2, 29.8, 27.1, 15.2],
                'Marks': [6.2, 4.8, 5.1, 5.9, 8.1],
                'Tackles': [4.8, 6.2, 5.5, 5.1, 3.2],
                'Goals': [0.8, 0.5, 1.2, 0.9, 1.1],
                'Contested Possessions': [12.1, 14.2, 11.8, 13.5, 8.9],
                'Mark_Disposal_Ratio': [0.22, 0.15, 0.17, 0.22, 0.53],
                'Contested_Rate': [0.42, 0.46, 0.40, 0.50, 0.59],
                'Goal_Accuracy': [0.65, 0.58, 0.72, 0.61, 0.69]
            })
            
            # Add derived metrics
            sample_players = self.data_processor.add_derived_metrics(sample_players)
            
            st.session_state.player_data = sample_players
            st.session_state.data_loaded = True
            st.success("✅ Sample data loaded successfully!")
            
        except Exception as e:
            st.error(f"Error loading sample data: {e}")
    
    def get_numeric_columns(self) -> List[str]:
        """
        Get numeric columns from player data
        """
        if st.session_state.player_data.empty:
            return []
        
        numeric_cols = st.session_state.player_data.select_dtypes(include=[np.number]).columns.tolist()
        return [col for col in numeric_cols if col not in ['Age']]  # Exclude Age from metrics
    
    def analyze_player_strengths(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Analyze player strengths
        """
        strengths = []
        
        if player_data.get('Disposals', 0) > 25:
            strengths.append("High ball winning ability")
        if player_data.get('Marks', 0) > 6:
            strengths.append("Strong marking")
        if player_data.get('Tackles', 0) > 5:
            strengths.append("Excellent defensive pressure")
        if player_data.get('Goal_Accuracy', 0) > 0.6:
            strengths.append("Accurate goal kicking")
        
        return strengths if strengths else ["Solid all-around performer"]
    
    def analyze_player_improvements(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Analyze areas for improvement
        """
        improvements = []
        
        if player_data.get('Goal_Accuracy', 1.0) < 0.5:
            improvements.append("Goal kicking accuracy")
        if player_data.get('Contested_Rate', 1.0) < 0.3:
            improvements.append("Contested ball winning")
        if player_data.get('Tackles', 0) < 3:
            improvements.append("Defensive pressure")
        
        return improvements if improvements else ["Continue current development path"]
    
    def train_models(self):
        """
        Train ML models with current data
        """
        try:
            if not st.session_state.player_data.empty:
                result = self.player_analyzer.train_performance_model(
                    st.session_state.player_data, 
                    'Disposals'
                )
                
                if 'error' not in result:
                    st.success("✅ ML model trained successfully!")
                    st.json(result)
                else:
                    st.error(f"Training failed: {result['error']}")
            
        except Exception as e:
            st.error(f"Error training models: {e}")
    
    def export_data(self):
        """
        Export all data to Excel
        """
        try:
            if not st.session_state.player_data.empty:
                output_path = self.report_generator.generate_scouting_shortlist_excel(
                    st.session_state.player_data,
                    {'exported_at': pd.Timestamp.now().isoformat()},
                    'scout_ai_export.xlsx'
                )
                st.success(f"✅ Data exported to: {output_path}")
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    def show_team_fit_analysis(self, player_data: Dict[str, Any]):
        """
        Show team fit analysis for a player
        """
        st.subheader(f"🎯 Team Fit Analysis: {player_data.get('Player', 'Unknown')}")
        
        # Team style options
        team_styles = ["possession_based", "pressure_based", "attacking", "defensive"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_style = st.selectbox("Team Style:", team_styles)
        
        with col2:
            if st.button("🔍 Analyze Fit"):
                # Create single-row DataFrame for analysis
                player_df = pd.DataFrame([player_data])
                
                # Analyze team fit
                fit_analysis = self.player_analyzer.evaluate_team_fit(player_df, selected_style)
                
                if not fit_analysis.empty:
                    fit_score = fit_analysis.iloc[0].get(f'{selected_style}_fit_score', 0)
                    
                    st.metric("Team Fit Score", f"{fit_score:.2f}/1.0")
                    
                    # Provide recommendations
                    if fit_score > 0.7:
                        st.success("🎯 Excellent fit for this team style!")
                    elif fit_score > 0.5:
                        st.info("👍 Good fit with some development needed")
                    else:
                        st.warning("⚠️ May not suit this team style")
        
        # Show fit explanations
        st.subheader("📋 Team Style Requirements")
        
        style_descriptions = {
            "possession_based": "Teams that emphasize ball retention, uncontested possessions, and controlled build-up play",
            "pressure_based": "Teams that focus on high-intensity defensive pressure, tackling, and contested ball work",
            "attacking": "Teams that prioritize forward movement, goal scoring, and offensive efficiency",
            "defensive": "Teams that emphasize defensive structure, contested marks, and defensive pressure"
        }
        
        if selected_style in style_descriptions:
            st.info(style_descriptions[selected_style])
    
    def show_player_comparison(self, selected_player: str):
        """
        Show player comparison interface
        """
        st.subheader(f"⚖️ Player Comparison: {selected_player}")
        
        # Select comparison player
        other_players = st.session_state.player_data[
            st.session_state.player_data['Player'] != selected_player
        ]['Player'].unique()
        
        comparison_player = st.selectbox("Compare with:", other_players)
        
        if comparison_player:
            # Get both player data
            player1_data = st.session_state.player_data[
                st.session_state.player_data['Player'] == selected_player
            ].iloc[0]
            
            player2_data = st.session_state.player_data[
                st.session_state.player_data['Player'] == comparison_player
            ].iloc[0]
            
            # Comparison metrics
            metrics = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Contested Possessions']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 {selected_player}")
                for metric in metrics:
                    if metric in player1_data:
                        st.metric(metric, f"{player1_data[metric]:.1f}")
            
            with col2:
                st.subheader(f"📊 {comparison_player}")
                for metric in metrics:
                    if metric in player2_data:
                        delta = player2_data[metric] - player1_data[metric]
                        st.metric(metric, f"{player2_data[metric]:.1f}", delta=f"{delta:+.1f}")
            
            # Comparison chart
            comparison_df = pd.DataFrame({
                'Metric': metrics,
                selected_player: [player1_data.get(m, 0) for m in metrics],
                comparison_player: [player2_data.get(m, 0) for m in metrics]
            })
            
            st.subheader("📈 Side-by-Side Comparison")
            st.bar_chart(comparison_df.set_index('Metric'))
    
    def create_position_distribution_interface(self):
        """
        Create position distribution visualization interface
        """
        st.subheader("📦 Position Distribution")
        
        numeric_columns = self.get_numeric_columns()
        selected_metric = st.selectbox("Select Metric:", numeric_columns)
        
        if selected_metric:
            fig = self.visualizer.create_position_distribution(
                st.session_state.player_data, selected_metric
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_team_comparison_interface(self):
        """
        Create team comparison visualization interface
        """
        st.subheader("🏟️ Team Comparison")
        
        numeric_columns = self.get_numeric_columns()
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metric = st.selectbox("Select Metric:", numeric_columns)
        
        with col2:
            if 'Team' in st.session_state.player_data.columns:
                all_teams = st.session_state.player_data['Team'].unique()
                selected_teams = st.multiselect("Select Teams (optional):", all_teams)
        
        if selected_metric:
            fig = self.visualizer.create_team_comparison(
                st.session_state.player_data, 
                selected_metric, 
                selected_teams if selected_teams else None
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_heatmap_interface(self):
        """
        Create correlation heatmap interface
        """
        st.subheader("🔥 Correlation Heatmap")
        
        numeric_columns = self.get_numeric_columns()
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metrics = st.multiselect(
                "Select Metrics:", 
                numeric_columns, 
                default=numeric_columns[:5] if len(numeric_columns) >= 5 else numeric_columns
            )
        
        with col2:
            heatmap_type = st.selectbox("Heatmap Type:", ["Correlation", "Team Performance"])
        
        if selected_metrics and len(selected_metrics) >= 2:
            correlation = heatmap_type == "Correlation"
            fig = self.visualizer.create_heatmap(
                st.session_state.player_data, 
                selected_metrics, 
                correlation=correlation
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_age_performance_interface(self):
        """
        Create age vs performance visualization interface
        """
        st.subheader("📅 Age vs Performance")
        
        numeric_columns = self.get_numeric_columns()
        selected_metric = st.selectbox("Performance Metric:", numeric_columns)
        
        if selected_metric:
            fig = self.visualizer.create_age_performance_scatter(
                st.session_state.player_data, selected_metric
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_rankings_interface(self):
        """
        Create player rankings interface
        """
        st.subheader("🏆 Player Rankings")
        
        numeric_columns = self.get_numeric_columns()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_metric = st.selectbox("Ranking Metric:", numeric_columns)
        
        with col2:
            if 'Position' in st.session_state.player_data.columns:
                positions = ['All'] + list(st.session_state.player_data['Position'].unique())
                selected_position = st.selectbox("Filter by Position:", positions)
        
        with col3:
            top_n = st.slider("Number of Players:", 5, 50, 20)
        
        if selected_metric:
            position_filter = None if selected_position == 'All' else selected_position
            
            fig = self.visualizer.create_ranking_chart(
                st.session_state.player_data, 
                selected_metric,
                position_filter,
                top_n
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def generate_team_report_interface(self):
        """
        Interface for generating team analysis reports
        """
        st.subheader("🏟️ Team Analysis Report")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available.")
            return
        
        if 'Team' not in st.session_state.player_data.columns:
            st.error("No team data available.")
            return
        
        # Team selection
        teams = st.session_state.player_data['Team'].unique()
        selected_team = st.selectbox("Select Team:", teams)
        
        # Report format
        format_type = st.selectbox("Report Format:", ["PDF", "Excel", "HTML"])
        
        if st.button("📄 Generate Team Report") and selected_team:
            with st.spinner("Generating team analysis report..."):
                try:
                    team_data = st.session_state.player_data[
                        st.session_state.player_data['Team'] == selected_team
                    ]
                    
                    if format_type == "PDF":
                        # Generate charts for the report
                        charts = {
                            'position_dist': self.visualizer.create_position_distribution(team_data, 'Disposals'),
                            'age_performance': self.visualizer.create_age_performance_scatter(team_data)
                        }
                        
                        report_path = self.report_generator.generate_team_analysis_pdf(
                            team_data, selected_team, charts
                        )
                        st.success(f"✅ PDF report generated: {report_path}")
                        
                        # Provide download link
                        with open(report_path, "rb") as file:
                            st.download_button(
                                label="📥 Download PDF Report",
                                data=file.read(),
                                file_name=f"{selected_team.replace(' ', '_')}_analysis.pdf",
                                mime="application/pdf"
                            )
                    
                    elif format_type == "Excel":
                        report_path = self.report_generator.generate_scouting_shortlist_excel(
                            team_data,
                            {'team': selected_team, 'generated_at': pd.Timestamp.now().isoformat()},
                            f"{selected_team.replace(' ', '_')}_analysis.xlsx"
                        )
                        st.success(f"✅ Excel report generated: {report_path}")
                
                except Exception as e:
                    st.error(f"Error generating team report: {e}")
    
    def generate_shortlist_interface(self):
        """
        Interface for generating scouting shortlists
        """
        st.subheader("📋 Scouting Shortlist")
        
        if st.session_state.player_data.empty:
            st.warning("No player data available.")
            return
        
        # Shortlist criteria
        st.subheader("🎯 Define Shortlist Criteria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Position filter
            if 'Position' in st.session_state.player_data.columns:
                positions = ['All'] + list(st.session_state.player_data['Position'].unique())
                selected_positions = st.multiselect("Positions:", positions, default=['All'])
            
            # Age filter
            if 'Age' in st.session_state.player_data.columns:
                age_range = st.slider(
                    "Age Range:", 
                    int(st.session_state.player_data['Age'].min()), 
                    int(st.session_state.player_data['Age'].max()),
                    (18, 35)
                )
        
        with col2:
            # Performance thresholds
            numeric_columns = self.get_numeric_columns()
            selected_metric = st.selectbox("Primary Metric:", numeric_columns)
            
            if selected_metric:
                metric_threshold = st.slider(
                    f"Minimum {selected_metric}:",
                    float(st.session_state.player_data[selected_metric].min()),
                    float(st.session_state.player_data[selected_metric].max()),
                    float(st.session_state.player_data[selected_metric].mean())
                )
        
        # Generate shortlist
        if st.button("🔍 Generate Shortlist"):
            # Apply filters
            filtered_data = st.session_state.player_data.copy()
            
            # Position filter
            if 'All' not in selected_positions and 'Position' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Position'].isin(selected_positions)]
            
            # Age filter
            if 'Age' in filtered_data.columns:
                filtered_data = filtered_data[
                    (filtered_data['Age'] >= age_range[0]) & 
                    (filtered_data['Age'] <= age_range[1])
                ]
            
            # Performance filter
            if selected_metric and selected_metric in filtered_data.columns:
                filtered_data = filtered_data[filtered_data[selected_metric] >= metric_threshold]
            
            # Display results
            st.subheader(f"📊 Shortlist Results ({len(filtered_data)} players)")
            st.dataframe(filtered_data, use_container_width=True)
            
            # Export options
            if not filtered_data.empty:
                criteria = {
                    'positions': selected_positions,
                    'age_range': age_range,
                    'metric_filter': f"{selected_metric} >= {metric_threshold}",
                    'generated_at': pd.Timestamp.now().isoformat()
                }
                
                report_path = self.report_generator.generate_scouting_shortlist_excel(
                    filtered_data, criteria, 'scouting_shortlist.xlsx'
                )
                
                with open(report_path, "rb") as file:
                    st.download_button(
                        label="📥 Download Shortlist (Excel)",
                        data=file.read(),
                        file_name="scouting_shortlist.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    
    def generate_custom_report_interface(self):
        """
        Interface for generating custom reports
        """
        st.subheader("🎨 Custom Report Builder")
        
        st.info("Custom report builder allows you to create tailored reports with specific metrics and visualizations.")
        
        # Report components
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Include Sections")
            include_overview = st.checkbox("Player Overview", value=True)
            include_stats = st.checkbox("Performance Statistics", value=True)
            include_charts = st.checkbox("Visualizations", value=True)
            include_comparison = st.checkbox("League Comparison", value=False)
        
        with col2:
            st.subheader("📈 Chart Types")
            if include_charts:
                chart_types = st.multiselect(
                    "Select Charts:",
                    ["Radar Chart", "Performance Trends", "Position Distribution", "Team Comparison"],
                    default=["Radar Chart"]
                )
        
        # Data selection
        st.subheader("🎯 Data Selection")
        
        if 'Team' in st.session_state.player_data.columns:
            data_scope = st.selectbox(
                "Report Scope:",
                ["All Players", "Specific Team", "Specific Position", "Custom Selection"]
            )
            
            if data_scope == "Specific Team":
                teams = st.session_state.player_data['Team'].unique()
                selected_team = st.selectbox("Select Team:", teams)
            elif data_scope == "Specific Position":
                positions = st.session_state.player_data['Position'].unique()
                selected_position = st.selectbox("Select Position:", positions)
        
        # Generate button
        if st.button("🚀 Generate Custom Report"):
            st.success("Custom report generation feature coming soon!")
            st.info("This feature will allow you to create fully customized reports with your selected components.")

# Main execution
if __name__ == "__main__":
    dashboard = ScoutAIDashboard()
    dashboard.run()