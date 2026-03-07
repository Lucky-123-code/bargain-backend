from typing import Any, Dict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from database import get_db
from auth_utils import (
    get_current_user, 
    create_access_token, 
    get_password_hash, 
    verify_password
)
from constants import GOOGLE_CLIENT_ID, ERROR_USER_NOT_FOUND

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register(user_data: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Register a new user - expects {name, email, password}"""
    name = user_data.get("name")
    email = user_data.get("email")
    password = user_data.get("password")
    
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email and password are required")
    
    # Check if user already exists
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email}
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Insert new user
    db.execute(
        text(
            """
            INSERT INTO users (name, email, password, created_at)
            VALUES (:name, :email, :password, :created_at)
            """
        ),
        {
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now()
        }
    )
    db.commit()
    
    # Get the inserted user's id
    user = db.execute(
        text("SELECT id, name, email FROM users WHERE email = :email"),
        {"email": email}
    ).first()
    
    if not user:
        raise HTTPException(status_code=500, detail="Failed to retrieve user after registration")
    
    # Create JWT token
    token = create_access_token(data={"sub": str(user[0])})
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }


@router.post("/login")
def login(credentials: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """User login - expects {email, password}"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    
    # Find user
    user = db.execute(
        text("SELECT id, name, email, password FROM users WHERE email = :email"),
        {"email": email}
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(password, user[3]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = create_access_token(data={"sub": str(user[0])})
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }


@router.post("/google")
def google_auth(google_token: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Google OAuth login - expects {token} from Google"""
    token = google_token.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Google token is required")
    
    try:
        # Verify Google token
        idinfo = id_token.verify_token(token, google_requests.Request())
        
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Invalid Google token")
            
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google token verification failed: {str(e)}")
    
    # Check if user exists
    user = db.execute(
        text("SELECT id, name, email, password FROM users WHERE email = :email"),
        {"email": email}
    ).first()
    
    if not user:
        # Create new user with Google
        # For Google users, we'll set a placeholder password
        hashed_password = get_password_hash(f"google_{email}_{datetime.now().timestamp()}")
        
        db.execute(
            text(
                """
                INSERT INTO users (name, email, password, created_at)
                VALUES (:name, :email, :password, :created_at)
                """
            ),
            {
                "name": name,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.now()
            }
        )
        db.commit()
        
        user = db.execute(
            text("SELECT id, name, email FROM users WHERE email = :email"),
            {"email": email}
        ).first()
        
        if not user:
            raise HTTPException(status_code=500, detail="Failed to retrieve user after Google registration")
    
    # Create JWT token
    jwt_token = create_access_token(data={"sub": str(user[0])})
    
    return {
        "message": "Google login successful",
        "token": jwt_token,
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }


@router.post("/logout")
def logout() -> Dict[str, str]:
    """User logout"""
    return {"message": "Logged out successfully"}


@router.get("/me")
def get_current_user_info(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user info"""
    user_id = current_user.get("id")
    
    user = db.execute(
        text("SELECT id, name, email, created_at FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
    
    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "created_at": user[3]
    }


@router.put("/me")
def update_user_profile(
    user_data: Dict[str, str], 
    db: Session = Depends(get_db), 
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user profile - expects {name} (and optionally {password})"""
    user_id = current_user.get("id")
    name = user_data.get("name")
    password = user_data.get("password")
    
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    if password:
        # Update password if provided
        hashed_password = get_password_hash(password)
        db.execute(
            text("UPDATE users SET password = :password WHERE id = :user_id"),
            {"password": hashed_password, "user_id": user_id}
        )
    
    # Update name
    db.execute(
        text("UPDATE users SET name = :name WHERE id = :user_id"),
        {"name": name, "user_id": user_id}
    )
    db.commit()
    
    # Get updated user
    user = db.execute(
        text("SELECT id, name, email, created_at FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }
