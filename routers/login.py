from datetime import datetime, timedelta, timezone
from urllib.request import Request
from http.client import HTTPException
from fastapi import Depends, Request, APIRouter
import jwt 
import models
from database import get_db
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/login")
def login():
    return {"message": "Login successful! Backend response received 🎉"}

SECRET_KEY = "THIS_IS_HOGWARTS_PORTAL"  # Replace with a strong secret key
ALGORITHM = "HS256"  # You can use other algorithms, like RS256, if you want

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)  # Default 1-hour expiration
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
async def login_user(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "username": user.username
    }

#signup api
@router.post("/students/signup")
async def add_user(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get('userName')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not username or not email or not password or not role:
        raise HTTPException(status_code=400, detail="Missing required fields")

    existing_user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(password)

    new_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}

@router.get("/student/meta/{user_id}")
def get_student_meta(user_id: int, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter_by(user_id=user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student metadata not found")
    return {
        "student_id": student.id,
        "class_id": student.class_id
    }

@router.get("/teacher/meta/{user_id}")
def get_teacher_meta(user_id: int, db: Session = Depends(get_db)):
    teacher = db.query(models.Teacher).filter_by(user_id=user_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher metadata not found")
    return {
        "teacher_id": teacher.id,
        "subject": teacher.subject,
        "department": teacher.department,
    }
