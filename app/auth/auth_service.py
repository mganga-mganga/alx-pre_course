"""
Authentication and Authorization Service for ScoutAI Enterprise
"""
import logging
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database import db_manager
from ..config import config

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole:
    """User role definitions"""
    ADMIN = "admin"
    ANALYST = "analyst" 
    SCOUT = "scout"
    VIEWER = "viewer"

class AuthenticationService:
    """Service for user authentication and authorization"""
    
    def __init__(self):
        self.secret_key = config.auth.secret_key
        self.algorithm = config.auth.algorithm
        self.access_token_expire_minutes = config.auth.access_token_expire_minutes
    
    def create_user(self, username: str, email: str, password: str, role: str, team_access: List[str] = None) -> Dict:
        """Create a new user account"""
        try:
            # Validate role
            if role not in [UserRole.ADMIN, UserRole.ANALYST, UserRole.SCOUT, UserRole.VIEWER]:
                raise ValueError(f"Invalid role: {role}")
            
            # Hash password
            hashed_password = self._hash_password(password)
            
            # Prepare user data
            user_data = {
                'username': username,
                'email': email,
                'hashed_password': hashed_password,
                'role': role,
                'team_access': json.dumps(team_access or []),
                'is_active': True,
                'created_at': datetime.now()
            }
            
            with db_manager.get_session() as session:
                # Check if user already exists
                existing_user = session.execute(
                    "SELECT id FROM users WHERE username = :username OR email = :email",
                    {'username': username, 'email': email}
                ).fetchone()
                
                if existing_user:
                    raise ValueError("User with this username or email already exists")
                
                # Insert new user
                result = session.execute(
                    """INSERT INTO users (username, email, hashed_password, role, team_access, is_active, created_at) 
                       VALUES (:username, :email, :hashed_password, :role, :team_access, :is_active, :created_at)
                       RETURNING id""",
                    user_data
                )
                user_id = result.fetchone()[0]
                session.commit()
                
                logger.info(f"Created new user: {username} with role: {role}")
                return {"user_id": user_id, "username": username, "role": role}
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials"""
        try:
            with db_manager.get_session() as session:
                user = session.execute(
                    """SELECT id, username, email, hashed_password, role, team_access, is_active 
                       FROM users WHERE username = :username AND is_active = true""",
                    {'username': username}
                ).fetchone()
                
                if not user:
                    return None
                
                # Verify password
                if not self._verify_password(password, user.hashed_password):
                    return None
                
                # Update last login
                session.execute(
                    "UPDATE users SET last_login = :last_login WHERE id = :id",
                    {'last_login': datetime.now(), 'id': user.id}
                )
                session.commit()
                
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'team_access': json.loads(user.team_access)
                }
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def create_access_token(self, user_data: Dict) -> str:
        """Create JWT access token"""
        try:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            token_data = {
                'sub': user_data['username'],
                'user_id': user_data['id'],
                'role': user_data['role'],
                'team_access': user_data['team_access'],
                'exp': expire
            }
            
            encoded_jwt = jwt.encode(token_data, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                return None
            
            return payload
            
        except jwt.PyJWTError:
            return None
    
    def get_user_permissions(self, role: str) -> Dict[str, bool]:
        """Get user permissions based on role"""
        permissions = {
            'view_players': False,
            'view_teams': False,
            'view_matches': False,
            'generate_reports': False,
            'access_analytics': False,
            'manage_users': False,
            'manage_data': False,
            'access_llm': False,
            'export_data': False
        }
        
        if role == UserRole.VIEWER:
            permissions.update({
                'view_players': True,
                'view_teams': True,
                'view_matches': True
            })
        
        elif role == UserRole.SCOUT:
            permissions.update({
                'view_players': True,
                'view_teams': True,
                'view_matches': True,
                'generate_reports': True,
                'access_analytics': True,
                'access_llm': True,
                'export_data': True
            })
        
        elif role == UserRole.ANALYST:
            permissions.update({
                'view_players': True,
                'view_teams': True,
                'view_matches': True,
                'generate_reports': True,
                'access_analytics': True,
                'access_llm': True,
                'export_data': True,
                'manage_data': True
            })
        
        elif role == UserRole.ADMIN:
            # Admin has all permissions
            permissions = {k: True for k in permissions.keys()}
        
        return permissions
    
    def check_team_access(self, user_team_access: List[str], required_team: str) -> bool:
        """Check if user has access to specific team data"""
        if not user_team_access:  # Empty list means access to all teams
            return True
        
        return required_team in user_team_access
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        try:
            with db_manager.get_session() as session:
                users = session.execute(
                    """SELECT id, username, email, role, team_access, is_active, created_at, last_login 
                       FROM users ORDER BY created_at DESC"""
                ).fetchall()
                
                return [
                    {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'team_access': json.loads(user.team_access),
                        'is_active': user.is_active,
                        'created_at': user.created_at,
                        'last_login': user.last_login
                    }
                    for user in users
                ]
                
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []
    
    def update_user_role(self, user_id: int, new_role: str, team_access: List[str] = None) -> bool:
        """Update user role and team access"""
        try:
            if new_role not in [UserRole.ADMIN, UserRole.ANALYST, UserRole.SCOUT, UserRole.VIEWER]:
                raise ValueError(f"Invalid role: {new_role}")
            
            with db_manager.get_session() as session:
                session.execute(
                    """UPDATE users SET role = :role, team_access = :team_access 
                       WHERE id = :id""",
                    {
                        'role': new_role,
                        'team_access': json.dumps(team_access or []),
                        'id': user_id
                    }
                )
                session.commit()
                logger.info(f"Updated user {user_id} role to {new_role}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating user role: {e}")
            return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        try:
            with db_manager.get_session() as session:
                session.execute(
                    "UPDATE users SET is_active = false WHERE id = :id",
                    {'id': user_id}
                )
                session.commit()
                logger.info(f"Deactivated user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        try:
            hashed_password = self._hash_password(new_password)
            
            with db_manager.get_session() as session:
                session.execute(
                    "UPDATE users SET hashed_password = :hashed_password WHERE id = :id",
                    {'hashed_password': hashed_password, 'id': user_id}
                )
                session.commit()
                logger.info(f"Changed password for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def create_default_admin(self):
        """Create default admin user if no users exist"""
        try:
            with db_manager.get_session() as session:
                user_count = session.execute("SELECT COUNT(*) FROM users").scalar()
                
                if user_count == 0:
                    # Create default admin
                    default_password = secrets.token_urlsafe(12)
                    self.create_user(
                        username="admin",
                        email="admin@scoutai.com", 
                        password=default_password,
                        role=UserRole.ADMIN
                    )
                    logger.info(f"Created default admin user with password: {default_password}")
                    print(f"\n🔐 DEFAULT ADMIN CREDENTIALS:")
                    print(f"Username: admin")
                    print(f"Password: {default_password}")
                    print(f"Please change these credentials after first login!\n")
                    
        except Exception as e:
            logger.error(f"Error creating default admin: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

# Global authentication service instance
auth_service = AuthenticationService()