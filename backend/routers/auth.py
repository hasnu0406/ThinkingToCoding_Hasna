import hashlib
import secrets
import datetime
from fastapi import APIRouter, HTTPException, status
from models import UserRegisterRequest, UserLoginRequest
from database import users_collection

router = APIRouter(prefix="/auth", tags=["Authentication"])

def hash_password(password: str, salt: str) -> str:
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    return hash_obj.hexdigest()

@router.post("/register")
def register(data: UserRegisterRequest):
    name = data.name.strip()
    email = data.email.strip().lower()
    password = data.password
    
    # Check if user already exists by email
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
        
    # Generate salt and password hash
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    
    # Store user
    users_collection.insert_one({
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "salt": salt,
        "created_at": datetime.datetime.utcnow()
    })
    
    return {"message": "Registration successful", "email": email, "name": name}

@router.post("/login")
def login(data: UserLoginRequest):
    email = data.email.strip().lower()
    password = data.password
    
    # Find user by email
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Verify hash
    salt = user["salt"]
    password_hash = hash_password(password, salt)
    
    if password_hash != user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Generate a simple token
    token = f"session_{secrets.token_hex(24)}"
    
    return {
        "message": "Login successful",
        "email": email,
        "name": user.get("name", "User"),
        "access_token": token,
        "token_type": "bearer"
    }
