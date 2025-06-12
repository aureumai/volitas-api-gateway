"""
Authentication middleware for Volitas backend.
Handles Supabase JWT verification and user session management.
"""

from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from typing import Optional, Dict, Any
import os
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.warning("Supabase credentials not found. Auth will be disabled.")
    supabase: Optional[Client] = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

security = HTTPBearer(auto_error=False)

class AuthError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthUser:
    """User object from Supabase auth"""
    def __init__(self, user_data: Dict[str, Any]):
        self.id = user_data.get("id")
        self.email = user_data.get("email")
        self.user_metadata = user_data.get("user_metadata", {})
        self.app_metadata = user_data.get("app_metadata", {})
        self.created_at = user_data.get("created_at")
        self.subscription_tier = self.app_metadata.get("subscription_tier", "free")
        self.subscription_status = self.app_metadata.get("subscription_status", "inactive")
        
    @property
    def full_name(self) -> str:
        return self.user_metadata.get("full_name", "")
        
    @property
    def is_pro(self) -> bool:
        return self.subscription_tier in ["professional", "enterprise"]
        
    @property
    def is_enterprise(self) -> bool:
        return self.subscription_tier == "enterprise"

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[AuthUser]:
    """
    Get current authenticated user from JWT token.
    Returns None if no token provided or if Supabase is not configured.
    """
    if not supabase:
        logger.warning("Supabase not configured, skipping auth")
        return None
        
    if not credentials:
        return None
        
    try:
        # Verify JWT token with Supabase
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response.user:
            raise AuthError("Invalid token")
            
        return AuthUser(user_response.user.model_dump())
        
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise AuthError("Invalid authentication token")

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthUser:
    """
    Require authentication. Raises 401 if user is not authenticated.
    """
    user = await get_current_user(credentials)
    if not user:
        raise AuthError("Authentication required")
    return user

def require_subscription_tier(required_tier: str):
    """
    Dependency factory to check if user has required subscription tier.
    
    Tier hierarchy: free < professional < enterprise
    """
    async def tier_checker(user: AuthUser = Depends(require_auth)) -> AuthUser:
        tier_levels = {
            "free": 0,
            "professional": 1,
            "enterprise": 2
        }
        
        user_level = tier_levels.get(user.subscription_tier, 0)
        required_level = tier_levels.get(required_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} subscription. "
                       f"Current tier: {user.subscription_tier}"
            )
        
        return user
    
    return tier_checker

# Convenience dependency aliases
require_professional = require_subscription_tier("professional")
require_enterprise = require_subscription_tier("enterprise")

def optional_auth(func):
    """
    Decorator for endpoints that work with or without authentication.
    Adds 'current_user' parameter that can be None.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get user without requiring auth
        credentials = kwargs.pop('credentials', None)
        current_user = await get_current_user(credentials) if credentials else None
        return await func(*args, current_user=current_user, **kwargs)
    
    return wrapper

# Widget access control
WIDGET_TIERS = {
    'line': 'free',
    'bar': 'free', 
    'candlestick': 'professional',
    'treemap': 'professional',
    'volatilitycalendar': 'enterprise',
    'correlation': 'enterprise',
    'sankey': 'enterprise'
}

async def check_widget_access(widget_type: str, user: AuthUser = Depends(require_auth)):
    """Check if user has access to a specific widget type"""
    required_tier = WIDGET_TIERS.get(widget_type, 'free')
    
    tier_levels = {
        "free": 0,
        "professional": 1, 
        "enterprise": 2
    }
    
    user_level = tier_levels.get(user.subscription_tier, 0)
    required_level = tier_levels.get(required_tier, 0)
    
    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Widget '{widget_type}' requires {required_tier} subscription"
        )
    
    return user
