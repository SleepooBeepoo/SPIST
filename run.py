import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment or use default
config_name = os.environ.get('FLASK_CONFIG', 'development')

# Create app with the specified configuration
app = create_app(config_name)

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port)