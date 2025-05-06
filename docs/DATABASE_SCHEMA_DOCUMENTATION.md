# Educational Assessment Platform - Database Schema Documentation

## Overview

This document provides a detailed description of the database schema for the Educational Assessment Platform. It includes entity relationships, table structures, and field descriptions to help developers understand the data model.

## Entity-Relationship Diagram

The database consists of the following main entities and their relationships:

```
+-------------+       +----------------+       +-------------+
|    User     |<----->| StudentSubject |<----->|   Subject   |
+-------------+       +----------------+       +-------------+
      ^                                              ^
      |                                              |
      v                                              v
+-------------+       +----------------+       +-------------+
|   Question  |<----->| StudentSubmission |<-->| Quiz       |
+-------------+       +----------------+       +-------------+
                              ^
                              |
                              v
                      +----------------+
                      | QuizSubmission |
                      +----------------+
                              ^
                              |
                              v
                      +----------------+
                      |  Announcement  |
                      +----------------+
```

## Table Definitions

### User

Stores user information with role distinction (teacher/student).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the user |
| username | String(80) | Unique, Not Null | User's login name |
| email | String(120) | Unique, Not Null | User's email address |
| password_hash | String(128) | | Hashed password for security |
| role | String(20) | Not Null, Default: 'student' | User role ('teacher' or 'student') |

**Relationships:**
- One-to-Many with Question (as author)
- One-to-Many with StudentSubmission (as student)
- One-to-Many with Announcement (as creator)
- One-to-Many with QuizSubmission (as student)
- One-to-Many with Subject (as teacher)
- Many-to-Many with Subject (as enrolled_students through StudentSubject)

### Subject

Represents academic subjects created by teachers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the subject |
| name | String(100) | Not Null | Name of the subject |
| subject_code | String(20) | Unique, Not Null | Unique code for subject enrollment |
| teacher_id | Integer | Foreign Key (User.id), Not Null | ID of the teacher who created the subject |
| created_at | DateTime | Not Null, Default: current time | When the subject was created |

**Relationships:**
- Many-to-One with User (as teacher)
- One-to-Many with Quiz
- One-to-Many with Announcement
- Many-to-Many with User (as enrolled_students through StudentSubject)

### StudentSubject

Association table for student enrollments in subjects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| student_id | Integer | Primary Key, Foreign Key (User.id) | ID of the enrolled student |
| subject_id | Integer | Primary Key, Foreign Key (Subject.id) | ID of the subject |
| enrollment_status | String(20) | Not Null, Default: 'pending' | Status of enrollment ('pending', 'approved', 'rejected') |
| enrolled_at | DateTime | Not Null, Default: current time | When the enrollment request was made |

**Relationships:**
- Many-to-One with User (as student)
- Many-to-One with Subject

### Quiz

Represents assessments created by teachers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the quiz |
| title | String(100) | Not Null | Title of the quiz |
| description | Text | Nullable | Description of the quiz |
| quiz_type | String(20) | Not Null, Default: 'quiz' | Type of assessment ('quiz' or 'exam') |
| created_at | DateTime | Not Null, Default: current time | When the quiz was created |
| user_id | Integer | Foreign Key (User.id), Not Null | ID of the teacher who created the quiz |
| subject_id | Integer | Foreign Key (Subject.id), Not Null | ID of the subject the quiz belongs to |
| duration | Integer | Nullable | Duration of the quiz in minutes |
| start_time | DateTime | Nullable | When the quiz becomes available |

**Relationships:**
- Many-to-One with User (as teacher)
- Many-to-One with Subject
- One-to-Many with Question
- One-to-Many with QuizSubmission
- One-to-Many with Announcement

### Question

Stores assessment questions with various types.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the question |
| question_text | String(500) | Not Null | Text of the question |
| question_type | String(20) | Not Null | Type of question ('multiple_choice', 'identification', 'true_false', 'essay') |
| word_limit | Integer | Nullable | Word limit for essay questions |
| options | JSON | Nullable | Options for multiple choice questions |
| correct_answer | String(500) | Not Null | Correct answer for the question |
| points | Float | Not Null, Default: 1.0 | Points awarded for correct answer |
| order_index | Integer | Not Null, Default: 0 | Order of the question in the quiz |
| created_at | DateTime | Not Null, Default: current time | When the question was created |
| user_id | Integer | Foreign Key (User.id), Not Null | ID of the teacher who created the question |
| quiz_id | Integer | Foreign Key (Quiz.id), Nullable | ID of the quiz the question belongs to |

**Relationships:**
- Many-to-One with User (as author)
- Many-to-One with Quiz
- One-to-Many with StudentSubmission

### QuizSubmission

Tracks student attempts at quizzes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the submission |
| student_id | Integer | Foreign Key (User.id), Not Null | ID of the student |
| quiz_id | Integer | Foreign Key (Quiz.id), Not Null | ID of the quiz |
| submitted_at | DateTime | Nullable | When the quiz was submitted (null for in-progress) |
| start_time | DateTime | Nullable | When the student started the quiz |
| duration_taken | Integer | Nullable | Time spent in minutes |
| total_score | Float | Not Null, Default: 0.0 | Total score for the quiz |
| graded | Boolean | Not Null, Default: False | Whether all questions have been graded |
| visible_to_students | Boolean | Not Null, Default: False | Whether grades are visible to students |
| show_answers | Boolean | Not Null, Default: False | Whether correct answers are visible to students |
| feedback | Text | Nullable | Overall feedback for the submission |

**Relationships:**
- Many-to-One with User (as student)
- Many-to-One with Quiz
- One-to-Many with StudentSubmission
- One-to-Many with Announcement

### StudentSubmission

Stores individual question responses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the submission |
| student_id | Integer | Foreign Key (User.id), Not Null | ID of the student |
| question_id | Integer | Foreign Key (Question.id), Not Null | ID of the question |
| quiz_submission_id | Integer | Foreign Key (QuizSubmission.id), Not Null | ID of the quiz submission |
| submitted_answer | String(500) | Not Null | Student's answer to the question |
| is_correct | Boolean | Not Null | Whether the answer is correct |
| submitted_at | DateTime | Not Null, Default: current time | When the answer was submitted |
| score | Float | Not Null, Default: 0.0 | Score for this question |
| graded | Boolean | Not Null, Default: False | Whether this question has been graded |
| feedback | Text | Nullable | Feedback for this specific answer |

**Relationships:**
- Many-to-One with User (as student)
- Many-to-One with Question
- Many-to-One with QuizSubmission

### Announcement

System notifications and messages.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary Key | Unique identifier for the announcement |
| title | String(100) | Not Null | Title of the announcement |
| content | Text | Not Null | Content of the announcement |
| created_at | DateTime | Not Null, Default: current time | When the announcement was created |
| user_id | Integer | Foreign Key (User.id), Not Null | ID of the user who created the announcement |
| subject_id | Integer | Foreign Key (Subject.id), Nullable | ID of the related subject (if any) |
| quiz_id | Integer | Foreign Key (Quiz.id), Nullable | ID of the related quiz (if any) |
| submission_id | Integer | Foreign Key (QuizSubmission.id), Nullable | ID of the related submission (if any) |

**Relationships:**
- Many-to-One with User (as creator)
- Many-to-One with Subject (optional)
- Many-to-One with Quiz (optional)
- Many-to-One with QuizSubmission (optional)

## Database Constraints

### Primary Keys
- Each table has a unique primary key (usually `id`)
- The `StudentSubject` table has a composite primary key (`student_id`, `subject_id`)

### Foreign Keys
- `User.id` is referenced by:
  - `Subject.teacher_id`
  - `StudentSubject.student_id`
  - `Quiz.user_id`
  - `Question.user_id`
  - `QuizSubmission.student_id`
  - `StudentSubmission.student_id`
  - `Announcement.user_id`
- `Subject.id` is referenced by:
  - `StudentSubject.subject_id`
  - `Quiz.subject_id`
  - `Announcement.subject_id`
- `Quiz.id` is referenced by:
  - `Question.quiz_id`
  - `QuizSubmission.quiz_id`
  - `Announcement.quiz_id`
- `Question.id` is referenced by:
  - `StudentSubmission.question_id`
- `QuizSubmission.id` is referenced by:
  - `StudentSubmission.quiz_submission_id`
  - `Announcement.submission_id`

### Cascading Behavior

The database implements cascading deletes for certain relationships to maintain data integrity:

- When a `User` is deleted, all related records are deleted
- When a `Subject` is deleted, all related `Quiz` records are deleted
- When a `Quiz` is deleted, all related `Question` and `QuizSubmission` records are deleted
- When a `QuizSubmission` is deleted, all related `StudentSubmission` records are deleted

## Indexing Strategy

The following indexes are recommended for optimal performance:

- `User.username` and `User.email` (already indexed as unique)
- `Subject.subject_code` (already indexed as unique)
- `StudentSubject.student_id` and `StudentSubject.subject_id`
- `Quiz.subject_id`
- `Question.quiz_id`
- `QuizSubmission.quiz_id` and `QuizSubmission.student_id`
- `StudentSubmission.quiz_submission_id`

## Data Validation

The database models implement validation logic to ensure data integrity:

- Password hashing for security
- Answer validation based on question type
- Enrollment status validation

## Example Queries

### Get all subjects taught by a teacher
```sql
SELECT * FROM subject WHERE teacher_id = :teacher_id;
```

### Get all students enrolled in a subject
```sql
SELECT u.* FROM user u
JOIN student_subjects ss ON u.id = ss.student_id
WHERE ss.subject_id = :subject_id AND ss.enrollment_status = 'approved';
```

### Get all quizzes for a subject
```sql
SELECT * FROM quiz WHERE subject_id = :subject_id ORDER BY created_at DESC;
```

### Get all submissions for a quiz
```sql
SELECT qs.*, u.username FROM quiz_submission qs
JOIN user u ON qs.student_id = u.id
WHERE qs.quiz_id = :quiz_id;
```

### Get all questions for a quiz
```sql
SELECT * FROM question WHERE quiz_id = :quiz_id ORDER BY order_index;
```

### Get all answers for a quiz submission
```sql
SELECT ss.*, q.question_text, q.question_type FROM student_submission ss
JOIN question q ON ss.question_id = q.id
WHERE ss.quiz_submission_id = :quiz_submission_id;
```

---

This database schema documentation provides a comprehensive reference for the data model of the Educational Assessment Platform. It includes detailed information about table structures, relationships, constraints, and example queries to help developers understand and work with the database effectively.