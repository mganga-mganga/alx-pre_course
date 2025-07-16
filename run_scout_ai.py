#!/usr/bin/env python3
"""
Scout AI AFL Platform - Alternative Runner
Launches the Streamlit dashboard with proper configuration
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    """
    Main function to launch Scout AI dashboard
    """
    print("🏈 Starting Scout AI AFL Platform...")
    print("=====================================")
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Set environment variables for Streamlit
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    
    try:
        # Check if streamlit is installed
        import streamlit
        print(f"✅ Streamlit found (version {streamlit.__version__})")
        
        # Launch the dashboard
        dashboard_path = current_dir / "scout_ai_dashboard.py"
        
        if not dashboard_path.exists():
            print(f"❌ Dashboard file not found: {dashboard_path}")
            return 1
        
        print(f"🚀 Launching dashboard from: {dashboard_path}")
        print("📱 Access the platform at: http://localhost:8501")
        print("⏹️  Press Ctrl+C to stop the server")
        print()
        
        # Run streamlit
        cmd = [
            sys.executable, 
            "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ]
        
        subprocess.run(cmd)
        
    except ImportError:
        print("❌ Streamlit not found. Please install dependencies first:")
        print("   pip install -r requirements.txt")
        return 1
    
    except KeyboardInterrupt:
        print("\n👋 Scout AI dashboard stopped.")
        return 0
    
    except Exception as e:
        print(f"❌ Error starting Scout AI: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)