import os
import hashlib
import json
import base64
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from database.db import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "quizgen_ai_secret_key_2026")

# Schemas
class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str
    role: str # 'faculty' or 'student'

class LoginSchema(BaseModel):
    email: str
    password: str

# Password Hashing Helper
def hash_password(password: str) -> str:
    salt = b"quizgen_salt_2026"
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return pwd_hash.hex()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# Lightweight JWT Token implementation
def create_access_token(user_id: int, email: str, role: str, name: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "name": name,
        "exp": int(time.time()) + (24 * 3600) # 24 hours
    }
    payload_str = json.dumps(payload)
    encoded_payload = base64.b64encode(payload_str.encode("utf-8")).decode("utf-8")
    signature = hashlib.sha256(f"{encoded_payload}.{SECRET_KEY}".encode("utf-8")).hexdigest()
    return f"{encoded_payload}.{signature}"

def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        encoded_payload, signature = parts
        expected_sig = hashlib.sha256(f"{encoded_payload}.{SECRET_KEY}".encode("utf-8")).hexdigest()
        if signature != expected_sig:
            return None
        
        payload_bytes = base64.b64decode(encoded_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

# Dependency to get current user from Authorization header
def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")
    
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token.")
    return payload

@router.post("/register")
def register(data: RegisterSchema):
    if data.role not in ["faculty", "student"]:
        raise HTTPException(status_code=400, detail="Role must be either 'faculty' or 'student'.")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (data.email.strip().lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    pwd_hashed = hash_password(data.password)
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (data.name.strip(), data.email.strip().lower(), pwd_hashed, data.role)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    token = create_access_token(user_id, data.email.strip().lower(), data.role, data.name.strip())
    return {
        "message": "User registered successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": data.name.strip(),
            "email": data.email.strip().lower(),
            "role": data.role
        }
    }

@router.post("/login")
def login(data: LoginSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE email = ?", (data.email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user["id"], user["email"], user["role"], user["name"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
