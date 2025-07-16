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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #003f7f 0%, #cc2e3a 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .query-box {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #003f7f;
    }
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
    
    def run(self):
        """
        Main dashboard runner
        """
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>🏈 Scout AI - AFL Scouting Platform</h1>
        </div>
        """, unsafe_allow_html=True)
        
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
        Create sidebar with data management and settings
        """
        st.sidebar.title("Scout AI Control Panel")
        
        # Data Management Section
        st.sidebar.header("📥 Data Management")
        
        if st.sidebar.button("🔄 Refresh Data", help="Scrape latest data from sources"):
            with st.spinner("Scraping latest AFL data..."):
                self.refresh_data()
        
        # Data status
        if st.session_state.data_loaded:
            st.sidebar.success("✅ Data loaded successfully")
            if not st.session_state.player_data.empty:
                st.sidebar.info(f"Players: {len(st.session_state.player_data)}")
            if not st.session_state.games_data.empty:
                st.sidebar.info(f"Games: {len(st.session_state.games_data)}")
        else:
            st.sidebar.warning("⚠️ No data loaded")
            if st.sidebar.button("🚀 Load Sample Data"):
                self.load_sample_data()
        
        # Settings
        st.sidebar.header("⚙️ Settings")
        
        # ML Model settings
        st.sidebar.subheader("ML Models")
        if st.sidebar.button("🤖 Train Performance Model"):
            if not st.session_state.player_data.empty:
                with st.spinner("Training ML model..."):
                    self.train_models()
            else:
                st.sidebar.error("No player data available for training")
        
        # Export options
        st.sidebar.subheader("📤 Quick Export")
        if st.sidebar.button("💾 Export All Data"):
            self.export_data()
    
    def natural_language_interface(self):
        """
        Natural language query interface
        """
        st.header("🗣️ Ask Scout AI Anything")
        
        # Query examples
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("""
            **Try these example queries:**
            - "Find midfielders under 23 with high clearance rates in the VFL"
            - "Show me the top 10 key forwards with best goal accuracy"
            - "Compare Carlton players vs Richmond players for contested possessions"
            - "List young defenders with good marking ability"
            - "Who are the best ruckmen for contested ball work?"
            """)
        
        # Query input
        st.markdown('<div class="query-box">', unsafe_allow_html=True)
        user_query = st.text_input(
            "Enter your scouting query:",
            placeholder="e.g., Find the best young midfielders with high disposal counts",
            help="Use natural language to describe what you're looking for"
        )
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
        
        # Results
        if 'filtered_data' in st.session_state and not st.session_state.filtered_data.empty:
            st.subheader("📊 Query Results")
            
            # Summary metrics
            result_data = st.session_state.filtered_data
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Players Found", len(result_data))
            with col2:
                if 'Team' in result_data.columns:
                    st.metric("Teams", result_data['Team'].nunique())
            with col3:
                if 'Position' in result_data.columns:
                    st.metric("Positions", result_data['Position'].nunique())
            with col4:
                if 'Age' in result_data.columns:
                    st.metric("Avg Age", f"{result_data['Age'].mean():.1f}")
            
            # Data table
            st.dataframe(
                result_data.head(20),
                use_container_width=True,
                height=400
            )
            
            # Quick visualization
            if len(result_data) > 1:
                st.subheader("📈 Quick Visualization")
                
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    if 'Position' in result_data.columns:
                        position_counts = result_data['Position'].value_counts()
                        st.bar_chart(position_counts)
                        st.caption("Players by Position")
                
                with viz_col2:
                    if 'Team' in result_data.columns:
                        team_counts = result_data['Team'].value_counts().head(10)
                        st.bar_chart(team_counts)
                        st.caption("Players by Team")
        else:
            st.warning("No players found matching your criteria. Try adjusting your query.")
    
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