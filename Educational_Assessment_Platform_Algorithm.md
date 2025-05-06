# Educational Assessment Platform - Detailed Algorithm

## System Overview
This document provides a detailed algorithmic representation of the educational assessment platform, outlining the main workflows and processes. This can serve as a guide for creating a comprehensive flowchart of the system.

## 1. User Authentication and Management

### 1.1 User Registration Process
```
INPUT: username, email, password, role (teacher/student), subject_code (optional for teachers)
PROCESS:
    1. Validate input fields
    2. Check if username or email already exists in database
    3. If validation fails:
        a. Return error message
    4. If validation passes:
        a. Create new User object
        b. Hash password
        c. Save user to database
        d. If role is teacher AND subject_code provided:
            i. Create new Subject with teacher as owner
            ii. Save subject to database
    5. Redirect to login page
OUTPUT: Success/failure message, redirect to appropriate page
```

### 1.2 User Login Process
```
INPUT: username, password
PROCESS:
    1. Validate input fields
    2. Query database for user with matching username
    3. If user not found:
        a. Return error message
    4. If user found:
        a. Verify password hash
        b. If password incorrect:
            i. Return error message
        c. If password correct:
            i. Create user session
            ii. Redirect to appropriate dashboard based on role
OUTPUT: Success/failure message, redirect to dashboard or login page
```

## 2. Subject Management

### 2.1 Subject Creation (Teacher)
```
INPUT: subject_name, subject_code
PROCESS:
    1. Validate input fields
    2. Check if subject_code already exists
    3. If validation fails:
        a. Return error message
    4. If validation passes:
        a. Create new Subject object
        b. Set current teacher as owner
        c. Save subject to database
    5. Redirect to teacher dashboard
OUTPUT: Success/failure message, updated subject list on dashboard
```

### 2.2 Subject Enrollment (Student)
```
INPUT: subject_code
PROCESS:
    1. Validate subject_code exists
    2. Check if student is already enrolled in subject
    3. If already enrolled:
        a. Return error message
    4. If not enrolled:
        a. Create new StudentSubject record
        b. Set enrollment_status to 'pending'
        c. Save enrollment to database
    5. Redirect to student dashboard
OUTPUT: Success/failure message, updated enrollment list on dashboard
```

### 2.3 Enrollment Approval (Teacher)
```
INPUT: enrollment_id, action (approve/reject)
PROCESS:
    1. Retrieve StudentSubject record
    2. Verify teacher owns the subject
    3. Update enrollment_status based on action
    4. Save changes to database
    5. Refresh teacher dashboard
OUTPUT: Success/failure message, updated pending enrollment list
```

## 3. Quiz/Exam Creation

### 3.1 Quiz Setup
```
INPUT: title, description, quiz_type, subject_id, question_count, duration, start_time
PROCESS:
    1. Validate input fields
    2. Create new Quiz object
    3. Set current teacher as owner
    4. Save quiz to database
    5. Store quiz_id and question_count in session
    6. Redirect to question creation page
OUTPUT: Success/failure message, redirect to add question page
```

### 3.2 Question Creation
```
INPUT: question_text, question_type, options (for multiple choice), correct_answer, points, word_limit (for essay)
PROCESS:
    1. Validate input fields based on question_type
    2. Create new Question object
    3. Set appropriate attributes based on question_type:
        a. For multiple_choice: store options array and correct option index
        b. For identification: store correct answer string
        c. For true_false: store boolean value
        d. For essay: store word_limit
    4. Save question to database
    5. Increment questions_added counter in session
    6. If questions_added < total_questions:
        a. Redirect to add another question
    7. Else:
        a. Clear quiz setup from session
        b. Redirect to teacher dashboard
OUTPUT: Success/failure message, redirect to next question or dashboard
```

## 4. Quiz Taking

### 4.1 Starting a Quiz
```
INPUT: quiz_id
PROCESS:
    1. Verify student is enrolled in the subject
    2. Check if quiz is available (start_time has passed)
    3. Check if student has already taken the quiz
    4. If any checks fail:
        a. Return error message
    5. If all checks pass:
        a. Create new QuizSubmission record
        b. Set start_time to current time
        c. Save to database
        d. Load quiz questions
    6. Display quiz interface
OUTPUT: Quiz interface with questions and timer
```

### 4.2 Submitting Answers
```
INPUT: quiz_submission_id, answers (array of question_id and submitted_answer pairs)
PROCESS:
    1. Verify quiz submission belongs to current student
    2. For each answer in answers:
        a. Create new StudentSubmission record
        b. Set submitted_answer
        c. Validate answer against correct_answer:
            i. For multiple_choice, identification, true_false:
               - Set is_correct based on automatic validation
               - Set score based on points if correct
               - Set graded to true
            ii. For essay:
               - Set is_correct to false (requires manual grading)
               - Set score to 0 (temporary)
               - Set graded to false
        d. Save submission to database
    3. Update QuizSubmission record:
        a. Set submitted_at to current time
        b. Calculate duration_taken
        c. Calculate total_score for auto-graded questions
        d. Set graded to true if no essay questions, otherwise false
    4. Save changes to database
    5. Redirect to student dashboard
OUTPUT: Success message, redirect to dashboard
```

## 5. Grading

### 5.1 Manual Grading (Essay Questions)
```
INPUT: quiz_submission_id, grades (array of submission_id, score, and feedback)
PROCESS:
    1. Verify teacher owns the quiz
    2. For each grade in grades:
        a. Retrieve StudentSubmission record
        b. Update score and feedback
        c. Set graded to true
        d. Save changes to database
    3. Update QuizSubmission record:
        a. Recalculate total_score
        b. Set graded to true if all questions now graded
        c. Add overall feedback if provided
    4. Save changes to database
    5. Redirect to teacher dashboard
OUTPUT: Success message, updated submission status
```

### 5.2 Publishing Results
```
INPUT: quiz_submission_id, visible_to_students (boolean), show_answers (boolean)
PROCESS:
    1. Verify teacher owns the quiz
    2. Update QuizSubmission record:
        a. Set visible_to_students flag
        b. Set show_answers flag
    3. Save changes to database
    4. Redirect to teacher dashboard
OUTPUT: Success message, updated visibility settings
```

## 6. Result Viewing

### 6.1 Student Viewing Results
```
INPUT: quiz_submission_id
PROCESS:
    1. Verify submission belongs to current student
    2. Check if results are visible_to_students
    3. If not visible:
        a. Return message that results are not yet available
    4. If visible:
        a. Retrieve QuizSubmission with related StudentSubmissions
        b. Calculate statistics (score, percentage)
        c. Determine if correct answers should be shown
    5. Display results page
OUTPUT: Results page showing score, feedback, and possibly correct answers
```

### 6.2 Teacher Viewing Results
```
INPUT: quiz_submission_id
PROCESS:
    1. Verify teacher owns the quiz
    2. Retrieve QuizSubmission with related StudentSubmissions
    3. Calculate statistics (score, percentage)
    4. Display detailed results page
OUTPUT: Detailed results page with all student answers and grading options
```

## 7. System Data Flow

### 7.1 Main Data Entities and Relationships
```
User
  ↓
  ├── Teacher → creates → Subject
  │                ↓
  │                └── contains → Quiz
  │                                ↓
  │                                └── contains → Questions
  │
  └── Student → enrolls in → Subject
                   ↓
                   └── takes → Quiz
                              ↓
                              └── creates → QuizSubmission
                                             ↓
                                             └── contains → StudentSubmissions
```

### 7.2 Authentication Flow
```
Start
  ↓
User visits site
  ↓
Check if authenticated
  ↓
  ├── Yes → Redirect to appropriate dashboard
  │
  └── No → Show login/register options
      ↓
      ├── Login → Authenticate → Success → Create session → Dashboard
      │                        → Failure → Show error
      │
      └── Register → Validate → Success → Create user → Login page
                              → Failure → Show error
```

### 7.3 Quiz Creation Flow
```
Teacher dashboard
  ↓
Select create quiz
  ↓
Enter quiz details
  ↓
Create quiz record
  ↓
For each question (1 to n):
  ↓
  ├── Enter question details
  ↓
  ├── Select question type
  ↓
  ├── Enter type-specific details
  ↓
  └── Save question
  ↓
All questions added
  ↓
Quiz ready for students
```

### 7.4 Quiz Taking Flow
```
Student dashboard
  ↓
Select available quiz
  ↓
System checks eligibility
  ↓
Create quiz submission record
  ↓
Display questions with timer
  ↓
Student answers questions
  ↓
Submission occurs when:
  ├── Student clicks submit
  └── OR Timer expires
  ↓
Process answers:
  ├── Auto-grade objective questions
  └── Flag essay questions for manual grading
  ↓
Update submission record
  ↓
Redirect to dashboard
```

### 7.5 Grading Flow
```
Teacher dashboard
  ↓
Select quiz submission to grade
  ↓
System displays all answers:
  ├── Auto-graded questions (with option to override)
  └── Essay questions requiring manual grading
  ↓
Teacher enters scores and feedback
  ↓
System updates submission records
  ↓
Teacher sets visibility options:
  ├── Make results visible to student
  └── Show/hide correct answers
  ↓
System updates submission settings
  ↓
Redirect to dashboard
```

## 8. Security Considerations

### 8.1 Authentication Security
```
Password handling:
  1. Never store plaintext passwords
  2. Use generate_password_hash for secure storage
  3. Use check_password_hash for verification

Session management:
  1. Use Flask-Login for session handling
  2. Implement CSRF protection
  3. Set appropriate session timeouts

Access control:
  1. Use @login_required decorator for protected routes
  2. Check user role for role-specific actions
  3. Verify ownership of resources before allowing modifications
```

### 8.2 Data Validation
```
Input validation:
  1. Use WTForms validators for form inputs
  2. Validate data types and ranges
  3. Sanitize inputs to prevent injection attacks

Database integrity:
  1. Use SQLAlchemy relationships for referential integrity
  2. Implement transaction management with commit/rollback
  3. Handle exceptions to prevent data corruption
```

---

This algorithm document provides a comprehensive overview of the educational assessment platform's workflows and processes. It can be used as a guide to create a detailed flowchart representing the system's operation.