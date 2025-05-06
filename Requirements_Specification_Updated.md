# Requirements Specification: Functional Requirements

## 1. User Authentication Module

### 1.1 User Registration
- Description: System allows new users to create accounts with role-based access
- Details:
  - Users can register with username, email, and password
  - Role selection between teacher and student
  - Email and username uniqueness validation
  - Password hashing for security
  - Teachers can specify a subject code during registration

### 1.2 User Login
- Description: Authenticated access to the system
- Details:
  - Username and password authentication
  - Role-based redirect to appropriate dashboard
  - Session management for logged-in users
  - CSRF protection with extended timeout

## 2. Subject Management Module

### 2.1 Subject Creation
- Description: Teachers can create and manage academic subjects
- Details:
  - Create subjects with name and unique subject code
  - View enrolled students for each subject
  - Drop subjects when no longer needed
  - Remove students from subjects

### 2.2 Subject Enrollment
- Description: Students can enroll in subjects using subject codes
- Details:
  - Request enrollment using subject code
  - Enrollment status tracking (pending, approved, rejected)
  - Timestamp tracking for enrollment requests
  - Teachers can approve or reject enrollment requests

## 3. Teacher Module

### 3.1 Question Management
- Description: Teachers can create and manage assessment questions
- Details:
  - Create multiple types of questions:
    - Multiple choice (with up to 5 options)
    - Identification
    - True/False
    - Essay (with word limit)
  - Set question properties:
    - Question text
    - Points allocation
    - Order index for question sequence
    - Answer options (for multiple choice)
    - Correct answers
    - Word limits (for essay questions)
  - Edit existing questions
  - Delete questions
  - Organize questions in a question bank

### 3.2 Quiz/Exam Creation
- Description: Teachers can create and schedule assessments
- Details:
  - Create quizzes or exams with title and description
  - Set assessment properties:
    - Duration (time limit)
    - Start time (scheduled availability)
    - Question count
    - Assessment type (quiz or exam)
  - Add questions to assessments
  - Associate assessments with specific subjects

### 3.3 Assessment Grading
- Description: Teachers can grade and provide feedback on student submissions
- Details:
  - View student submissions
  - Assign scores
  - Provide written feedback
  - Track grading status
  - Automatic grading for objective questions
  - Manual grading for Essay and Identification
  - Control visibility of grades to students
  - Option to show correct answers to students
  - Delete submissions if needed

## 4. Student Module

### 4.1 Subject Enrollment
- Description: Students can enroll in and access subjects
- Details:
  - Request enrollment using subject codes
  - View enrollment status (pending, approved, rejected)
  - Access approved subjects and their content

### 4.2 Assessment Taking
- Description: Students can take assessments and submit answers
- Details:
  - View assigned questions
  - Submit answers for different question types
  - Real-time answer submission
  - View submission status
  - Time tracking for quiz duration

### 4.3 Performance Tracking
- Description: Students can view their assessment results
- Details:
  - View scores for submitted assessments
  - Access teacher feedback
  - Track submission history
  - Monitor grading status
  - View correct answers (if enabled by teacher)

## 5. Database Management

### 5.1 Data Storage
- Description: Secure storage and management of system data
- Details:
  - User information storage
  - Subject and enrollment data
  - Question bank management
  - Quiz and exam configuration
  - Student submission records
  - Grading and feedback data
  - Timestamps for all records

### 5.2 Data Relationships
- Description: Maintain relationships between different data entities
- Details:
  - User-Subject relationships
  - Teacher-Student associations
  - Subject-Quiz correlations
  - Quiz-Question linkages
  - Student-Submission associations
  - Grade-Feedback connections

### 5.3 Database Maintenance
- Description: Tools for database management and repair
- Details:
  - Database backup functionality
  - Database repair utilities
  - Schema migration tools
  - Data integrity verification

## 6. System Interface

### 6.1 User Interface
- Description: Responsive and user-friendly web interface
- Details:
  - Clean and intuitive navigation
  - Role-specific dashboards
  - Form-based interactions
  - Bootstrap-based responsive design
  - Consistent layout and styling
  - Modal dialogs for quick actions

### 6.2 Notification System
- Description: User feedback and notification mechanisms
- Details:
  - Flash messages for user actions
  - Error notifications
  - Status updates for enrollments and submissions
  - Confirmation dialogs for critical actions