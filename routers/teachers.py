from datetime import datetime
import json
from typing import List, Optional
from pydantic import BaseModel
from requests import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
import google.generativeai as genai
from utils.prompt_template import generate_mcq_prompt,generate_descriptive_prompt, generate_math_problem_prompt, correction_prompt
from services.ai_service import generate_from_prompt
import models 
import os


class QuestionPayload(BaseModel):
    question_text: str
    options: Optional[dict] = None
    correct_answer: Optional[str] = None
    marks: int

class AssignmentPayload(BaseModel):
    class_id: int
    teacher_id: int
    title: str
    subject: str
    assignment_type: str  # "mcq", "description", or "file"
    due_date: Optional[datetime]
    questions: List[QuestionPayload]


class StudentResponseSchema(BaseModel):
    id: int
    assignment_id: int
    question_id: int
    student_id: int
    response: Optional[str]
    file_url: Optional[str]
    obtained_marks: Optional[int]
    reviewed_by_ai: bool
    submitted_at: datetime

    class Config:
        orm_mode = True

class GradeUpdateSchema(BaseModel):
    obtained_marks: int
    reviewed_by_ai: Optional[bool] = False


router = APIRouter()
@router.get("/check")
async def senddata(request:Request):
  return "success bro"

@router.post("/generate-questions")
async def generate_questions(request: Request):
    data = await request.json()
    topic = data.get("topic")
    grade = data.get("grade", "general")
    type = data.get("type")
    count = data.get("count")
    description = data.get("description")

    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")

    if type == "mcq":
      prompt = generate_mcq_prompt(count,topic,grade,description)
    elif type == "prob":
      prompt = generate_math_problem_prompt(count,topic,grade,description)
    else:
      prompt = generate_descriptive_prompt(count,topic,grade,description)
    try:
        response = generate_from_prompt(prompt)
        raw_output = response.text
    except Exception as e:
      print(f"AI model error: {str(e)}")
      raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")

    return {"questions": raw_output}

@router.get("/get-class-id")
def get_class_id(grade: str, section: str, db: Session = Depends(get_db)):
    class_obj = db.query(models.Class).filter_by(grade=grade, section=section).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"class_id": class_obj.id}


@router.post("/send-assignment")
async def send_assignment(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()

        # Parse ISO 8601 datetime safely
        try:
            due_date = datetime.fromisoformat(data["due_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

        new_assignment = models.Assignment(
            title=data["title"],
            subject=data["subject"],
            teacher_id=data["teacher_id"],
            class_id=data["class_id"],
            due_date=due_date,
            assignment_type=data["assignment_type"],
            created_at=datetime.now()
        )

        db.add(new_assignment)
        db.flush()  # get assignment ID

        for q in data["questions"]:
            question_kwargs = {
                "assignment_id": new_assignment.id,
                "question_text": q["question_text"],
                "marks": q["marks"]
            }
            if "options" in q:
                question_kwargs["options"] = q["options"]
            if "correct_answer" in q:
                question_kwargs["correct_answer"] = q["correct_answer"]

            question = models.AssignmentQuestion(**question_kwargs)
            db.add(question)

        db.commit()
        return {"message": "Assignment successfully posted"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")



@router.get("/assignments/{teacher_id}")
def get_assignments_by_teacher(teacher_id: int, db: Session = Depends(get_db)):
    assignments = db.query(models.Assignment).filter(models.Assignment.teacher_id == teacher_id).all()
    result = []
    for assignment in assignments:
        class_info = db.query(models.Class).filter(models.Class.id == assignment.class_id).first()
        result.append({
            "id": assignment.id,
            "title": assignment.title,
            "subject": assignment.subject,
            "class_name": f"{class_info.grade} {class_info.section}" if class_info else "N/A"
        })
    return result

@router.get("/assignments/{assignment_id}/submissions")
def get_submissions_by_assignment(assignment_id: int, db: Session = Depends(get_db)):
    responses = db.query(models.StudentResponse).filter(models.StudentResponse.assignment_id == assignment_id).all()
    result = []
    for response in responses:
        question = db.query(models.AssignmentQuestion).filter(models.AssignmentQuestion.id == response.question_id).first()
        student = db.query(models.Student).filter(models.Student.id == response.student_id).first()
        user = db.query(models.User).filter(models.User.id == student.user_id).first() if student else None
        result.append({
            "id": response.id,
            "student_name": user.username if user else "Unknown",
            "question_text": question.question_text if question else "Unknown",
            "response": response.response,
            "obtained_marks": response.obtained_marks
        })
    return result


@router.post("/submissions/{submission_id}/evaluate")
def evaluate_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(models.StudentResponse).filter(models.StudentResponse.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    question = db.query(models.AssignmentQuestion).filter(models.AssignmentQuestion.id == submission.question_id).first()
    assignment = db.query(models.Assignment).filter(models.Assignment.id == submission.assignment_id).first()

    if not question or not assignment:
        raise HTTPException(status_code=404, detail="Assignment or Question not found")

    assignment_type = assignment.assignment_type

    if assignment_type == models.AssignmentType.mcq:
        is_correct = submission.response.strip().lower() == question.correct_answer.strip().lower()
        submission.obtained_marks = question.marks if is_correct else 0
        submission.reviewed_by_ai = True

    elif assignment_type == models.AssignmentType.description:
        propmt =  correction_prompt(
            question=question.question_text,
            answer=submission.response,
            marks=question.marks
        )
        response = generate_from_prompt(propmt)
        try:
            result = json.loads(response)
            score = int(result.get("score", 0))
            feedback = result.get("feedback", "")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI response parsing failed: {str(e)}")
        submission.obtained_marks = score
        submission.reviewed_by_ai = True

    elif assignment_type in [models.AssignmentType.file, models.AssignmentType.prob]:
        # For manual review types
        submission.reviewed_by_ai = False
        submission.obtained_marks = None

    db.commit()
    db.refresh(submission)

    return {
        "id": submission.id,
        "question_text": question.question_text,
        "response": submission.response,
        "obtained_marks": submission.obtained_marks,
        "reviewed_by_ai": submission.reviewed_by_ai,
        "student_id": submission.student_id,
        "assignment_type": assignment_type.value
    }