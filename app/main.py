"""
ScoutAI Enterprise - Main Application Entry Point
FastAPI backend with authentication, data ingestion, and reporting endpoints
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from .config import config
from .database import db_manager
from .auth.auth_service import auth_service, UserRole
from .services.data_ingestion import afl_data_service
from .services.llm_service import llm_service
from .models.enhanced_ml_models import player_model, team_model
from .reports.report_generator import report_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting ScoutAI Enterprise system...")
    
    # Test database connection
    if not db_manager.test_connection():
        logger.error("Database connection failed!")
        raise Exception("Database connection failed")
    
    # Create database tables
    try:
        db_manager.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise
    
    # Create default admin user
    try:
        auth_service.create_default_admin()
    except Exception as e:
        logger.warning(f"Admin user creation skipped: {e}")
    
    # Initialize ML models (in background)
    try:
        player_model._load_models()
        logger.info("ML models loaded successfully")
    except Exception as e:
        logger.warning(f"ML models not available: {e}")
    
    logger.info("ScoutAI Enterprise started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ScoutAI Enterprise...")

# Create FastAPI app
app = FastAPI(
    title="ScoutAI Enterprise",
    description="Enterprise-Grade AFL Scouting Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data"""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

async def require_role(required_roles: List[str]):
    """Check if user has required role"""
    def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get('role')
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return current_user
    return role_checker

# Authentication endpoints
@app.post("/auth/login")
async def login(username: str, password: str):
    """User login endpoint"""
    user = auth_service.authenticate_user(username, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = auth_service.create_access_token(user)
    permissions = auth_service.get_user_permissions(user['role'])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "permissions": permissions
    }

@app.post("/auth/register")
async def register(
    username: str, 
    email: str, 
    password: str, 
    role: str = "viewer",
    current_user: Dict = Depends(require_role([UserRole.ADMIN]))
):
    """Register new user (admin only)"""
    try:
        result = auth_service.create_user(username, email, password, role)
        return {"message": "User created successfully", "user": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/users")
async def get_users(current_user: Dict = Depends(require_role([UserRole.ADMIN]))):
    """Get all users (admin only)"""
    users = auth_service.get_all_users()
    return {"users": users}

# Data ingestion endpoints
@app.post("/data/ingest")
async def ingest_data(
    background_tasks: BackgroundTasks,
    force_reload: bool = False,
    current_user: Dict = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    """Trigger data ingestion process"""
    background_tasks.add_task(afl_data_service.ingest_all_data, force_reload)
    return {"message": "Data ingestion started in background"}

@app.get("/data/status")
async def get_data_status(current_user: Dict = Depends(get_current_user)):
    """Get data ingestion status"""
    status = afl_data_service.get_ingestion_status()
    return {"status": status}

# Player endpoints
@app.get("/players")
async def get_players(
    limit: int = 100,
    offset: int = 0,
    search: str = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get players list with search and pagination"""
    try:
        with db_manager.get_session() as session:
            query = "SELECT * FROM players"
            params = {}
            
            if search:
                query += " WHERE LOWER(first_name || ' ' || last_name) LIKE LOWER(:search)"
                params['search'] = f"%{search}%"
            
            query += " ORDER BY last_name, first_name LIMIT :limit OFFSET :offset"
            params.update({'limit': limit, 'offset': offset})
            
            result = session.execute(query, params).fetchall()
            players = [dict(row._mapping) for row in result]
            
            return {"players": players}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/{player_id}")
async def get_player(player_id: int, current_user: Dict = Depends(get_current_user)):
    """Get detailed player information"""
    try:
        with db_manager.get_session() as session:
            # Get player details
            player_query = "SELECT * FROM players WHERE id = :player_id"
            player_result = session.execute(player_query, {'player_id': player_id}).fetchone()
            
            if not player_result:
                raise HTTPException(status_code=404, detail="Player not found")
            
            player_data = dict(player_result._mapping)
            
            # Get performance data
            performance_query = "SELECT * FROM player_performance WHERE player_id = :player_id ORDER BY year DESC, games_played DESC LIMIT 50"
            performance_result = session.execute(performance_query, {'player_id': player_id}).fetchall()
            performance_data = [dict(row._mapping) for row in performance_result]
            
            return {
                "player": player_data,
                "recent_performance": performance_data
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/players/{player_id}/analysis")
async def analyze_player(
    player_id: int,
    current_user: Dict = Depends(require_role([UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN]))
):
    """Generate AI analysis for player"""
    try:
        # Get ML predictions
        ml_analysis = player_model.predict_player_potential(player_id)
        
        # Get LLM insights if available
        llm_analysis = None
        permissions = auth_service.get_user_permissions(current_user['role'])
        
        if permissions.get('access_llm'):
            with db_manager.get_session() as session:
                # Get player data for LLM
                player_query = "SELECT * FROM players WHERE id = :player_id"
                player_result = session.execute(player_query, {'player_id': player_id}).fetchone()
                
                performance_query = "SELECT * FROM player_performance WHERE player_id = :player_id ORDER BY year DESC LIMIT 20"
                performance_result = session.execute(performance_query, {'player_id': player_id}).fetchall()
                
                if player_result:
                    player_data = dict(player_result._mapping)
                    performance_data = [dict(row._mapping) for row in performance_result]
                    
                    llm_analysis = llm_service.generate_player_analysis(player_data, performance_data)
        
        return {
            "ml_analysis": ml_analysis,
            "llm_analysis": llm_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Team endpoints
@app.get("/teams")
async def get_teams(current_user: Dict = Depends(get_current_user)):
    """Get teams list"""
    try:
        with db_manager.get_session() as session:
            query = "SELECT * FROM teams WHERE is_active = true ORDER BY name"
            result = session.execute(query).fetchall()
            teams = [dict(row._mapping) for row in result]
            
            return {"teams": teams}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/{team_name}/analysis")
async def analyze_team(
    team_name: str,
    season: int = None,
    current_user: Dict = Depends(require_role([UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN]))
):
    """Generate AI analysis for team"""
    try:
        # Get ML analysis
        ml_analysis = team_model.analyze_team_performance(team_name, season)
        
        # Get LLM insights if available
        llm_analysis = None
        permissions = auth_service.get_user_permissions(current_user['role'])
        
        if permissions.get('access_llm'):
            llm_analysis = llm_service.generate_team_analysis({'name': team_name}, [])
        
        return {
            "ml_analysis": ml_analysis,
            "llm_analysis": llm_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Report endpoints
@app.post("/reports/player/{player_id}")
async def generate_player_report(
    player_id: int,
    format: str = "pdf",
    current_user: Dict = Depends(require_role([UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN]))
):
    """Generate player scouting report"""
    try:
        filename = report_generator.generate_player_scouting_report(player_id, format)
        return {"message": "Report generated successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/team/{team_name}")
async def generate_team_report(
    team_name: str,
    format: str = "pdf",
    season: int = None,
    current_user: Dict = Depends(require_role([UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN]))
):
    """Generate team analysis report"""
    try:
        filename = report_generator.generate_team_analysis_report(team_name, season, format)
        return {"message": "Report generated successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/download/{filename}")
async def download_report(
    filename: str,
    current_user: Dict = Depends(get_current_user)
):
    """Download generated report"""
    try:
        file_path = f"reports/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# LLM Chat endpoint
@app.post("/chat")
async def chat_query(
    query: str,
    context_data: Dict = None,
    current_user: Dict = Depends(require_role([UserRole.SCOUT, UserRole.ANALYST, UserRole.ADMIN]))
):
    """Natural language chat interface"""
    try:
        response = llm_service.chat_query(query, context_data)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    status = {
        "status": "healthy",
        "database": db_manager.test_connection(),
        "data_status": afl_data_service.get_ingestion_status()
    }
    
    return status

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "ScoutAI Enterprise - AFL Scouting Intelligence System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level="info"
    )