"""
Report generation module for AFL Scout AI platform.
Generates PDF, Excel, and web-based reports for scouting analysis.
"""

import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import io
import base64
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AFLReportGenerator:
    """
    AFL scouting report generator supporting multiple formats
    """
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up styles
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        
    def _create_custom_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Create custom paragraph styles for reports
        """
        return {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Title'],
                fontSize=20,
                spaceAfter=30,
                textColor=colors.darkblue
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkred
            ),
            'PlayerName': ParagraphStyle(
                'PlayerName',
                parent=self.styles['Heading3'],
                fontSize=12,
                spaceBefore=10,
                spaceAfter=5,
                textColor=colors.black
            )
        }
    
    def generate_player_profile_pdf(self, player_data: Dict[str, Any], 
                                  charts: Dict[str, go.Figure] = None,
                                  filename: str = None) -> str:
        """
        Generate comprehensive player profile PDF report
        """
        if not filename:
            player_name = player_data.get('Player', 'Unknown').replace(' ', '_')
            filename = f"player_profile_{player_name}.pdf"
        
        filepath = self.output_dir / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        title = f"Player Profile: {player_data.get('Player', 'Unknown Player')}"
        story.append(Paragraph(title, self.custom_styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Basic Information Section
        story.append(Paragraph("Basic Information", self.custom_styles['SectionHeader']))
        
        basic_info = [
            ['Attribute', 'Value'],
            ['Name', player_data.get('Player', 'N/A')],
            ['Team', player_data.get('Team', 'N/A')],
            ['Position', player_data.get('Position', 'N/A')],
            ['Age', str(player_data.get('Age', 'N/A'))],
            ['Height', str(player_data.get('Height', 'N/A'))],
            ['Weight', str(player_data.get('Weight', 'N/A'))]
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 3*inch])
        basic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(basic_table)
        story.append(Spacer(1, 20))
        
        # Performance Statistics Section
        story.append(Paragraph("Performance Statistics", self.custom_styles['SectionHeader']))
        
        perf_stats = [
            ['Statistic', 'Value', 'League Average'],
            ['Disposals', str(player_data.get('Disposals', 'N/A')), '20.5'],
            ['Marks', str(player_data.get('Marks', 'N/A')), '5.2'],
            ['Tackles', str(player_data.get('Tackles', 'N/A')), '4.8'],
            ['Goals', str(player_data.get('Goals', 'N/A')), '1.2'],
            ['Contested Possessions', str(player_data.get('Contested Possessions', 'N/A')), '8.1'],
            ['Goal Accuracy', f"{player_data.get('Goal_Accuracy', 0):.1%}", '52.3%']
        ]
        
        perf_table = Table(perf_stats, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(perf_table)
        story.append(Spacer(1, 20))
        
        # Strengths and Weaknesses Analysis
        story.append(Paragraph("Analysis", self.custom_styles['SectionHeader']))
        
        strengths = self._analyze_player_strengths(player_data)
        weaknesses = self._analyze_player_weaknesses(player_data)
        
        analysis_text = f"""
        <b>Strengths:</b><br/>
        {'. '.join(strengths)}<br/><br/>
        
        <b>Areas for Improvement:</b><br/>
        {'. '.join(weaknesses)}<br/><br/>
        
        <b>Team Fit Assessment:</b><br/>
        This player demonstrates strong {player_data.get('Position', 'positional')} skills with particular 
        strength in {strengths[0] if strengths else 'key areas'}. Would suit teams that value 
        {self._get_team_fit_recommendation(player_data)}.
        """
        
        story.append(Paragraph(analysis_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Add charts if provided
        if charts:
            story.append(Paragraph("Performance Charts", self.custom_styles['SectionHeader']))
            for chart_name, fig in charts.items():
                # Convert Plotly figure to image
                img_bytes = pio.to_image(fig, format="png", width=500, height=400)
                img = Image(io.BytesIO(img_bytes), width=5*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Player profile PDF generated: {filepath}")
        
        return str(filepath)
    
    def generate_team_analysis_pdf(self, team_data: pd.DataFrame, 
                                 team_name: str, charts: Dict[str, go.Figure] = None,
                                 filename: str = None) -> str:
        """
        Generate team analysis PDF report
        """
        if not filename:
            filename = f"team_analysis_{team_name.replace(' ', '_')}.pdf"
        
        filepath = self.output_dir / filename
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        title = f"Team Analysis Report: {team_name}"
        story.append(Paragraph(title, self.custom_styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Team Summary
        story.append(Paragraph("Team Summary", self.custom_styles['SectionHeader']))
        
        team_stats = team_data.agg({
            'Disposals': 'mean',
            'Marks': 'mean',
            'Tackles': 'mean',
            'Goals': 'mean',
            'Age': 'mean'
        }).round(1)
        
        summary_data = [
            ['Metric', 'Team Average'],
            ['Average Disposals', str(team_stats.get('Disposals', 'N/A'))],
            ['Average Marks', str(team_stats.get('Marks', 'N/A'))],
            ['Average Tackles', str(team_stats.get('Tackles', 'N/A'))],
            ['Average Goals', str(team_stats.get('Goals', 'N/A'))],
            ['Average Age', str(team_stats.get('Age', 'N/A'))],
            ['Squad Size', str(len(team_data))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Top Performers
        story.append(Paragraph("Top Performers", self.custom_styles['SectionHeader']))
        
        if 'Disposals' in team_data.columns:
            top_performers = team_data.nlargest(5, 'Disposals')[['Player', 'Position', 'Disposals', 'Marks', 'Tackles']]
            
            performer_data = [['Player', 'Position', 'Disposals', 'Marks', 'Tackles']]
            for _, player in top_performers.iterrows():
                performer_data.append([
                    str(player.get('Player', 'N/A')),
                    str(player.get('Position', 'N/A')),
                    str(player.get('Disposals', 'N/A')),
                    str(player.get('Marks', 'N/A')),
                    str(player.get('Tackles', 'N/A'))
                ])
            
            performer_table = Table(performer_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            performer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(performer_table)
            story.append(Spacer(1, 20))
        
        # Add charts if provided
        if charts:
            story.append(Paragraph("Team Analysis Charts", self.custom_styles['SectionHeader']))
            for chart_name, fig in charts.items():
                img_bytes = pio.to_image(fig, format="png", width=500, height=400)
                img = Image(io.BytesIO(img_bytes), width=5*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 10))
        
        doc.build(story)
        logger.info(f"Team analysis PDF generated: {filepath}")
        
        return str(filepath)
    
    def generate_scouting_shortlist_excel(self, players_df: pd.DataFrame, 
                                        criteria: Dict[str, Any],
                                        filename: str = None) -> str:
        """
        Generate Excel scouting shortlist with multiple sheets
        """
        if not filename:
            filename = "scouting_shortlist.xlsx"
        
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            # Main shortlist
            players_df.to_excel(writer, sheet_name='Shortlist', index=False)
            
            # Position breakdown
            if 'Position' in players_df.columns:
                for position in players_df['Position'].unique():
                    position_players = players_df[players_df['Position'] == position]
                    if not position_players.empty:
                        sheet_name = position.replace('/', '_')[:31]  # Excel sheet name limit
                        position_players.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Summary statistics
            if len(players_df) > 0:
                summary_stats = players_df.describe()
                summary_stats.to_excel(writer, sheet_name='Summary_Stats')
            
            # Criteria used
            criteria_df = pd.DataFrame(list(criteria.items()), columns=['Criteria', 'Value'])
            criteria_df.to_excel(writer, sheet_name='Search_Criteria', index=False)
        
        logger.info(f"Excel scouting shortlist generated: {filepath}")
        return str(filepath)
    
    def generate_web_report(self, data: Dict[str, Any], 
                          charts: Dict[str, go.Figure] = None) -> str:
        """
        Generate HTML web report
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AFL Scout Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #003f7f; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f0f0f0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="header">
                <h1>AFL Scouting Report</h1>
                <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        """
        
        # Add data sections
        for section_name, section_data in data.items():
            html_content += f'<div class="section"><h2>{section_name}</h2>'
            
            if isinstance(section_data, pd.DataFrame):
                html_content += section_data.to_html(classes='table', escape=False)
            elif isinstance(section_data, dict):
                for key, value in section_data.items():
                    html_content += f'<div class="metric"><strong>{key}:</strong> {value}</div>'
            else:
                html_content += f'<p>{section_data}</p>'
            
            html_content += '</div>'
        
        # Add charts
        if charts:
            for chart_name, fig in charts.items():
                chart_html = pio.to_html(fig, include_plotlyjs=False, div_id=f"chart_{chart_name}")
                html_content += f'<div class="section"><h2>{chart_name}</h2>{chart_html}</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        filename = "scout_report.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Web report generated: {filepath}")
        return str(filepath)
    
    def _analyze_player_strengths(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Analyze player's key strengths based on statistics
        """
        strengths = []
        
        # Check disposal efficiency
        if player_data.get('Disposals', 0) > 20:
            strengths.append("High disposal count indicates strong involvement in play")
        
        # Check marking ability
        if player_data.get('Marks', 0) > 6:
            strengths.append("Excellent marking ability")
        
        # Check tackling
        if player_data.get('Tackles', 0) > 5:
            strengths.append("Strong defensive pressure and tackling")
        
        # Check goal scoring
        if player_data.get('Goals', 0) > 1.5:
            strengths.append("Consistent goal scoring threat")
        
        # Check contested possessions
        if player_data.get('Contested Possessions', 0) > 8:
            strengths.append("Excels in contested situations")
        
        return strengths if strengths else ["Solid all-around performance"]
    
    def _analyze_player_weaknesses(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Analyze areas for player improvement
        """
        weaknesses = []
        
        # Check goal accuracy
        if player_data.get('Goal_Accuracy', 1.0) < 0.5:
            weaknesses.append("Goal accuracy could be improved")
        
        # Check contested rate
        if player_data.get('Contested_Rate', 1.0) < 0.3:
            weaknesses.append("Could improve in contested situations")
        
        # Check tackle efficiency
        if player_data.get('Tackle_Efficiency', 1.0) < 0.5:
            weaknesses.append("Tackle efficiency needs work")
        
        return weaknesses if weaknesses else ["No significant weaknesses identified"]
    
    def _get_team_fit_recommendation(self, player_data: Dict[str, Any]) -> str:
        """
        Generate team fit recommendation based on player style
        """
        position = player_data.get('Position', '').lower()
        
        if 'forward' in position:
            if player_data.get('Goals', 0) > 1.5:
                return "attacking, high-scoring game plans"
            else:
                return "defensive forward pressure and workrate"
        elif 'midfielder' in position:
            if player_data.get('Contested_Rate', 0) > 0.4:
                return "contested ball and inside midfield strength"
            else:
                return "ball movement and outside run"
        elif 'defender' in position:
            if player_data.get('Marks', 0) > 6:
                return "strong aerial defense and intercept marking"
            else:
                return "rebounding defense and ball use"
        else:
            return "versatile role players"

def main():
    """
    Main function to demonstrate report generation
    """
    generator = AFLReportGenerator()
    logger.info("AFL Report Generator initialized")
    
    # Example usage would go here with actual data

if __name__ == "__main__":
    main()