"""
Interactive visualization module for AFL Scout AI platform.
Creates charts, heatmaps, and interactive dashboards for player and team analysis.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AFLVisualizer:
    """
    AFL-specific data visualization class
    """
    
    def __init__(self):
        # AFL team colors for consistent visualization
        self.team_colors = {
            'Adelaide Crows': '#002B5C',
            'Brisbane Lions': '#8B2635',
            'Carlton Blues': '#0F1B3C',
            'Collingwood Magpies': '#000000',
            'Essendon Bombers': '#CC2E3A',
            'Fremantle Dockers': '#2E0A4F',
            'Geelong Cats': '#1B5299',
            'Gold Coast Suns': '#FFC72C',
            'GWS Giants': '#F47920',
            'Hawthorn Hawks': '#4A2C17',
            'Melbourne Demons': '#CC2E3A',
            'North Melbourne Kangaroos': '#0F1B3C',
            'Port Adelaide Power': '#008A97',
            'Richmond Tigers': '#FFCD00',
            'St Kilda Saints': '#CC2E3A',
            'Sydney Swans': '#CC2E3A',
            'West Coast Eagles': '#003F7F',
            'Western Bulldogs': '#015BAE'
        }
        
        # Set default styling
        plt.style.use('default')
        sns.set_palette("husl")
    
    def create_player_scatter(self, df: pd.DataFrame, x_metric: str, y_metric: str, 
                            color_by: str = 'Position', size_by: str = None,
                            title: str = None) -> go.Figure:
        """
        Create interactive scatter plot for player comparison
        """
        if x_metric not in df.columns or y_metric not in df.columns:
            logger.error(f"Metrics {x_metric} or {y_metric} not found in DataFrame")
            return go.Figure()
        
        fig = px.scatter(
            df, 
            x=x_metric, 
            y=y_metric,
            color=color_by if color_by in df.columns else None,
            size=size_by if size_by and size_by in df.columns else None,
            hover_data=['Player', 'Team', 'Age'] if 'Player' in df.columns else None,
            title=title or f"{y_metric} vs {x_metric}",
            template="plotly_white"
        )
        
        # Customize layout
        fig.update_layout(
            xaxis_title=x_metric.replace('_', ' ').title(),
            yaxis_title=y_metric.replace('_', ' ').title(),
            height=600,
            showlegend=True
        )
        
        # Add trend line
        fig.add_trace(
            go.Scatter(
                x=df[x_metric], 
                y=np.poly1d(np.polyfit(df[x_metric].fillna(0), df[y_metric].fillna(0), 1))(df[x_metric]),
                mode='lines',
                name='Trend',
                line=dict(dash='dash', color='gray')
            )
        )
        
        return fig
    
    def create_player_radar(self, player_data: Dict[str, float], 
                          stats: List[str] = None, title: str = None) -> go.Figure:
        """
        Create radar chart for individual player analysis
        """
        if stats is None:
            stats = ['Disposals', 'Marks', 'Tackles', 'Goals', 'Contested_Rate']
        
        # Filter stats that exist in player data
        available_stats = [stat for stat in stats if stat in player_data]
        
        if not available_stats:
            logger.error("No matching stats found in player data")
            return go.Figure()
        
        values = [player_data.get(stat, 0) for stat in available_stats]
        
        # Normalize values to 0-100 scale for radar chart
        max_values = [max(1, abs(v)) for v in values]  # Avoid division by zero
        normalized_values = [(v / max_v) * 100 for v, max_v in zip(values, max_values)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=normalized_values + [normalized_values[0]],  # Close the radar
            theta=available_stats + [available_stats[0]],
            fill='toself',
            name=title or 'Player Stats'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title=title or "Player Performance Radar"
        )
        
        return fig
    
    def create_team_comparison(self, df: pd.DataFrame, metric: str, 
                             teams: List[str] = None) -> go.Figure:
        """
        Create team comparison bar chart
        """
        if 'Team' not in df.columns or metric not in df.columns:
            logger.error("Required columns not found for team comparison")
            return go.Figure()
        
        # Group by team and calculate mean
        team_stats = df.groupby('Team')[metric].mean().reset_index()
        
        if teams:
            team_stats = team_stats[team_stats['Team'].isin(teams)]
        
        # Sort by metric value
        team_stats = team_stats.sort_values(metric, ascending=False)
        
        fig = px.bar(
            team_stats,
            x='Team',
            y=metric,
            title=f"Team Comparison: {metric.replace('_', ' ').title()}",
            template="plotly_white"
        )
        
        # Color bars by team colors if available
        colors = [self.team_colors.get(team, '#636EFA') for team in team_stats['Team']]
        fig.update_traces(marker_color=colors)
        
        fig.update_layout(
            xaxis_title="Team",
            yaxis_title=metric.replace('_', ' ').title(),
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
    
    def create_position_distribution(self, df: pd.DataFrame, metric: str) -> go.Figure:
        """
        Create box plot showing metric distribution by position
        """
        if 'Position' not in df.columns or metric not in df.columns:
            logger.error("Required columns not found for position distribution")
            return go.Figure()
        
        fig = px.box(
            df,
            x='Position',
            y=metric,
            title=f"{metric.replace('_', ' ').title()} Distribution by Position",
            template="plotly_white"
        )
        
        fig.update_layout(
            xaxis_title="Position",
            yaxis_title=metric.replace('_', ' ').title(),
            height=500
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, metrics: List[str], 
                      correlation: bool = True) -> go.Figure:
        """
        Create correlation heatmap or metric heatmap
        """
        # Filter metrics that exist in DataFrame
        available_metrics = [m for m in metrics if m in df.columns]
        
        if len(available_metrics) < 2:
            logger.error("Insufficient metrics for heatmap")
            return go.Figure()
        
        if correlation:
            # Correlation heatmap
            corr_matrix = df[available_metrics].corr()
            
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title="Player Statistics Correlation Matrix",
                template="plotly_white"
            )
            
        else:
            # Direct metric heatmap (e.g., by team)
            if 'Team' in df.columns:
                pivot_data = df.groupby('Team')[available_metrics].mean()
                
                fig = px.imshow(
                    pivot_data.T,
                    text_auto=True,
                    aspect="auto",
                    title="Team Performance Heatmap",
                    template="plotly_white"
                )
            else:
                # Fallback to correlation
                return self.create_heatmap(df, metrics, correlation=True)
        
        fig.update_layout(height=600)
        return fig
    
    def create_age_performance_scatter(self, df: pd.DataFrame, 
                                     performance_metric: str = 'Disposals') -> go.Figure:
        """
        Create age vs performance scatter plot with trend analysis
        """
        if 'Age' not in df.columns or performance_metric not in df.columns:
            logger.error("Age or performance metric not found")
            return go.Figure()
        
        fig = px.scatter(
            df,
            x='Age',
            y=performance_metric,
            color='Position' if 'Position' in df.columns else None,
            hover_data=['Player', 'Team'] if 'Player' in df.columns else None,
            title=f"Age vs {performance_metric.replace('_', ' ').title()}",
            template="plotly_white"
        )
        
        # Add polynomial trend line
        ages = df['Age'].fillna(df['Age'].median())
        performance = df[performance_metric].fillna(0)
        
        # Fit polynomial (degree 2 for age curve)
        z = np.polyfit(ages, performance, 2)
        p = np.poly1d(z)
        
        x_trend = np.linspace(ages.min(), ages.max(), 100)
        y_trend = p(x_trend)
        
        fig.add_trace(
            go.Scatter(
                x=x_trend,
                y=y_trend,
                mode='lines',
                name='Age Curve',
                line=dict(dash='dash', color='red', width=2)
            )
        )
        
        fig.update_layout(
            xaxis_title="Age",
            yaxis_title=performance_metric.replace('_', ' ').title(),
            height=500
        )
        
        return fig
    
    def create_ranking_chart(self, df: pd.DataFrame, metric: str, 
                           position: str = None, top_n: int = 20) -> go.Figure:
        """
        Create player ranking chart
        """
        df_filtered = df.copy()
        
        if position and 'Position' in df.columns:
            df_filtered = df_filtered[df_filtered['Position'] == position]
        
        if metric not in df_filtered.columns:
            logger.error(f"Metric {metric} not found")
            return go.Figure()
        
        # Sort and get top N
        df_ranked = df_filtered.nlargest(top_n, metric)
        
        fig = px.bar(
            df_ranked,
            x=metric,
            y='Player' if 'Player' in df_ranked.columns else df_ranked.index,
            orientation='h',
            color='Team' if 'Team' in df_ranked.columns else None,
            title=f"Top {top_n} Players: {metric.replace('_', ' ').title()}" + 
                  (f" ({position})" if position else ""),
            template="plotly_white"
        )
        
        fig.update_layout(
            xaxis_title=metric.replace('_', ' ').title(),
            yaxis_title="Player",
            height=max(400, top_n * 25),  # Dynamic height based on number of players
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
    
    def create_performance_trends(self, df: pd.DataFrame, player_name: str,
                                metrics: List[str]) -> go.Figure:
        """
        Create performance trend chart for a specific player
        """
        if 'Player' not in df.columns:
            logger.error("Player column not found")
            return go.Figure()
        
        player_data = df[df['Player'] == player_name]
        
        if player_data.empty:
            logger.error(f"No data found for player: {player_name}")
            return go.Figure()
        
        # Assuming we have round or date data for trends
        if 'Round' in player_data.columns:
            x_axis = 'Round'
        elif 'Date' in player_data.columns:
            x_axis = 'Date'
        else:
            # Create a simple index if no time series data
            player_data = player_data.reset_index()
            x_axis = 'index'
        
        fig = make_subplots(
            rows=len(metrics), cols=1,
            subplot_titles=[m.replace('_', ' ').title() for m in metrics],
            shared_xaxes=True
        )
        
        for i, metric in enumerate(metrics, 1):
            if metric in player_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=player_data[x_axis],
                        y=player_data[metric],
                        mode='lines+markers',
                        name=metric.replace('_', ' ').title(),
                        line=dict(width=2)
                    ),
                    row=i, col=1
                )
        
        fig.update_layout(
            title=f"Performance Trends: {player_name}",
            height=200 * len(metrics),
            showlegend=False,
            template="plotly_white"
        )
        
        return fig
    
    def create_team_style_analysis(self, df: pd.DataFrame) -> go.Figure:
        """
        Create team playing style analysis using advanced metrics
        """
        if 'Team' not in df.columns:
            logger.error("Team column not found")
            return go.Figure()
        
        # Define style metrics
        style_metrics = {
            'Contested_Rate': 'Contest Focus',
            'Mark_Disposal_Ratio': 'Marking Game',
            'Goal_Accuracy': 'Scoring Efficiency',
            'Tackle_Efficiency': 'Defensive Pressure'
        }
        
        # Calculate team averages
        team_styles = df.groupby('Team').agg({
            metric: 'mean' for metric in style_metrics.keys() 
            if metric in df.columns
        }).reset_index()
        
        if team_styles.empty:
            logger.error("No style metrics found")
            return go.Figure()
        
        # Create parallel coordinates plot
        fig = px.parallel_coordinates(
            team_styles,
            dimensions=[col for col in team_styles.columns if col != 'Team'],
            color_discrete_map=self.team_colors,
            title="Team Playing Style Analysis"
        )
        
        fig.update_layout(height=600)
        return fig

def main():
    """
    Main function to demonstrate visualization capabilities
    """
    visualizer = AFLVisualizer()
    logger.info("AFL Visualizer initialized")
    
    # Example usage would go here with actual data

if __name__ == "__main__":
    main()