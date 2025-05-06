"""Service layer for submission-related business logic"""
from app.models import db, QuizSubmission, StudentSubmission, Quiz, Question, User, Announcement
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from datetime import datetime
import logging

class SubmissionService:
    """Service class for submission-related operations"""
    
    @staticmethod
    def get_quiz_submission_by_id(submission_id: int) -> Optional[QuizSubmission]:
        """Get a quiz submission by ID
        
        Args:
            submission_id: The ID of the quiz submission
            
        Returns:
            QuizSubmission object or None if not found
        """
        try:
            return QuizSubmission.query.get(submission_id)
        except Exception as e:
            current_app.logger.error(f"Error retrieving quiz submission {submission_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_quiz_submissions_by_student(student_id: int) -> List[QuizSubmission]:
        """Get all quiz submissions for a student
        
        Args:
            student_id: The ID of the student
            
        Returns:
            List of QuizSubmission objects
        """
        try:
            return QuizSubmission.query.filter_by(student_id=student_id).order_by(QuizSubmission.submitted_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving quiz submissions for student {student_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_quiz_submissions_by_quiz(quiz_id: int) -> List[QuizSubmission]:
        """Get all quiz submissions for a quiz
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            List of QuizSubmission objects
        """
        try:
            return QuizSubmission.query.filter_by(quiz_id=quiz_id).order_by(QuizSubmission.submitted_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving quiz submissions for quiz {quiz_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_quiz_submission(quiz_id: int, student_id: int, total_score: float = 0.0,
                              is_graded: bool = False) -> Tuple[bool, str, Optional[QuizSubmission]]:
        """Create a new quiz submission
        
        Args:
            quiz_id: The ID of the quiz
            student_id: The ID of the student
            total_score: The total score for the submission
            is_graded: Whether the submission has been graded
            
        Returns:
            Tuple containing (success, message, quiz_submission_object)
        """
        try:
            # Check if quiz exists
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found", None
            
            # Check if student exists
            student = User.query.get(student_id)
            if not student or student.role != 'student':
                return False, "Student not found", None
            
            # Check if student has already submitted this quiz
            existing_submission = QuizSubmission.query.filter_by(quiz_id=quiz_id, student_id=student_id).first()
            if existing_submission:
                return False, "You have already submitted this quiz", None
            
            # Create quiz submission
            quiz_submission = QuizSubmission(
                quiz_id=quiz_id,
                student_id=student_id,
                total_score=total_score,
                is_graded=is_graded,
                submitted_at=datetime.utcnow()
            )
            db.session.add(quiz_submission)
            db.session.commit()
            
            # Create announcement for the teacher
            announcement = Announcement(
                title=f'New Submission Received',
                content=f'{student.username} has submitted {quiz.title}.',
                user_id=quiz.user_id,  # Teacher who created the quiz
                subject_id=quiz.subject_id,
                quiz_id=quiz.id,
                announcement_type='submission_received'
            )
            db.session.add(announcement)
            db.session.commit()
            
            return True, "Quiz submitted successfully!", quiz_submission
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating quiz submission: {str(e)}")
            return False, f"An error occurred while submitting the quiz: {str(e)}", None
    
    @staticmethod
    def create_student_submission(quiz_submission_id: int, question_id: int, answer: str,
                                 is_correct: bool = False, score: float = 0.0,
                                 feedback: str = None) -> Tuple[bool, str, Optional[StudentSubmission]]:
        """Create a new student submission for a question
        
        Args:
            quiz_submission_id: The ID of the quiz submission
            question_id: The ID of the question
            answer: The student's answer
            is_correct: Whether the answer is correct (defaults to False for missing answers)
            score: The score for the answer
            feedback: Optional feedback for the answer
            
        Returns:
            Tuple containing (success, message, student_submission_object)
        """
        try:
            # Check if quiz submission exists
            quiz_submission = QuizSubmission.query.get(quiz_submission_id)
            if not quiz_submission:
                return False, "Quiz submission not found", None
            
            # Check if question exists
            question = Question.query.get(question_id)
            if not question:
                return False, "Question not found", None
            
            # Create student submission
            student_submission = StudentSubmission(
                quiz_submission_id=quiz_submission_id,
                question_id=question_id,
                answer=answer,
                is_correct=is_correct,
                score=score,
                feedback=feedback
            )
            db.session.add(student_submission)
            db.session.commit()
            
            return True, "Answer submitted successfully!", student_submission
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating student submission: {str(e)}")
            return False, f"An error occurred while submitting the answer: {str(e)}", None
    
    @staticmethod
    def grade_submission(quiz_submission_id: int, total_score: float,
                        feedback: Dict[int, Dict[str, Any]]) -> Tuple[bool, str, Optional[QuizSubmission]]:
        """Grade a quiz submission
        
        Args:
            quiz_submission_id: The ID of the quiz submission
            total_score: The total score for the submission
            feedback: Dictionary mapping question IDs to feedback dictionaries
                      Each feedback dictionary should have 'score' and 'feedback' keys
            
        Returns:
            Tuple containing (success, message, quiz_submission_object)
        """
        try:
            # Check if quiz submission exists
            quiz_submission = QuizSubmission.query.get(quiz_submission_id)
            if not quiz_submission:
                return False, "Quiz submission not found", None
            
            # Update quiz submission
            quiz_submission.total_score = total_score
            quiz_submission.is_graded = True
            quiz_submission.graded_at = datetime.utcnow()
            
            # Update student submissions with feedback
            for question_id, question_feedback in feedback.items():
                student_submission = StudentSubmission.query.filter_by(
                    quiz_submission_id=quiz_submission_id,
                    question_id=question_id
                ).first()
                
                if student_submission:
                    student_submission.score = question_feedback.get('score', 0.0)
                    student_submission.feedback = question_feedback.get('feedback', '')
                    student_submission.is_correct = question_feedback.get('score', 0.0) > 0
            
            db.session.commit()
            
            return True, "Submission graded successfully!", quiz_submission
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error grading submission {quiz_submission_id}: {str(e)}")
            return False, f"An error occurred while grading the submission: {str(e)}", None
    
    @staticmethod
    def get_student_submissions_by_quiz_submission(quiz_submission_id: int) -> List[StudentSubmission]:
        """Get all student submissions for a quiz submission
        
        Args:
            quiz_submission_id: The ID of the quiz submission
            
        Returns:
            List of StudentSubmission objects
        """
        try:
            return StudentSubmission.query.filter_by(quiz_submission_id=quiz_submission_id).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving student submissions for quiz submission {quiz_submission_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_student_submission(quiz_submission_id: int, question_id: int) -> Optional[StudentSubmission]:
        """Get a student submission for a specific question in a quiz submission
        
        Args:
            quiz_submission_id: The ID of the quiz submission
            question_id: The ID of the question
            
        Returns:
            StudentSubmission object or None if not found
        """
        try:
            return StudentSubmission.query.filter_by(
                quiz_submission_id=quiz_submission_id,
                question_id=question_id
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error retrieving student submission for quiz submission {quiz_submission_id}, question {question_id}: {str(e)}")
            return None