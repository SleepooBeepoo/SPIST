"""Service layer for question-related business logic"""
from app.models import db, Question, Quiz, StudentSubmission
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
import json
import logging

class QuestionService:
    """Service class for question-related operations"""
    
    @staticmethod
    def get_question_by_id(question_id: int) -> Optional[Question]:
        """Get a question by ID
        
        Args:
            question_id: The ID of the question
            
        Returns:
            Question object or None if not found
        """
        try:
            return Question.query.get(question_id)
        except Exception as e:
            current_app.logger.error(f"Error retrieving question {question_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_questions_by_quiz(quiz_id: int) -> List[Question]:
        """Get all questions for a quiz
        
        Args:
            quiz_id: The ID of the quiz
            
        Returns:
            List of Question objects
        """
        try:
            return Question.query.filter_by(quiz_id=quiz_id).order_by(Question.order_index).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving questions for quiz {quiz_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_questions_by_teacher(teacher_id: int) -> List[Question]:
        """Get all questions created by a teacher
        
        Args:
            teacher_id: The ID of the teacher
            
        Returns:
            List of Question objects
        """
        try:
            return Question.query.filter_by(user_id=teacher_id).order_by(Question.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error retrieving questions for teacher {teacher_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_question(question_text: str, question_type: str, options: Optional[List[str]],
                       correct_answer: str, points: float, user_id: int,
                       quiz_id: Optional[int] = None, word_limit: Optional[int] = None,
                       order_index: int = 0) -> Tuple[bool, str, Optional[Question]]:
        """Create a new question
        
        Args:
            question_text: The text of the question
            question_type: The type of question
            options: Optional list of options for multiple choice questions
            correct_answer: The correct answer
            points: The points for the question
            user_id: The ID of the user creating the question
            quiz_id: Optional ID of the quiz for the question
            word_limit: Optional word limit for essay questions
            order_index: The order index of the question
            
        Returns:
            Tuple containing (success, message, question_object)
        """
        try:
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
                user_id=user_id,
                quiz_id=quiz_id
            )
            db.session.add(question)
            db.session.commit()
            
            return True, "Question created successfully!", question
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating question: {str(e)}")
            return False, f"An error occurred while creating the question: {str(e)}", None
    
    @staticmethod
    def update_question(question_id: int, question_text: str, question_type: str,
                       options: Optional[List[str]], correct_answer: str, points: float,
                       word_limit: Optional[int] = None) -> Tuple[bool, str, Optional[Question]]:
        """Update an existing question
        
        Args:
            question_id: The ID of the question to update
            question_text: The updated text of the question
            question_type: The updated type of question
            options: Optional updated list of options for multiple choice questions
            correct_answer: The updated correct answer
            points: The updated points for the question
            word_limit: Optional updated word limit for essay questions
            
        Returns:
            Tuple containing (success, message, question_object)
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                return False, "Question not found", None
            
            # Process options for multiple choice questions
            options_json = None
            if question_type == 'multiple_choice' and options:
                options_json = json.dumps(options)
            
            question.question_text = question_text
            question.question_type = question_type
            question.options = options_json
            question.correct_answer = correct_answer
            question.points = points
            question.word_limit = word_limit
            
            db.session.commit()
            
            return True, "Question updated successfully!", question
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating question {question_id}: {str(e)}")
            return False, f"An error occurred while updating the question: {str(e)}", None
    
    @staticmethod
    def delete_question(question_id: int) -> Tuple[bool, str]:
        """Delete a question
        
        Args:
            question_id: The ID of the question to delete
            
        Returns:
            Tuple containing (success, message)
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                return False, "Question not found"
            
            # Delete related submissions
            StudentSubmission.query.filter_by(question_id=question_id).delete()
            
            # Delete the question
            db.session.delete(question)
            db.session.commit()
            
            return True, "Question deleted successfully!"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting question {question_id}: {str(e)}")
            return False, f"An error occurred while deleting the question: {str(e)}"
    
    @staticmethod
    def validate_answer(question_id: int, submitted_answer: str) -> Tuple[bool, float, str]:
        """Validate a submitted answer against the correct answer
        
        Args:
            question_id: The ID of the question
            submitted_answer: The submitted answer
            
        Returns:
            Tuple containing (is_correct, points_earned, feedback)
        """
        try:
            question = Question.query.get(question_id)
            if not question:
                return False, 0, "Question not found"
            
            # For essay questions, return True as they require manual grading
            if question.question_type == 'essay':
                return True, 0, "Essay question - requires manual grading"
            
            # For identification questions, we'll allow manual grading
            # but still check for exact matches for automatic grading
            if question.question_type == 'identification':
                is_correct = question.validate_answer(submitted_answer)
                if is_correct:
                    # If exact match, automatically grade as correct
                    return True, question.points, "Correct answer!"
                else:
                    # If not exact match, mark for manual grading
                    return False, 0, "Identification question - requires manual grading"
            
            # Validate the answer using the model's validate_answer method
            is_correct = question.validate_answer(submitted_answer)
            
            # Ensure is_correct is always a boolean, never None
            if is_correct is None:
                is_correct = False
                
            points_earned = question.points if is_correct else 0
            feedback = "Correct!" if is_correct else "Incorrect"
            
            return is_correct, points_earned, feedback
        except Exception as e:
            current_app.logger.error(f"Error validating answer for question {question_id}: {str(e)}")
            return False, 0, f"An error occurred while validating the answer: {str(e)}"