#!/usr/bin/env python
"""
LeadTool Main Entry Point
Unified Lead Generation and Management System
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging configuration"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/leadtool.log'),
            logging.StreamHandler()
        ]
    )

def run_api():
    """Run the FastAPI server"""
    import uvicorn
    
    # Check if we're on Render (has PORT environment variable)
    if os.getenv('PORT'):
        print("Detected Render environment - skipping API server")
        print("Use start_render.py for dashboard deployment")
        return
    
    print("Starting LeadTool API Server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

def run_dashboard():
    """Run the Streamlit dashboard"""
    import subprocess
    import os
    
    print("Starting LeadTool Dashboard...")
    
    # Try to use the same Python interpreter that's running this script
    python_exe = sys.executable
    
    # Check if we're on Render
    if os.getenv('PORT'):
        print("Render environment detected - using render_dashboard.py")
        dashboard_file = 'render_dashboard.py'
    else:
        print("Local environment - using simple_dashboard.py")
        dashboard_file = 'simple_dashboard.py'
    
    # If that doesn't work, try to find the correct Python with streamlit
    try:
        subprocess.run([
            python_exe, "-m", "streamlit", "run", 
            dashboard_file,
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except subprocess.CalledProcessError:
        print("Trying alternative Python paths...")
        # Try common Python paths
        python_paths = [
            "python",
            "python3",
            "python3.13",
            r"C:\Users\s\miniconda3\python.exe"
        ]
        
        for python_path in python_paths:
            try:
                print(f"Trying: {python_path}")
                subprocess.run([
                    python_path, "-m", "streamlit", "run", 
                    dashboard_file,
                    "--server.port", "8501",
                    "--server.address", "localhost"
                ], check=True)
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            print("Error: Could not find Python with streamlit installed.")
            print("Please run: pip install streamlit")
            print("Or run manually: streamlit run app/dashboard/main.py --server.port 8501")

def run_scraper():
    """Run the scraper manually"""
    from app.scheduler.manual import run_manual_scraping
    
    print("Starting LeadTool Scraper...")
    run_manual_scraping()

def run_scheduler():
    """Run the scheduler"""
    from app.scheduler.cron import main as scheduler_main
    
    print("Starting LeadTool Scheduler...")
    scheduler_main()

def run_all():
    """Run all services"""
    import threading
    import time
    
    print("Starting LeadTool - All Services...")
    
    # Start API in background
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Wait for API to start
    time.sleep(5)
    
    # Start dashboard in background
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Start scheduler in foreground
    run_scheduler()

def main():
    """Main entry point"""
    # Check if we're on Render and should run dashboard
    if os.getenv('PORT') and len(sys.argv) == 1:
        print("Detected Render environment - running dashboard")
        run_dashboard()
        return
    
    parser = argparse.ArgumentParser(
        description="LeadTool - Unified Lead Generation and Management System"
    )
    
    parser.add_argument(
        "command",
        choices=["api", "dashboard", "scraper", "scheduler", "all"],
        help="Command to run"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Set debug mode
    if args.debug:
        os.environ["DEBUG"] = "true"
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the requested command
    if args.command == "api":
        run_api()
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "scraper":
        run_scraper()
    elif args.command == "scheduler":
        run_scheduler()
    elif args.command == "all":
        run_all()

if __name__ == "__main__":
    main()
