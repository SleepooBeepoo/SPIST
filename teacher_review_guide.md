# Teacher Review Interface for Manual Grading

## Overview

This document provides guidance on how to use the teacher review interface for manually grading identification and essay questions. While multiple choice and true/false questions are automatically graded by the system, identification and essay questions require teacher evaluation.

## Question Types and Grading Methods

### Automatically Graded Questions
- **Multiple Choice**: System compares the selected option index with the correct answer and assigns points automatically.
- **True/False**: System evaluates the submitted boolean value against the correct answer and assigns points automatically.

### Manually Graded Questions
- **Identification**: Requires teacher review to account for variations in spelling, capitalization, and acceptable alternative answers.
- **Essay**: Requires teacher evaluation of content, reasoning, and writing quality.

## Using the Review Interface

### Accessing Submissions Requiring Review

1. Navigate to the Quiz Management section
2. Select the quiz containing submissions
3. Click on "Review Submissions"
4. The system will highlight questions requiring manual grading

### Grading Identification Questions

When reviewing identification questions:

1. Compare the student's answer with the correct answer
2. Consider acceptable variations (spelling, capitalization, synonyms)
3. Assign full or partial credit as appropriate
4. Add feedback explaining the grading decision

### Grading Essay Questions

When reviewing essay questions:

1. Read the complete response
2. Evaluate based on:
   - Content accuracy
   - Reasoning and analysis
   - Organization and clarity
   - Writing mechanics (if relevant)
3. Assign points based on the rubric
4. Provide constructive feedback

### Submission Status

The system tracks the grading status of all submissions:

- **Automatically Graded**: Multiple choice and true/false questions
- **Pending Review**: Identification and essay questions awaiting teacher evaluation
- **Manually Graded**: Identification and essay questions that have been reviewed

## Best Practices

1. **Consistency**: Use the same criteria for all students
2. **Detailed Feedback**: Provide specific comments to help students understand their performance
3. **Partial Credit**: Consider awarding partial points for partially correct identification answers
4. **Rubrics**: Develop clear rubrics for essay questions to ensure fair evaluation

## Technical Implementation

The system has been enhanced to support this workflow through:

- Automatic detection of question types during document import
- Flagging of questions requiring manual grading
- Interface for teachers to efficiently review and grade submissions
- Support for providing feedback on each submission

This implementation ensures that all question types are properly supported while maintaining the efficiency benefits of automatic grading where appropriate.