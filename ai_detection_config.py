# AI Detection Configuration

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configuration for AI content detection
class AIDetectionConfig:
    # API provider options: 'local', 'gptzero', 'originality'
    DEFAULT_PROVIDER = 'local'
    
    # Get API provider from environment variable or use default
    PROVIDER = os.environ.get('AI_DETECTION_PROVIDER', DEFAULT_PROVIDER)
    
    # API keys for different providers
    GPTZERO_API_KEY = os.environ.get('GPTZERO_API_KEY')
    ORIGINALITY_API_KEY = os.environ.get('ORIGINALITY_API_KEY')
    
    # Get the appropriate API key based on the provider
    @classmethod
    def get_api_key(cls):
        if cls.PROVIDER == 'gptzero':
            return cls.GPTZERO_API_KEY
        elif cls.PROVIDER == 'originality':
            return cls.ORIGINALITY_API_KEY
        return None
    
    # Instructions for setting up API keys
    @staticmethod
    def get_setup_instructions():
        return """
        To configure external AI detection APIs:
        
        1. Create a .env file in the root directory of the project
        2. Add your API keys and provider choice:
           
           # Choose one: 'local', 'gptzero', or 'originality'
           AI_DETECTION_PROVIDER=local
           
           # If using GPTZero
           GPTZERO_API_KEY=your_api_key_here
           
           # If using Originality.ai
           ORIGINALITY_API_KEY=your_api_key_here
        
        3. Restart the application for changes to take effect
        """