from http.client import HTTPException
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import login, students, teachers, admin

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # use exact domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.include_router(login.router, prefix="/auth", tags=["Authentication"])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(teachers.router, prefix="/teachers", tags=["Teachers"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is live!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)