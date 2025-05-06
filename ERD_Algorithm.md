# Entity-Relationship Diagram (ERD) Algorithm for Educational Assessment Platform

## 1. Entity Identification

Based on the database models in the application, the following entities have been identified:

### 1.1 Primary Entities

1. **User**
   - Primary entity representing system users (teachers and students)
   - Contains authentication and role information

2. **Subject**
   - Primary entity representing academic subjects/courses
   - Contains subject information and ownership details

3. **Quiz**
   - Primary entity representing assessments (quizzes or exams)
   - Contains assessment configuration and metadata

4. **Question**
   - Primary entity representing individual questions within assessments
   - Contains question content, type, and grading information

5. **QuizSubmission**
   - Primary entity representing a student's submission of an entire quiz
   - Contains submission metadata and overall grading information

6. **StudentSubmission**
   - Primary entity representing a student's answer to an individual question
   - Contains the submitted answer and grading information

7. **Announcement**
   - Primary entity representing system notifications
   - Contains notification content and metadata

### 1.2 Junction Entities

1. **StudentSubject**
   - Junction entity connecting students to subjects (enrollment)
   - Implements many-to-many relationship between User and Subject

## 2. Attribute Identification

### 2.1 User Entity Attributes

- **id** (Primary Key, Integer)
- **username** (String, Unique, Not Null)
- **email** (String, Unique, Not Null)
- **password_hash** (String)
- **role** (String, Not Null, Default: 'student')

### 2.2 Subject Entity Attributes

- **id** (Primary Key, Integer)
- **name** (String, Not Null)
- **subject_code** (String, Unique, Not Null)
- **teacher_id** (Foreign Key to User.id, Not Null)
- **created_at** (DateTime, Not Null, Default: current timestamp)

### 2.3 Quiz Entity Attributes

- **id** (Primary Key, Integer)
- **title** (String, Not Null)
- **description** (Text, Nullable)
- **quiz_type** (String, Not Null, Default: 'quiz')
- **created_at** (DateTime, Not Null, Default: current timestamp)
- **user_id** (Foreign Key to User.id, Not Null)
- **subject_id** (Foreign Key to Subject.id, Not Null)
- **duration** (Integer, Nullable)
- **start_time** (DateTime, Nullable)

### 2.4 Question Entity Attributes

- **id** (Primary Key, Integer)
- **question_text** (String, Not Null)
- **question_type** (String, Not Null)
- **word_limit** (Integer, Nullable)
- **options** (JSON, Nullable)
- **correct_answer** (String, Not Null)
- **points** (Float, Not Null, Default: 1.0)
- **order_index** (Integer, Not Null, Default: 0)
- **created_at** (DateTime, Not Null, Default: current timestamp)
- **user_id** (Foreign Key to User.id, Not Null)
- **quiz_id** (Foreign Key to Quiz.id, Nullable)

### 2.5 QuizSubmission Entity Attributes

- **id** (Primary Key, Integer)
- **student_id** (Foreign Key to User.id, Not Null)
- **quiz_id** (Foreign Key to Quiz.id, Not Null)
- **submitted_at** (DateTime, Nullable)
- **start_time** (DateTime, Nullable)
- **duration_taken** (Integer, Nullable)
- **total_score** (Float, Not Null, Default: 0.0)
- **graded** (Boolean, Not Null, Default: False)
- **visible_to_students** (Boolean, Not Null, Default: False)
- **show_answers** (Boolean, Not Null, Default: False)
- **feedback** (Text, Nullable)

### 2.6 StudentSubmission Entity Attributes

- **id** (Primary Key, Integer)
- **student_id** (Foreign Key to User.id, Not Null)
- **question_id** (Foreign Key to Question.id, Not Null)
- **quiz_submission_id** (Foreign Key to QuizSubmission.id, Not Null)
- **submitted_answer** (String, Not Null)
- **is_correct** (Boolean, Not Null)
- **submitted_at** (DateTime, Not Null, Default: current timestamp)
- **score** (Float, Not Null, Default: 0.0)
- **graded** (Boolean, Not Null, Default: False)
- **feedback** (Text, Nullable)

### 2.7 Announcement Entity Attributes

- **id** (Primary Key, Integer)
- **title** (String, Not Null)
- **content** (Text, Not Null)
- **created_at** (DateTime, Not Null, Default: current timestamp)
- **user_id** (Foreign Key to User.id, Not Null)
- **subject_id** (Foreign Key to Subject.id, Nullable)
- **quiz_id** (Foreign Key to Quiz.id, Nullable)
- **submission_id** (Foreign Key to QuizSubmission.id, Nullable)
- **announcement_type** (String, Not Null)
- **is_read** (Boolean, Default: False)

### 2.8 StudentSubject Entity Attributes

- **student_id** (Primary Key, Foreign Key to User.id)
- **subject_id** (Primary Key, Foreign Key to Subject.id)
- **enrollment_status** (String, Not Null, Default: 'pending')
- **enrolled_at** (DateTime, Not Null, Default: current timestamp)

## 3. Relationship Identification

### 3.1 User-Subject Relationships

1. **Teacher-Subject Relationship**
   - Type: One-to-Many
   - A teacher (User) can create and teach multiple subjects
   - A subject is taught by exactly one teacher
   - Implementation: Foreign key `teacher_id` in Subject table references User.id

2. **Student-Subject Enrollment**
   - Type: Many-to-Many
   - A student (User) can enroll in multiple subjects
   - A subject can have multiple enrolled students
   - Implementation: Junction table `student_subjects` with composite primary key (student_id, subject_id)

### 3.2 User-Quiz Relationships

1. **Teacher-Quiz Creation**
   - Type: One-to-Many
   - A teacher (User) can create multiple quizzes
   - A quiz is created by exactly one teacher
   - Implementation: Foreign key `user_id` in Quiz table references User.id

2. **Student-Quiz Submission**
   - Type: One-to-Many
   - A student (User) can submit multiple quizzes
   - A quiz submission belongs to exactly one student
   - Implementation: Foreign key `student_id` in QuizSubmission table references User.id

### 3.3 Subject-Quiz Relationship

1. **Subject-Quiz Association**
   - Type: One-to-Many
   - A subject can have multiple quizzes
   - A quiz belongs to exactly one subject
   - Implementation: Foreign key `subject_id` in Quiz table references Subject.id

### 3.4 Quiz-Question Relationship

1. **Quiz-Question Composition**
   - Type: One-to-Many
   - A quiz contains multiple questions
   - A question belongs to exactly one quiz
   - Implementation: Foreign key `quiz_id` in Question table references Quiz.id

### 3.5 User-Question Relationship

1. **Teacher-Question Creation**
   - Type: One-to-Many
   - A teacher (User) can create multiple questions
   - A question is created by exactly one teacher
   - Implementation: Foreign key `user_id` in Question table references User.id

### 3.6 Quiz-QuizSubmission Relationship

1. **Quiz-Submission Association**
   - Type: One-to-Many
   - A quiz can have multiple submissions from different students
   - A quiz submission is for exactly one quiz
   - Implementation: Foreign key `quiz_id` in QuizSubmission table references Quiz.id

### 3.7 QuizSubmission-StudentSubmission Relationship

1. **QuizSubmission-StudentSubmission Composition**
   - Type: One-to-Many
   - A quiz submission contains multiple question submissions
   - A question submission belongs to exactly one quiz submission
   - Implementation: Foreign key `quiz_submission_id` in StudentSubmission table references QuizSubmission.id

### 3.8 Question-StudentSubmission Relationship

1. **Question-Answer Association**
   - Type: One-to-Many
   - A question can have multiple answers from different students
   - A student submission answers exactly one question
   - Implementation: Foreign key `question_id` in StudentSubmission table references Question.id

### 3.9 User-Announcement Relationship

1. **User-Announcement Creation**
   - Type: One-to-Many
   - A user can create multiple announcements
   - An announcement is created by exactly one user
   - Implementation: Foreign key `user_id` in Announcement table references User.id

### 3.10 Subject-Announcement Relationship

1. **Subject-Announcement Association**
   - Type: One-to-Many
   - A subject can have multiple announcements
   - An announcement can be associated with at most one subject
   - Implementation: Foreign key `subject_id` in Announcement table references Subject.id

### 3.11 Quiz-Announcement Relationship

1. **Quiz-Announcement Association**
   - Type: One-to-Many
   - A quiz can have multiple announcements
   - An announcement can be associated with at most one quiz
   - Implementation: Foreign key `quiz_id` in Announcement table references Quiz.id

### 3.12 QuizSubmission-Announcement Relationship

1. **QuizSubmission-Announcement Association**
   - Type: One-to-Many
   - A quiz submission can have multiple announcements
   - An announcement can be associated with at most one quiz submission
   - Implementation: Foreign key `submission_id` in Announcement table references QuizSubmission.id

## 4. Cardinality and Participation Constraints

### 4.1 Mandatory Participation

- A Subject must have a Teacher (mandatory participation of Subject in Teacher-Subject relationship)
- A Quiz must have a Subject and a Teacher (mandatory participation of Quiz in Subject-Quiz and Teacher-Quiz relationships)
- A Question must have an Author (mandatory participation of Question in User-Question relationship)
- A StudentSubmission must have a Student, Question, and QuizSubmission (mandatory participation in all related relationships)

### 4.2 Optional Participation

- A User is not required to teach any Subjects (optional participation of User in Teacher-Subject relationship)
- A User is not required to enroll in any Subjects (optional participation of User in Student-Subject relationship)
- A User is not required to create any Questions (optional participation of User in User-Question relationship)
- A Subject is not required to have any enrolled Students (optional participation of Subject in Student-Subject relationship)
- A Quiz is not required to have any Submissions (optional participation of Quiz in Quiz-QuizSubmission relationship)

## 5. ERD Implementation Algorithm

### 5.1 Entity Creation

1. Create the User entity with all attributes
2. Create the Subject entity with all attributes including the foreign key to User
3. Create the Quiz entity with all attributes including foreign keys to User and Subject
4. Create the Question entity with all attributes including foreign keys to User and Quiz
5. Create the QuizSubmission entity with all attributes including foreign keys to User and Quiz
6. Create the StudentSubmission entity with all attributes including foreign keys to User, Question, and QuizSubmission
7. Create the Announcement entity with all attributes including foreign keys to User, Subject, Quiz, and QuizSubmission
8. Create the StudentSubject junction entity with composite primary key and additional attributes

### 5.2 Relationship Implementation

1. Implement one-to-many relationships using foreign keys in the "many" side entity
2. Implement many-to-many relationships using junction tables with composite primary keys
3. Define referential integrity constraints (CASCADE, SET NULL, RESTRICT) for all foreign keys

### 5.3 Indexing Strategy

1. Create indexes on all foreign key columns to improve join performance
2. Create unique indexes on columns with uniqueness constraints (username, email, subject_code)
3. Create composite indexes on frequently queried combinations (e.g., student_id + quiz_id)

## 6. Database Schema Optimization

### 6.1 Normalization

The current schema is already in Third Normal Form (3NF) with the following characteristics:

1. All attributes are atomic (1NF)
2. All non-key attributes are fully functionally dependent on the primary key (2NF)
3. No transitive dependencies exist (3NF)

### 6.2 Denormalization Considerations

Potential denormalization strategies for performance optimization:

1. Store calculated total scores in QuizSubmission for faster retrieval
2. Store count of enrolled students in Subject for faster display
3. Store question count in Quiz for faster UI rendering

## 7. Physical Implementation Considerations

### 7.1 Data Types

- Use appropriate data types for each attribute (INTEGER for IDs, VARCHAR for text, DATETIME for timestamps)
- Consider storage requirements and query performance when selecting data types

### 7.2 Constraints

- Implement PRIMARY KEY constraints on all entity identifiers
- Implement FOREIGN KEY constraints with appropriate referential actions
- Implement UNIQUE constraints on attributes requiring uniqueness
- Implement NOT NULL constraints on required attributes
- Implement CHECK constraints for data validation (e.g., enrollment_status values)

### 7.3 Indexes

- Create indexes on frequently queried columns
- Create composite indexes for common query patterns
- Balance index creation with write performance considerations

---

This algorithm provides a comprehensive blueprint for implementing an Entity-Relationship Diagram for the educational assessment platform. The ERD can be visualized using any standard ERD notation (Chen, Crow's Foot, UML) based on the entities, attributes, and relationships defined in this document.