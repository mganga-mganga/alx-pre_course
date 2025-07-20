#!/usr/bin/env python3
"""
ScoutAI Enterprise Setup Script
Automated installation and configuration
"""
import os
import sys
import subprocess
import shutil
import secrets
from pathlib import Path
import psycopg2
from psycopg2 import sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScoutAISetup:
    """Setup manager for ScoutAI Enterprise"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_installed = False
        self.database_configured = False
        self.env_configured = False
        
    def run_setup(self):
        """Run complete setup process"""
        logger.info("🏈 Starting ScoutAI Enterprise Setup...")
        
        try:
            self.check_prerequisites()
            self.install_requirements()
            self.setup_environment()
            self.setup_database()
            self.download_afl_data()
            self.initialize_system()
            self.setup_complete()
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            sys.exit(1)
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8+ required")
        
        # Check if PostgreSQL is available
        try:
            subprocess.run(['psql', '--version'], capture_output=True, check=True)
            logger.info("✅ PostgreSQL found")
        except subprocess.CalledProcessError:
            logger.warning("⚠️ PostgreSQL not found. Please install PostgreSQL 12+")
            response = input("Continue without PostgreSQL? (y/N): ")
            if response.lower() != 'y':
                raise Exception("PostgreSQL required for full functionality")
        
        # Check if Git is available
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            logger.info("✅ Git found")
        except subprocess.CalledProcessError:
            raise Exception("Git is required for downloading AFL data")
    
    def install_requirements(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")
        
        requirements_file = self.project_root / "requirements_enterprise.txt"
        if not requirements_file.exists():
            raise Exception("requirements_enterprise.txt not found")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True)
            
            self.requirements_installed = True
            logger.info("✅ Dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install dependencies: {e}")
    
    def setup_environment(self):
        """Setup environment configuration"""
        logger.info("⚙️ Setting up environment configuration...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            logger.info("📄 .env file already exists")
            response = input("Overwrite existing .env file? (y/N): ")
            if response.lower() != 'y':
                self.env_configured = True
                return
        
        # Copy example file
        if env_example.exists():
            shutil.copy(env_example, env_file)
            logger.info("📄 Created .env from example")
        else:
            # Create basic .env file
            self.create_basic_env_file(env_file)
        
        # Generate secret key
        secret_key = secrets.token_urlsafe(32)
        self.update_env_file(env_file, "SECRET_KEY", secret_key)
        
        # Get user input for configuration
        self.configure_environment_interactive(env_file)
        
        self.env_configured = True
        logger.info("✅ Environment configured")
    
    def create_basic_env_file(self, env_file):
        """Create basic .env file"""
        env_content = """# ScoutAI Enterprise Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scout_ai_afl
DB_USER=scout_ai
DB_PASSWORD=scout_ai_password

LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

SECRET_KEY=generated-secret-key
AFL_DATA_PATH=data/afl_data_source
DEBUG=false
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
    
    def configure_environment_interactive(self, env_file):
        """Interactive environment configuration"""
        logger.info("🔧 Configuring environment variables...")
        
        # OpenAI API Key
        api_key = input("Enter OpenAI API Key (or press Enter to skip): ").strip()
        if api_key:
            self.update_env_file(env_file, "OPENAI_API_KEY", api_key)
        
        # Database configuration
        print("\n📊 Database Configuration:")
        db_host = input("Database host (localhost): ").strip() or "localhost"
        db_port = input("Database port (5432): ").strip() or "5432"
        db_name = input("Database name (scout_ai_afl): ").strip() or "scout_ai_afl"
        db_user = input("Database user (scout_ai): ").strip() or "scout_ai"
        db_password = input("Database password (scout_ai_password): ").strip() or "scout_ai_password"
        
        self.update_env_file(env_file, "DB_HOST", db_host)
        self.update_env_file(env_file, "DB_PORT", db_port)
        self.update_env_file(env_file, "DB_NAME", db_name)
        self.update_env_file(env_file, "DB_USER", db_user)
        self.update_env_file(env_file, "DB_PASSWORD", db_password)
    
    def update_env_file(self, env_file, key, value):
        """Update environment file with key-value pair"""
        # Read current content
        content = []
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.readlines()
        
        # Update or add the key
        key_found = False
        for i, line in enumerate(content):
            if line.startswith(f"{key}="):
                content[i] = f"{key}={value}\n"
                key_found = True
                break
        
        if not key_found:
            content.append(f"{key}={value}\n")
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(content)
    
    def setup_database(self):
        """Setup PostgreSQL database"""
        logger.info("🗄️ Setting up database...")
        
        # Load environment variables
        env_file = self.project_root / ".env"
        env_vars = self.load_env_file(env_file)
        
        db_config = {
            'host': env_vars.get('DB_HOST', 'localhost'),
            'port': env_vars.get('DB_PORT', '5432'),
            'database': 'postgres',  # Connect to default database first
            'user': 'postgres',  # Use postgres superuser
            'password': None
        }
        
        # Get postgres password
        pg_password = input("Enter PostgreSQL superuser password (or press Enter if no password): ").strip()
        if pg_password:
            db_config['password'] = pg_password
        
        try:
            # Connect to PostgreSQL
            if db_config['password']:
                conn = psycopg2.connect(**db_config)
            else:
                del db_config['password']
                conn = psycopg2.connect(**db_config)
            
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create database
            db_name = env_vars.get('DB_NAME', 'scout_ai_afl')
            db_user = env_vars.get('DB_USER', 'scout_ai')
            db_password = env_vars.get('DB_PASSWORD', 'scout_ai_password')
            
            try:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                logger.info(f"📊 Created database: {db_name}")
            except psycopg2.errors.DuplicateDatabase:
                logger.info(f"📊 Database {db_name} already exists")
            
            # Create user
            try:
                cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(db_user)), [db_password])
                logger.info(f"👤 Created user: {db_user}")
            except psycopg2.errors.DuplicateObject:
                logger.info(f"👤 User {db_user} already exists")
            
            # Grant privileges
            cursor.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name), sql.Identifier(db_user)
            ))
            
            cursor.close()
            conn.close()
            
            self.database_configured = True
            logger.info("✅ Database setup completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Database setup failed: {e}")
            logger.info("Please set up PostgreSQL manually or use SQLite for development")
    
    def download_afl_data(self):
        """Download AFL dataset"""
        logger.info("📥 Downloading AFL dataset...")
        
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)
        
        afl_data_path = data_dir / "afl_data_source"
        
        if afl_data_path.exists():
            logger.info("📊 AFL data already exists")
            response = input("Re-download AFL data? (y/N): ")
            if response.lower() != 'y':
                return
            
            shutil.rmtree(afl_data_path)
        
        try:
            subprocess.run([
                'git', 'clone', 
                'https://github.com/akareen/AFL-Data-Analysis.git',
                str(afl_data_path)
            ], check=True)
            
            logger.info("✅ AFL dataset downloaded successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download AFL data: {e}")
            logger.info("Please download manually from: https://github.com/akareen/AFL-Data-Analysis")
    
    def initialize_system(self):
        """Initialize the system"""
        logger.info("🚀 Initializing system...")
        
        try:
            # Create necessary directories
            (self.project_root / "reports").mkdir(exist_ok=True)
            (self.project_root / "models").mkdir(exist_ok=True)
            
            # Test imports
            sys.path.append(str(self.project_root))
            
            try:
                from app.database import db_manager
                from app.auth.auth_service import auth_service
                
                # Test database connection
                if db_manager.test_connection():
                    logger.info("✅ Database connection successful")
                    
                    # Create tables
                    db_manager.create_tables()
                    logger.info("✅ Database tables created")
                    
                    # Create default admin user
                    auth_service.create_default_admin()
                    logger.info("✅ Default admin user created")
                    
                else:
                    logger.warning("⚠️ Database connection failed")
                    
            except ImportError as e:
                logger.warning(f"⚠️ Could not import modules: {e}")
                logger.info("System will initialize on first run")
            
            logger.info("✅ System initialization completed")
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
    
    def load_env_file(self, env_file):
        """Load environment variables from file"""
        env_vars = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        return env_vars
    
    def setup_complete(self):
        """Display setup completion message"""
        logger.info("🎉 ScoutAI Enterprise setup completed!")
        
        print("\n" + "="*60)
        print("🏈 SCOUTAI ENTERPRISE - SETUP COMPLETE!")
        print("="*60)
        
        print("\n📋 Next Steps:")
        print("1. Configure your .env file with API keys")
        print("2. Start the system:")
        print("   • Backend:   python -m app.main")
        print("   • Dashboard: streamlit run scout_ai_enterprise_dashboard.py")
        print("3. Access the dashboard at: http://localhost:8501")
        print("4. API documentation at: http://localhost:8000/docs")
        
        print("\n🔐 Default Admin Credentials:")
        print("Username: admin")
        print("Password: (check console output when starting the system)")
        
        print("\n📚 Documentation:")
        print("• README_ENTERPRISE.md - Comprehensive documentation")
        print("• .env.example - Configuration options")
        print("• Docker: docker-compose up -d")
        
        print("\n🆘 Support:")
        print("• GitHub Issues: <repository-url>/issues")
        print("• Documentation: README_ENTERPRISE.md")
        
        print("\n" + "="*60)
        print("Happy Scouting! 🏈")
        print("="*60)

def main():
    """Main setup entry point"""
    setup = ScoutAISetup()
    setup.run_setup()

if __name__ == "__main__":
    main()