"""Service layer for quiz-related business logic"""
from app.models import db, Quiz, Question, Subject, Announcement, QuizSubmission, StudentSubmission
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from datetime import datetime
import json
import logging

class QuizService:
    """Service class for quiz-related operations"""
    
    @staticmethod
    def get_quiz_by_id(quiz_id: int) -> Optional[Quiz]:
        """Get a quiz by ID
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            Quiz object or None if not found
        """
        try:
            return Quiz.query.get(quiz_id)
        except Exception as e:
            current_app.logger.error(f"Error retrieving quiz {quiz_id}: {str(e)}")
            return None
    
    @staticmethod
    def create_quiz(title: str, description: str, quiz_type: str, duration: Optional[int],
                   start_time: Optional[datetime], user_id: int, subject_id: int) -> Tuple[bool, str, Optional[Quiz]]:
        """Create a new quiz
        
        Args:
            title: The title of the quiz
            description: The description of the quiz
            quiz_type: The type of quiz ('quiz' or 'exam')
            duration: Optional duration in minutes
            start_time: Optional start time
            user_id: The ID of the user creating the quiz
            subject_id: The ID of the subject for the quiz
            
        Returns:
            Tuple containing (success, message, quiz_object)
        """
        try:
            # Create the quiz
            quiz = Quiz(
                title=title,
                description=description,
                quiz_type=quiz_type,
                duration=duration,
                start_time=start_time,
                user_id=user_id,
                subject_id=subject_id
            )
            db.session.add(quiz)
            db.session.commit()
            
            # Create announcement for the new quiz
            subject = Subject.query.get(subject_id)
            if subject:
                announcement = Announcement(
                    title=f'New {quiz.quiz_type.capitalize()} Available',
                    content=f'A new {quiz.quiz_type} "{quiz.title}" has been created for {subject.name}.',
                    user_id=user_id,
                    subject_id=subject_id,
                    quiz_id=quiz.id,
                    announcement_type='quiz_created'
                )
                db.session.add(announcement)
                db.session.commit()
            
            return True, f"{quiz_type.capitalize()} created successfully!", quiz
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating quiz: {str(e)}")
            return False, f"An error occurred while creating the {quiz_type}: {str(e)}", None
    
    @staticmethod
    def add_question(quiz_id: int, question_text: str, question_type: str, options: Optional[List[str]],
                    correct_answer: str, points: float, order_index: int, word_limit: Optional[int] = None) -> Tuple[bool, str, Optional[Question]]:
        """Add a question to a quiz
        
        Args:
            quiz_id: The ID of the quiz
            question_text: The text of the question
            question_type: The type of question
            options: Optional list of options for multiple choice questions
            correct_answer: The correct answer
            points: The points for the question
            order_index: The order index of the question
            word_limit: Optional word limit for essay questions
            
        Returns:
            Tuple containing (success, message, question_object)
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found", None
            
            # Process options for multiple choice questions
            options_json = None
            if question_type == 'multiple_choice' and options:
                options_json = json.dumps(options)
            
            question = Question(
                question_text=question_text,
                question_type=question_type,
                options=options_json,
                correct_answer=correct_answer,
                points=points,
                order_index=order_index,
                word_limit=word_limit,
                user_id=quiz.user_id,
                quiz_id=quiz_id
            )
            db.session.add(question)
            db.session.commit()
            
            return True, "Question added successfully!", question
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding question: {str(e)}")
            return False, f"An error occurred while adding the question: {str(e)}", None
    
    @staticmethod
    def get_quizzes_by_subject(subject_id: int) -> List[Quiz]:
        """Get all quizzes for a subject
        
        Args:
            subject_id: The ID of the subject
            
        Returns:
            List of Quiz objects
        """
        try:
            return Quiz.query.filter_by(subject_id=subject_id).order_by(Quiz.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving quizzes for subject {subject_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_quizzes_by_teacher(teacher_id: int) -> List[Quiz]:
        """Get all quizzes created by a teacher
        
        Args:
            teacher_id: The ID of the teacher
            
        Returns:
            List of Quiz objects
        """
        try:
            return Quiz.query.filter_by(user_id=teacher_id).order_by(Quiz.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving quizzes for teacher {teacher_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_quiz_submissions(quiz_id: int) -> List[QuizSubmission]:
        """Get all submissions for a quiz
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            List of QuizSubmission objects
        """
        try:
            return QuizSubmission.query.filter_by(quiz_id=quiz_id).order_by(QuizSubmission.submitted_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving submissions for quiz {quiz_id}: {str(e)}")
            return []
    
    @staticmethod
    def delete_quiz(quiz_id: int) -> Tuple[bool, str]:
        """Delete a quiz
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            Tuple containing (success, message)
        """
        try:
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return False, "Quiz not found"
            
            # Delete related announcements
            Announcement.query.filter_by(quiz_id=quiz_id).delete()
            
            # Delete related submissions
            submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
            for submission in submissions:
                StudentSubmission.query.filter_by(quiz_submission_id=submission.id).delete()
            
            QuizSubmission.query.filter_by(quiz_id=quiz_id).delete()
            
            # Delete related questions
            Question.query.filter_by(quiz_id=quiz_id).delete()
            
            # Delete the quiz
            db.session.delete(quiz)
            db.session.commit()
            
            return True, "Quiz deleted successfully!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
            return False, f"An error occurred while deleting the quiz: {str(e)}"