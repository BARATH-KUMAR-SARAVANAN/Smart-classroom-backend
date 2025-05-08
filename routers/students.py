import shutil
from fastapi import FastAPI, UploadFile, File, Form, APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models import AssignmentQuestion, Student, Assignment, StudentResponse
from database import get_db
from typing import List, Optional
import json
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AssignmentQuestionSchema(BaseModel):
    id: int
    assignment_id: int
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    marks: int

    class Config:
        orm_mode = True

class StudentResponseSchema(BaseModel):
    assignment_id: int
    question_id: int
    student_id: int
    response: Optional[str] = None
    file_url: Optional[str] = None
  

@router.get("/{user_id}/assignments")
def get_student_assignments(user_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student or not student.class_id:
        raise HTTPException(status_code=404, detail="Student or class not found")

    assignments = db.query(Assignment).filter(Assignment.class_id == student.class_id).all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "subject": a.subject,
            "assignment_type": a.assignment_type.value,
            "due_date": a.due_date
        } for a in assignments
    ]


@router.get("/{assignment_id}/questions", response_model=List[AssignmentQuestionSchema])
def get_assignment_questions(assignment_id: int, db: Session = Depends(get_db)):
    questions = db.query(AssignmentQuestion).filter(AssignmentQuestion.assignment_id == assignment_id).all()

    if not questions:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 🔁 Convert stringified options to real list
    for q in questions:
        if isinstance(q.options, str):
            try:
                q.options = json.loads(q.options)
            except json.JSONDecodeError:
                q.options = []  # fallback to empty list if invalid JSON

    return questions


# Endpoint to submit student responses
@router.post("/student_responses/")
async def submit_student_responses(
    assignment_id: int = Form(...),
    student_id: int = Form(...),
    responses: str = Form(...),  # JSON string of responses
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    import json
    response_data = json.loads(responses)  # Expecting a list of dicts with question_id and response

    file_mapping = {}
    if files:
        for file in files:
            file_location = f"uploads/{file.filename}"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_mapping[file.filename] = file_location

    for resp in response_data:
        file_url = file_mapping.get(resp.get("file_name")) if resp.get("file_name") else None
        student_response = StudentResponse(
            assignment_id=assignment_id,
            question_id=resp["question_id"],
            student_id=student_id,
            response=resp.get("response"),
            file_url=file_url
        )
        db.add(student_response)
    db.commit()
    return {"message": "Responses submitted successfully"}