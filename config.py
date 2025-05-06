import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    # Secret key should be set in environment variables for security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CSRF protection settings
    WTF_CSRF_TIME_LIMIT = 86400  # 24 hours in seconds
    
    # Application settings
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Database path configuration
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'users.db')
        return f'sqlite:///{db_path}'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration"""
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # In production, use environment variable for database URI
        return os.environ.get('DATABASE_URI', 'sqlite:///instance/users.db')

# Configuration dictionary
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name='default'):
    """Get configuration class based on environment"""
    return config_dict.get(config_name, config_dict['default'])()