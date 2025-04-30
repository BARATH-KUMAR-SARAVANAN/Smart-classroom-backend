from http.client import HTTPException
from fastapi import Depends, FastAPI, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from passlib.context import CryptContext

app = FastAPI()
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    

# Enable CORS for frontend (important!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use exact domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/login")
def login():
    return {"message": "Login successful! Backend response received 🎉"}


@app.post("/students/signup")
async def add_user(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    username = data.get('userName')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not username or not email or not password or not role:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Check if username or email already exists
    existing_user = db.query(models.LoginDetails).filter(
        (models.LoginDetails.username == username) | (models.LoginDetails.email == email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(password)

    new_user = models.LoginDetails(
        username=username,
        email=email,
        password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is live!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)