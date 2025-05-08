from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class LoginDetails(Base):
    __tablename__ = 'login_details'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    
class User(Base):
  __tablename__ = 'users'
  
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(50), unique=True, nullable=False)
  email = Column(String(100), unique=True, nullable=False)
  hashed_password = Column(String(255), nullable=False)
  role = Column(String(20), nullable=False)  # 'student', 'teacher', 'parent', 'admin'
  created_at = Column(DateTime(timezone=True), server_default=func.now())

  # Relationships
  student = relationship("Student", back_populates="user", uselist=False)
  teacher = relationship("Teacher", back_populates="user", uselist=False)
  parent = relationship("Parent", back_populates="user", uselist=False)
  admin = relationship("Admin", back_populates="user", uselist=False)

class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    class_id = Column(Integer, ForeignKey('classes.id'))

    user = relationship("User", back_populates="student")
    class_ = relationship("Class")

class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String(10), nullable=False)
    department = Column(String(10), nullable=False)

    user = relationship("User", back_populates="teacher")

class Parent(Base):
    __tablename__ = 'parents'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    child_user_id = Column(Integer)  # Optional: FK to 'users.id' of child

    user = relationship("User", back_populates="parent")

class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="admin")

class Class(Base):
    __tablename__ = 'classes'

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String(10), nullable=False)
    section = Column(String(5), nullable=False)
    strength = Column(Integer, nullable=False)

    assignments = relationship("Assignment", back_populates="class_")

class AssignmentType(enum.Enum):
    mcq = "mcq"
    description = "description"
    file = "file"
    prob = "prob"

class Assignment(Base):
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    due_date = Column(DateTime, nullable=True)
    assignment_type = Column(Enum(AssignmentType), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    questions = relationship("AssignmentQuestion", back_populates="assignment")
    class_ = relationship("Class", back_populates="assignments")

class AssignmentQuestion(Base):
    __tablename__ = 'assignment_questions'

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # list of options for MCQ
    correct_answer = Column(String(255), nullable=True)
    marks = Column(Integer, nullable=False)

    assignment = relationship("Assignment", back_populates="questions")
    
class StudentResponse(Base):
    __tablename__ = 'student_responses'

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey('assignments.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('assignment_questions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    response = Column(Text, nullable=True)  # for text/mcq answers
    file_url = Column(String(255), nullable=True)  # for file submissions
    obtained_marks = Column(Integer, nullable=True)
    reviewed_by_ai = Column(Boolean, default=False)
    submitted_at = Column(DateTime, default=datetime.now)
