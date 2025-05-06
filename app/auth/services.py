"""Service layer for authentication-related business logic"""
from app.models import db, User, Subject
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import logging

class AuthService:
    """Service class for authentication-related operations"""
    
    @staticmethod
    def login_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Authenticate a user
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            Tuple containing (success, message, user_object)
        """
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return False, "Invalid username or password", None
                
            if not user.check_password(password):
                return False, "Invalid username or password", None
                
            return True, "Login successful", user
        except Exception as e:
            current_app.logger.error(f"Error during login: {str(e)}")
            return False, f"An error occurred during login: {str(e)}", None
    
    @staticmethod
    def register_user(username: str, email: str, password: str, role: str, 
                      subject_code: Optional[str] = None) -> Tuple[bool, str, Optional[User]]:
        """Register a new user
        
        Args:
            username: The username for the new user
            email: The email for the new user
            password: The password for the new user
            role: The role for the new user (teacher or student)
            subject_code: Optional subject code for teachers
            
        Returns:
            Tuple containing (success, message, user_object)
        """
        try:
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                return False, "Email address already registered. Please use a different email.", None
                
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                return False, "Username already taken. Please choose a different username.", None
            
            # Create new user
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            
            # If teacher, create initial subject
            subject = None
            if role == 'teacher' and subject_code:
                # Check if subject code already exists
                if Subject.query.filter_by(subject_code=subject_code).first():
                    return False, "Subject code already exists. Please choose a different code.", None
                    
                subject = Subject(
                    name=f"{username}'s Class", 
                    subject_code=subject_code,
                    teacher_id=user.id
                )
                db.session.add(subject)
            
            db.session.commit()
            return True, "Registration successful! Please login.", user
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {str(e)}")
            
            if 'UNIQUE constraint' in str(e):
                if 'username' in str(e):
                    return False, "Username already taken. Please choose a different username.", None
                else:
                    return False, "Email address already registered. Please use a different email.", None
            else:
                return False, f"Database error: {str(e)}", None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error during registration: {str(e)}")
            return False, f"An error occurred during registration: {str(e)}", None