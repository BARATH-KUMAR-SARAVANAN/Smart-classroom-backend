from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from requests import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
import google.generativeai as genai
from utils.prompt_template import generate_mcq_prompt,generate_descriptive_prompt, generate_math_problem_prompt
from services.ai_service import generate_from_prompt
import models
import json
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


router = APIRouter()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # Store your key securely in env variable
model = genai.GenerativeModel("gemini-2.0-flash")

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