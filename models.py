from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime , Integer, String, ForeignKey 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class LoginDetails(Base):
    __tablename__ = 'login_details'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())
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
    grade = Column(String(10))
    section = Column(String(5))

    user = relationship("User", back_populates="student")

class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String(50))
    department = Column(String(50))

    user = relationship("User", back_populates="teacher")

# Parent Table
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
