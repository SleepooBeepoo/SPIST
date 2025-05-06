"""Configuration service for managing application settings"""
import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import logging

# Load environment variables from .env file
load_dotenv()

class ConfigService:
    """Service for managing application configuration"""
    
    @staticmethod
    def get_env_var(key: str, default: Optional[Any] = None) -> Any:
        """Get an environment variable with a default fallback
        
        Args:
            key: The environment variable key
            default: The default value if the key is not found
            
        Returns:
            The environment variable value or the default
        """
        return os.environ.get(key, default)
    
    @staticmethod
    def get_secret_key() -> str:
        """Get the application secret key
        
        Returns:
            The secret key from environment or a default (for development only)
        """
        secret_key = ConfigService.get_env_var('SECRET_KEY')
        if not secret_key:
            # Log a warning if using default secret key
            logging.warning("Using default secret key. This is insecure for production.")
            secret_key = 'dev-default-secret-key-change-in-production'
        return secret_key
    
    @staticmethod
    def get_database_uri() -> str:
        """Get the database URI
        
        Returns:
            The database URI from environment or a default SQLite path
        """
        db_uri = ConfigService.get_env_var('DATABASE_URI')
        if not db_uri:
            # Construct a default SQLite URI
            instance_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance')
            if not os.path.exists(instance_path):
                os.makedirs(instance_path, exist_ok=True)
            db_path = os.path.join(instance_path, 'users.db')
            db_uri = f'sqlite:///{db_path}'
        return db_uri
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get the full application configuration
        
        Returns:
            Dictionary containing all configuration settings
        """
        return {
            'SECRET_KEY': ConfigService.get_secret_key(),
            'SQLALCHEMY_DATABASE_URI': ConfigService.get_database_uri(),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'WTF_CSRF_TIME_LIMIT': int(ConfigService.get_env_var('WTF_CSRF_TIME_LIMIT', 86400)),
            'DEBUG': ConfigService.get_env_var('FLASK_DEBUG', 'False').lower() in ('true', '1', 't'),
            'TESTING': ConfigService.get_env_var('FLASK_TESTING', 'False').lower() in ('true', '1', 't'),
        }