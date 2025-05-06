# Educational Assessment Platform

## Project Overview
This is an educational assessment platform designed to facilitate teacher-student interactions, subject management, quiz creation, and AI-based content detection for academic integrity.

## Architecture Improvements

The project has been restructured to follow modern software development practices:

### 1. Service Layer Architecture
Implemented a service layer to separate business logic from routes:
- **Auth Service**: Handles user authentication and registration
- **Subject Service**: Manages subject creation and enrollment
- **Dashboard Service**: Provides data for teacher and student dashboards
- **AI Detection Service**: Analyzes text for AI-generated content
- **Config Service**: Centralizes environment variable handling
- **Error Service**: Standardizes error handling across the application
- **Logging Service**: Provides consistent logging throughout the app

### 2. Improved Error Handling
- Standardized error responses
- Centralized error handling logic
- Better exception management with appropriate user feedback

### 3. Enhanced Security
- Environment variable management for sensitive configuration
- Improved password handling
- CSRF protection with extended timeout

### 4. Logging System
- Structured logging with request context
- Rotating file handlers to prevent log file bloat
- Separate error logs for easier debugging

## Project Structure

```
app/
├── __init__.py           # Application factory
├── auth/                 # Authentication module
│   ├── __init__.py
│   ├── forms.py          # Authentication forms
│   ├── routes.py         # Authentication routes
│   └── services.py       # Authentication business logic
├── dashboard/            # Dashboard module
│   ├── __init__.py
│   ├── routes.py         # Dashboard routes
│   └── services.py       # Dashboard business logic
├── main/                 # Main pages module
│   ├── __init__.py
│   └── routes.py         # Main routes
├── models.py             # Database models
├── services/             # Shared services
│   ├── ai_detection_service.py  # AI content detection
│   ├── config_service.py        # Configuration management
│   ├── error_service.py         # Error handling
│   └── logging_service.py       # Logging management
├── subject/              # Subject module
│   ├── __init__.py
│   ├── forms.py          # Subject forms
│   ├── routes.py         # Subject routes
│   └── services.py       # Subject business logic
└── quiz/                 # Quiz module
    ├── __init__.py
    └── routes.py         # Quiz routes
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=True  # Set to False in production
   DATABASE_URI=sqlite:///instance/users.db  # Or your preferred database URI
   ```
5. Run the application:
   ```
   python run.py
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|--------|
| SECRET_KEY | Flask secret key for session security | dev-default-secret-key-change-in-production |
| DATABASE_URI | Database connection string | sqlite:///instance/users.db |
| FLASK_DEBUG | Enable debug mode | False |
| FLASK_TESTING | Enable testing mode | False |
| WTF_CSRF_TIME_LIMIT | CSRF token expiry in seconds | 86400 (24 hours) |

## Code Quality Enhancements

1. **Type Annotations**: Added Python type hints for better code documentation and IDE support
2. **Docstrings**: Comprehensive docstrings for all functions and classes
3. **Consistent Error Handling**: Standardized approach to error handling and user feedback
4. **Separation of Concerns**: Clear separation between presentation, business logic, and data access
5. **Improved Logging**: Structured logging for better debugging and monitoring

## Testing

Run tests with pytest:
```
python -m pytest
```

## Future Improvements

1. Implement more comprehensive test coverage
2. Add API endpoints for mobile/frontend integration
3. Enhance AI detection capabilities
4. Implement caching for performance optimization
5. Add user profile management features