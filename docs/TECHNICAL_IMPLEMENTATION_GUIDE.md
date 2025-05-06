# Educational Assessment Platform - Technical Implementation Guide

## Table of Contents
1. [Setup and Installation](#setup-and-installation)
2. [Configuration](#configuration)
3. [Development Guidelines](#development-guidelines)
4. [Testing](#testing)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

## Setup and Installation

### Prerequisites

- Python 3.9+ installed
- Git (for version control)
- SQLite (included with Python)

### Installation Steps

1. Clone the repository (if applicable):
   ```bash
   git clone <repository-url>
   cd educational-assessment-platform
   ```

2. Create a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True  # Set to False in production
   DATABASE_URI=sqlite:///instance/users.db
   WTF_CSRF_TIME_LIMIT=86400
   AI_DETECTION_PROVIDER=local
   # Optional: Add API keys for external AI detection services
   # GPTZERO_API_KEY=your-api-key-here
   # ORIGINALITY_API_KEY=your-api-key-here
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the application:
   ```bash
   python run.py
   ```

7. Access the application at `http://127.0.0.1:5000`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| SECRET_KEY | Flask secret key for session security | dev-default-secret-key-change-in-production |
| DATABASE_URI | Database connection string | sqlite:///instance/users.db |
| FLASK_DEBUG | Enable debug mode | False |
| FLASK_TESTING | Enable testing mode | False |
| WTF_CSRF_TIME_LIMIT | CSRF token expiry in seconds | 86400 (24 hours) |
| AI_DETECTION_PROVIDER | Provider for AI detection ('local', 'gptzero', 'originality') | local |
| GPTZERO_API_KEY | API key for GPTZero integration | None |
| ORIGINALITY_API_KEY | API key for Originality.ai integration | None |

### Configuration Service

The platform uses a dedicated configuration service to manage environment variables:

```python
class ConfigService:
    """Service for centralizing environment variable handling"""
    
    @staticmethod
    def get_config(app):
        """Load configuration from environment variables
        
        Args:
            app: The Flask application instance
        """
        # Load .env file if it exists
        dotenv_path = os.path.join(os.path.dirname(app.root_path), '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        
        # Set configuration from environment variables
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-default-secret-key-change-in-production')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///instance/users.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_TIME_LIMIT'] = int(os.environ.get('WTF_CSRF_TIME_LIMIT', 86400))  # 24 hours
        
        # AI detection configuration
        app.config['AI_DETECTION_PROVIDER'] = os.environ.get('AI_DETECTION_PROVIDER', 'local')
        app.config['GPTZERO_API_KEY'] = os.environ.get('GPTZERO_API_KEY')
        app.config['ORIGINALITY_API_KEY'] = os.environ.get('ORIGINALITY_API_KEY')
```

## Development Guidelines

### Project Structure

The application follows a modular structure with blueprints and a service layer:

```
app/
├── __init__.py           # Application factory
├── auth/                 # Authentication module
├── dashboard/            # Dashboard module
├── main/                 # Main pages module
├── models.py             # Database models
├── quiz/                 # Quiz module
├── question/             # Question module
├── submission/           # Submission module
├── services/             # Shared services
├── subject/              # Subject module
└── utils/                # Utility functions
```

### Adding a New Feature

1. **Identify the appropriate module** for your feature
2. **Create or update models** in `models.py` if needed
3. **Implement business logic** in the appropriate service class
4. **Create forms** for user input if needed
5. **Add routes** to handle HTTP requests
6. **Create templates** for the user interface
7. **Update tests** to cover the new functionality

### Coding Standards

- Use **type annotations** for all function parameters and return values
- Add **docstrings** to all classes and functions
- Follow **PEP 8** style guidelines
- Use **consistent error handling** through the error service
- Implement **proper logging** using the logging service

### Example: Adding a New Service

```python
from typing import Dict, Any, List, Optional
from flask import current_app

class NewFeatureService:
    """Service for handling new feature functionality"""
    
    def __init__(self):
        """Initialize the service"""
        pass
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for the new feature
        
        Args:
            data: The input data to process
            
        Returns:
            Processed data
        """
        try:
            # Implementation
            result = {}
            # ...
            return result
        except Exception as e:
            current_app.logger.error(f"Error processing data: {str(e)}")
            raise
```

## Testing

### Running Tests

The platform uses pytest for testing:

```bash
python -m pytest
```

To run tests with coverage:

```bash
python -m pytest --cov=app tests/
```

### Writing Tests

#### Example: Testing a Service

```python
import pytest
from app.services.some_service import SomeService

def test_service_function():
    """Test a specific function in the service"""
    # Arrange
    service = SomeService()
    test_input = {"key": "value"}
    expected_output = {"processed": True}
    
    # Act
    result = service.process_data(test_input)
    
    # Assert
    assert result == expected_output
```

#### Example: Testing a Route

```python
def test_route(client):
    """Test a specific route"""
    # Arrange
    # ...
    
    # Act
    response = client.get('/some-route')
    
    # Assert
    assert response.status_code == 200
    assert b"Expected content" in response.data
```

## Deployment

### Production Configuration

1. Create a production `.env` file with secure settings:
   ```
   SECRET_KEY=your-secure-random-key
   FLASK_DEBUG=False
   DATABASE_URI=sqlite:///instance/users.db
   WTF_CSRF_TIME_LIMIT=86400
   AI_DETECTION_PROVIDER=local
   ```

2. Set up a production WSGI server (Gunicorn example):
   ```bash
   pip install gunicorn
   gunicorn "app:create_app()"
   ```

3. Consider using a reverse proxy like Nginx for production deployments

### Database Backup

Regularly backup the SQLite database:

```bash
# Create a backup with timestamp
cp instance/users.db instance/users.db.backup_$(date +%Y%m%d_%H%M%S)
```

## Troubleshooting

### Common Issues

#### Database Errors

**Issue**: Database is locked or corrupted

**Solution**: Use the database repair scripts:
```bash
python repair_db.py
```

#### NLTK Data Missing

**Issue**: NLTK data not found for AI detection

**Solution**: Manually download required NLTK data:
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

#### Environment Variable Issues

**Issue**: Configuration not loading correctly

**Solution**: Verify the `.env` file exists and has the correct format. Ensure no spaces around the equals sign.

### Logging

Check the log files for detailed error information:

```
logs/app.log
```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the error logs for detailed information
2. Review the source code documentation
3. Consult the project maintainers

---

This technical implementation guide provides detailed instructions for setting up, configuring, and developing the Educational Assessment Platform. It complements the comprehensive documentation by focusing on the practical aspects of working with the codebase.