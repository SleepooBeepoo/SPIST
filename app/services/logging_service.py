"""Logging service for standardized logging across the application"""
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask, has_request_context, request
from typing import Optional

class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request information when available"""
    
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            
        return super().format(record)

class LoggingService:
    """Service for standardized logging across the application"""
    
    @staticmethod
    def setup_logging(app: Flask, log_level: int = logging.INFO) -> None:
        """Configure application logging
        
        Args:
            app: The Flask application instance
            log_level: The logging level to use
        """
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(app.root_path, '..', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        # Set up file handler for application logs
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'app.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        
        # Create formatter with request context information
        formatter = RequestFormatter(
            '[%(asctime)s] %(remote_addr)s - %(method)s %(url)s\n'
            '%(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        
        # Set up error-specific log file
        error_file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'error.log'),
            maxBytes=10485760,
            backupCount=10
        )
        error_file_handler.setFormatter(formatter)
        error_file_handler.setLevel(logging.ERROR)
        
        # Add error handler to app logger
        app.logger.addHandler(error_file_handler)
        
        # Log application startup
        app.logger.info('Application startup')
    
    @staticmethod
    def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
        """Get a configured logger for a specific module
        
        Args:
            name: The name of the logger (typically __name__)
            log_level: The logging level to use
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Avoid adding handlers if they already exist
        if not logger.handlers:
            # Add console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger