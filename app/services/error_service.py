"""Error handling service for standardized error management"""
from flask import flash, redirect, url_for, render_template, jsonify, current_app
from typing import Union, Tuple, Dict, Any, Optional, Callable
import traceback
import logging

class ErrorService:
    """Service for standardized error handling across the application"""
    
    @staticmethod
    def handle_error(error: Exception, error_type: str = 'general') -> Tuple[str, str]:
        """Process an exception and return appropriate message and category
        
        Args:
            error: The exception that occurred
            error_type: The type of error (e.g., 'database', 'auth', 'validation')
            
        Returns:
            Tuple containing (message, category)
        """
        # Log the error with traceback
        current_app.logger.error(f"{error_type.upper()} ERROR: {str(error)}\n{traceback.format_exc()}")
        
        # Handle specific error types
        if error_type == 'database':
            if 'UNIQUE constraint' in str(error):
                if 'username' in str(error):
                    return "Username already taken. Please choose a different username.", "danger"
                elif 'email' in str(error):
                    return "Email address already registered. Please use a different email.", "danger"
                elif 'subject_code' in str(error):
                    return "Subject code already exists. Please choose a different code.", "danger"
                else:
                    return "A record with this information already exists.", "danger"
            return f"Database error: {str(error)}", "danger"
        
        elif error_type == 'auth':
            return "Authentication error. Please check your credentials.", "danger"
        
        elif error_type == 'validation':
            return str(error), "warning"
        
        elif error_type == 'permission':
            return "You do not have permission to perform this action.", "danger"
        
        # Default error handling
        return f"An error occurred: {str(error)}", "danger"
    
    @staticmethod
    def flash_error(error: Exception, error_type: str = 'general') -> None:
        """Process an exception and flash an appropriate message
        
        Args:
            error: The exception that occurred
            error_type: The type of error
        """
        message, category = ErrorService.handle_error(error, error_type)
        flash(message, category)
    
    @staticmethod
    def api_error_response(error: Exception, error_type: str = 'general', 
                          status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """Create a standardized API error response
        
        Args:
            error: The exception that occurred
            error_type: The type of error
            status_code: The HTTP status code to return
            
        Returns:
            Tuple containing (response_dict, status_code)
        """
        message, _ = ErrorService.handle_error(error, error_type)
        
        response = {
            'success': False,
            'error': {
                'type': error_type,
                'message': message
            }
        }
        
        return response, status_code
    
    @staticmethod
    def register_error_handlers(app) -> None:
        """Register error handlers with the Flask application
        
        Args:
            app: The Flask application instance
        """
        @app.errorhandler(400)
        def handle_bad_request(e):
            if 'CSRF' in str(e):
                flash('Your session has expired. Please try again.', 'error')
                return redirect(url_for('auth.login'))
            return render_template('errors/400.html', error=str(e)), 400
        
        @app.errorhandler(401)
        def handle_unauthorized(e):
            return render_template('errors/401.html'), 401
        
        @app.errorhandler(403)
        def handle_forbidden(e):
            return render_template('errors/403.html'), 403
        
        @app.errorhandler(404)
        def handle_not_found(e):
            return render_template('errors/404.html'), 404
        
        @app.errorhandler(500)
        def handle_server_error(e):
            current_app.logger.error(f"Server error: {str(e)}\n{traceback.format_exc()}")
            return render_template('errors/500.html'), 500