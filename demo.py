#!/usr/bin/env python3
"""
Scout AI AFL Platform - Demo Script
Showcases the enhanced user-friendly and AFL-themed interface
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Demo script for Scout AI AFL Platform
    """
    print("🏈 Scout AI AFL Platform - Enhanced Demo")
    print("=" * 50)
    print()
    
    print("🎨 New Features in this Update:")
    print("✅ AFL-themed visual design with team colors")
    print("✅ Enhanced landing page with graphics")
    print("✅ Interactive welcome section")
    print("✅ Improved natural language interface")
    print("✅ Professional sidebar with AFL branding")
    print("✅ Quick query buttons for common searches")
    print("✅ Enhanced result displays with insights")
    print("✅ Animated elements and hover effects")
    print()
    
    print("🏟️ AFL-Specific Enhancements:")
    print("• All 18 AFL team colors represented")
    print("• AFL football graphics and icons")
    print("• Position-specific analysis tools")
    print("• Team comparison visualizations")
    print("• AFL terminology and context")
    print()
    
    print("🚀 Quick Start Options:")
    print("1. Load sample AFL player data")
    print("2. Try natural language queries")
    print("3. Explore interactive visualizations")
    print("4. Generate professional reports")
    print()
    
    response = input("Would you like to launch the enhanced Scout AI dashboard? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print("\n🚀 Launching Scout AI with enhanced AFL theme...")
        print("📱 The dashboard will open at: http://localhost:8501")
        print("⏹️  Press Ctrl+C in the terminal to stop")
        print()
        
        try:
            # Launch Streamlit dashboard
            dashboard_path = Path(__file__).parent / "scout_ai_dashboard.py"
            
            if dashboard_path.exists():
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    str(dashboard_path),
                    "--server.port", "8501",
                    "--server.address", "0.0.0.0"
                ])
            else:
                print("❌ Dashboard file not found. Please ensure scout_ai_dashboard.py exists.")
                
        except KeyboardInterrupt:
            print("\n👋 Scout AI demo stopped.")
        except Exception as e:
            print(f"❌ Error launching dashboard: {e}")
            print("💡 Try running: streamlit run scout_ai_dashboard.py")
    
    else:
        print("\n📖 To launch manually, run:")
        print("   streamlit run scout_ai_dashboard.py")
        print("\n🔧 For installation help, run:")
        print("   ./install.sh  (Linux/Mac)")
        print("   install.bat   (Windows)")

if __name__ == "__main__":
    main()