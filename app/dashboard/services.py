"""Service layer for dashboard-related business logic"""
from app.models import db, Subject, StudentSubject, User, Question, Quiz, QuizSubmission, Announcement
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
import logging

class DashboardService:
    """Service class for dashboard-related operations"""
    
    @staticmethod
    def get_teacher_dashboard_data(teacher_id: int) -> Dict[str, Any]:
        """Get data for teacher dashboard
        
        Args:
            teacher_id: The ID of the teacher
            
        Returns:
            Dictionary containing dashboard data
        """
        try:
            # Get teacher's subjects
            subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
            
            # Get teacher's questions
            questions = Question.query.filter_by(user_id=teacher_id).all()
            
            # Get quiz submissions for teacher's quizzes
            quiz_submissions = QuizSubmission.query.join(Quiz).filter(Quiz.user_id == teacher_id).all()
            
            # Get teacher's quizzes
            quizzes = Quiz.query.filter_by(user_id=teacher_id).all()
            
            # Get pending enrollments for teacher's subjects
            pending_enrollments = StudentSubject.query.join(Subject).filter(
                Subject.teacher_id == teacher_id,
                StudentSubject.enrollment_status == 'pending'
            ).all()
            
            # Get submission announcements for teacher
            submission_announcements = Announcement.query.join(Quiz).filter(
                Quiz.user_id == teacher_id,
                Announcement.announcement_type == 'submission_received'
            ).order_by(Announcement.created_at.desc()).limit(10).all()
            
            return {
                'subjects': subjects,
                'questions': questions,
                'quiz_submissions': quiz_submissions,
                'quizzes': quizzes,
                'pending_enrollments': pending_enrollments,
                'announcements': submission_announcements,
                'title': 'Teacher Dashboard'
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error retrieving teacher dashboard data: {str(e)}")
            return {
                'error': f"Database error: {str(e)}",
                'title': 'Teacher Dashboard'
            }
        except Exception as e:
            current_app.logger.error(f"Unexpected error retrieving teacher dashboard data: {str(e)}")
            return {
                'error': f"An error occurred: {str(e)}",
                'title': 'Teacher Dashboard'
            }
    
    @staticmethod
    def get_student_dashboard_data(student_id: int) -> Dict[str, Any]:
        """Get data for student dashboard
        
        Args:
            student_id: The ID of the student
            
        Returns:
            Dictionary containing dashboard data
        """
        try:
            # Get student's enrollments
            enrollments = StudentSubject.query.filter_by(student_id=student_id).all()
            
            # Get student's quiz submissions
            quiz_submissions = QuizSubmission.query.filter_by(student_id=student_id).order_by(QuizSubmission.submitted_at.desc()).all()
            
            # Get quiz announcements for student's enrolled subjects
            enrolled_subject_ids = [enrollment.subject_id for enrollment in enrollments if enrollment.enrollment_status == 'approved']
            quiz_announcements = Announcement.query.filter(
                Announcement.subject_id.in_(enrolled_subject_ids) if enrolled_subject_ids else False,
                Announcement.announcement_type == 'quiz_created'
            ).order_by(Announcement.created_at.desc()).limit(10).all()
            
            return {
                'enrollments': enrollments,
                'quiz_submissions': quiz_submissions,
                'announcements': quiz_announcements,
                'title': 'Student Dashboard'
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error retrieving student dashboard data: {str(e)}")
            return {
                'error': f"Database error: {str(e)}",
                'title': 'Student Dashboard'
            }
        except Exception as e:
            current_app.logger.error(f"Unexpected error retrieving student dashboard data: {str(e)}")
            return {
                'error': f"An error occurred: {str(e)}",
                'title': 'Student Dashboard'
            }
    
    @staticmethod
    def update_enrollment_status(student_id: int, subject_id: int, teacher_id: int, 
                                status: str) -> Tuple[bool, str]:
        """Update a student's enrollment status
        
        Args:
            student_id: The student ID
            subject_id: The subject ID
            teacher_id: The teacher ID (for permission check)
            status: The new status ('approved' or 'rejected')
            
        Returns:
            Tuple containing (success, message)
        """
        try:
            # Get the subject
            subject = Subject.query.get_or_404(subject_id)
            
            # Check if the teacher owns the subject
            if subject.teacher_id != teacher_id:
                return False, f"You do not have permission to {status} enrollments for this subject."
            
            # Get the enrollment
            enrollment = StudentSubject.query.filter_by(
                student_id=student_id,
                subject_id=subject_id
            ).first_or_404()
            
            # Update enrollment status
            enrollment.enrollment_status = status
            db.session.commit()
            
            status_message = "approved" if status == "approved" else "rejected"
            return True, f"Enrollment {status_message} successfully."
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating enrollment status: {str(e)}")
            return False, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error updating enrollment status: {str(e)}")
            return False, f"An error occurred: {str(e)}"