"""Service layer for subject-related business logic"""
from app.models import db, Subject, StudentSubject, User
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
import logging

class SubjectService:
    """Service class for subject-related operations"""
    
    @staticmethod
    def get_subject_by_id(subject_id: int) -> Optional[Subject]:
        """Get a subject by ID"""
        try:
            return Subject.query.get_or_404(subject_id)
        except Exception as e:
            current_app.logger.error(f"Error retrieving subject {subject_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_subject_by_code(subject_code: str) -> Optional[Subject]:
        """Get a subject by code"""
        try:
            return Subject.query.filter_by(subject_code=subject_code).first()
        except Exception as e:
            current_app.logger.error(f"Error retrieving subject with code {subject_code}: {str(e)}")
            return None
    
    @staticmethod
    def create_subject(name: str, subject_code: str, teacher_id: int) -> Tuple[bool, str, Optional[Subject]]:
        """Create a new subject
        
        Returns:
            Tuple containing (success, message, subject_object)
        """
        try:
            # Check if subject code already exists
            existing_subject = Subject.query.filter_by(subject_code=subject_code).first()
            if existing_subject:
                return False, "Subject code already exists. Please choose a different code.", None
            
            # Create new subject
            subject = Subject(
                name=name,
                subject_code=subject_code,
                teacher_id=teacher_id
            )
            db.session.add(subject)
            db.session.commit()
            return True, "Subject created successfully!", subject
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error creating subject: {str(e)}")
            return False, f"Database error: {str(e)}", None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error creating subject: {str(e)}")
            return False, f"An error occurred: {str(e)}", None
    
    @staticmethod
    def enroll_student(student_id: int, subject_code: str) -> Tuple[bool, str, str]:
        """Enroll a student in a subject
        
        Returns:
            Tuple containing (success, message, status)
            where status can be 'new', 'pending', 'approved', 'rejected'
        """
        try:
            # Find the subject
            subject = Subject.query.filter_by(subject_code=subject_code).first()
            if not subject:
                return False, "Invalid subject code. Please check and try again.", ""
            
            # Check if already enrolled
            existing_enrollment = StudentSubject.query.filter_by(
                student_id=student_id,
                subject_id=subject.id
            ).first()
            
            if existing_enrollment:
                if existing_enrollment.enrollment_status == 'pending':
                    return False, "Your enrollment request is still pending teacher approval.", "pending"
                elif existing_enrollment.enrollment_status == 'approved':
                    return False, "You are already enrolled in this subject.", "approved"
                elif existing_enrollment.enrollment_status == 'rejected':
                    return False, "Your enrollment request was rejected. Please contact the teacher.", "rejected"
            
            # Create enrollment request
            enrollment = StudentSubject(student_id=student_id, subject_id=subject.id)
            
            # Check if auto-approval is enabled and if the student meets the criteria
            if subject.auto_approve_enabled:
                # Get the student's information
                student = User.query.get(student_id)
                if student:
                    auto_approved = False
                    
                    # Check domain whitelist if configured
                    if subject.domain_whitelist:
                        allowed_domains = [domain.strip() for domain in subject.domain_whitelist.split(',')]
                        student_email_domain = student.email.split('@')[-1] if '@' in student.email else ''
                        if student_email_domain and student_email_domain in allowed_domains:
                            auto_approved = True
                    
                    # Check student ID pattern if configured
                    if subject.student_id_pattern and not auto_approved:
                        import re
                        pattern = subject.student_id_pattern.strip()
                        if pattern and re.match(pattern, student.username):
                            auto_approved = True
                    
                    # Auto-approve if criteria met
                    if auto_approved:
                        enrollment.enrollment_status = 'approved'
                        db.session.add(enrollment)
                        db.session.commit()
                        return True, "You have been automatically enrolled in this subject based on verification criteria.", "approved"
            
            # If not auto-approved, proceed with regular enrollment request
            db.session.add(enrollment)
            db.session.commit()
            return True, "Enrollment request submitted. Waiting for teacher approval.", "new"
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error enrolling student: {str(e)}")
            return False, f"Database error: {str(e)}", ""
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error enrolling student: {str(e)}")
            return False, f"An error occurred: {str(e)}", ""
    
    @staticmethod
    def remove_student(subject_id: int, student_id: int, teacher_id: int) -> Tuple[bool, str]:
        """Remove a student from a subject
        
        Args:
            subject_id: The subject ID
            student_id: The student ID to remove
            teacher_id: The teacher ID (for permission check)
            
        Returns:
            Tuple containing (success, message)
        """
        try:
            # Get the subject
            subject = Subject.query.get_or_404(subject_id)
            
            # Check if the teacher owns the subject
            if subject.teacher_id != teacher_id:
                return False, "You do not have permission to remove students from this subject."
            
            # Get the enrollment
            enrollment = StudentSubject.query.filter_by(
                student_id=student_id,
                subject_id=subject_id
            ).first_or_404()
            
            # Remove enrollment
            db.session.delete(enrollment)
            db.session.commit()
            return True, "Student has been removed from the subject successfully."
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error removing student: {str(e)}")
            return False, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error removing student: {str(e)}")
            return False, f"An error occurred: {str(e)}"