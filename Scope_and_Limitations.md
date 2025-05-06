# Scope and Limitations

## 1. System Scope

### 1.1 User Management
- **User Roles**: The system supports two distinct user roles: teachers and students, each with specific permissions and capabilities.
- **Authentication**: Secure login and registration functionality with password hashing for user protection.
- **Profile Management**: Basic user profile information including username and email.

### 1.2 Course Management
- **Subject Creation**: Teachers can create subjects with unique subject codes.
- **Enrollment System**: Students can request enrollment in subjects, with teachers having approval authority.
- **Enrollment Tracking**: The system records enrollment dates and status (pending, approved, rejected).

### 1.3 Assessment Creation
- **Quiz Types**: Support for both quizzes and exams as assessment types.
- **Question Types**: Four question formats supported:
  - Multiple choice (with up to 5 options)
  - Identification/Short answer
  - True/False
  - Essay/Long answer
- **Assessment Settings**: Configurable duration, start time, and point values for questions.

### 1.4 Assessment Taking
- **Timed Assessments**: Support for time-limited quizzes with automatic submission.
- **Progress Tracking**: System tracks when students start and submit assessments.
- **Answer Submission**: Students can submit answers for all supported question types.

### 1.5 Grading and Feedback
- **Automatic Grading**: Automatic evaluation for multiple choice, identification, and true/false questions.
- **Manual Grading**: Interface for teachers to manually grade essay questions and provide feedback.
- **Score Calculation**: Automatic calculation of total scores based on individual question points.
- **Result Visibility Control**: Teachers can control when grades and correct answers are visible to students.

## 2. Technical Limitations

### 2.1 Database Constraints
- **SQLite Database**: The system uses SQLite, which has limitations for concurrent access and may not be suitable for very large deployments.
- **Data Migration**: Schema changes require complex migration scripts due to SQLite's limited ALTER TABLE capabilities.

### 2.2 Performance Limitations
- **Scalability**: The current architecture may face performance issues with a large number of concurrent users.
- **File Storage**: No dedicated system for handling large file uploads or media attachments.

### 2.3 Security Considerations
- **Session Management**: Basic session management with CSRF protection but limited session expiry controls.
- **Access Control**: Role-based access control implemented at the route level, but lacks fine-grained permission system.

## 3. Functional Limitations

### 3.1 Assessment Limitations
- **Question Formats**: Limited to four question types without support for more advanced formats (e.g., matching, ordering, coding questions).
- **Media Support**: No native support for embedding images, audio, or video in questions.
- **Question Bank**: No comprehensive question bank functionality for reusing questions across multiple assessments.

### 3.2 Grading Limitations
- **Partial Credit**: No support for awarding partial credit on questions.
- **Grading Rubrics**: No structured rubric system for consistent essay grading.
- **Plagiarism Detection**: No built-in plagiarism checking capabilities.

### 3.3 Reporting Limitations
- **Analytics**: Limited analytics on student performance and assessment statistics.
- **Data Export**: No functionality to export grades or assessment data to external formats.
- **Reporting Tools**: Absence of comprehensive reporting tools for tracking student progress over time.

### 3.4 Communication Limitations
- **Notifications**: No automated notification system for assessment availability or grading completion.
- **Messaging**: No built-in messaging system between teachers and students.
- **Discussion Forums**: No discussion capabilities for collaborative learning.

## 4. User Interface Limitations

### 4.1 Accessibility
- **Accessibility Standards**: Limited implementation of accessibility standards for users with disabilities.
- **Responsive Design**: Basic responsive design that may not be optimized for all device types and screen sizes.

### 4.2 Customization
- **Theming**: No support for custom themes or branding.
- **Layout Customization**: Fixed layout with limited customization options for teachers or institutions.

## 5. Integration Limitations

### 5.1 External Systems
- **LMS Integration**: No built-in integration with popular Learning Management Systems.
- **Authentication Services**: No support for single sign-on or integration with external authentication providers.
- **API Availability**: No public API for third-party integrations.

## 6. Deployment Limitations

### 6.1 Environment Requirements
- **Local Deployment**: Designed primarily for local deployment rather than cloud hosting.
- **Backup System**: Basic database backup functionality without automated scheduling.
- **Multi-tenancy**: No support for multi-tenant deployment for different institutions.

---

This document outlines the current scope and limitations of the educational assessment platform. It serves as a reference for understanding the system's capabilities and constraints, helping to set appropriate expectations for users and guide future development efforts.