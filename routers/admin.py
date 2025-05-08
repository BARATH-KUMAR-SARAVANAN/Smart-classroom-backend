from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import models
from typing import List, Optional

router = APIRouter()

class AssignRoleRequest(BaseModel):
    user_id: int
    role: str
    grade: Optional[int] = None
    section: Optional[str] = None
    department: Optional[str] = None
    subject: Optional[str] = None
    
class ClassOut(BaseModel):
    id: int
    grade: str
    section: str

    class Config:
        orm_mode = True
   


@router.get("/unassigned-users")
def get_unassigned_users(db: Session = Depends(get_db)):
    student_ids = [s.user_id for s in db.query(models.Student).all()]
    teacher_ids = [t.user_id for t in db.query(models.Teacher).all()]
    parent_ids = [p.user_id for p in db.query(models.Parent).all()]
    assigned_ids = set(student_ids + teacher_ids + parent_ids)
    unassigned_users = db.query(models.User).filter(~models.User.id.in_(assigned_ids)).all()

    return [
        {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role
        }
        for user in unassigned_users
    ]

from fastapi import Request

@router.post("/assign-role")
async def assign_role(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    user_id = data.get("user_id")
    role = data.get("role")
    class_id = data.get("class_id")  # new field replacing grade & section
    department = data.get("department")
    subject = data.get("subject")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if role == "student":
        if class_id is None:
            raise HTTPException(status_code=400, detail="Class ID is required for students")

        # Validate that the class_id exists
        class_obj = db.query(models.Class).filter(models.Class.id == class_id).first()
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")

        new_student = models.Student(
            user_id=user_id,
            class_id=class_id
        )
        db.add(new_student)

    elif role == "teacher":
        if department is None or subject is None:
            raise HTTPException(status_code=400, detail="Department and subject are required for teachers")

        new_teacher = models.Teacher(
            user_id=user_id,
            department=department,
            subject=subject
        )
        db.add(new_teacher)

    else:
        raise HTTPException(status_code=400, detail="Invalid role")

    db.commit()
    return {"message": f"{role.capitalize()} assigned successfully"}

@router.get("/classes")
def get_all_classes(db: Session = Depends(get_db)):
    classes = db.query(models.Class).all()
    return [{"id": c.id, "grade": c.grade, "section": c.section} for c in classes]
