# Questionnaire Import Feature

## Overview
This feature allows teachers to import questions from document files (.docx and .pdf) into the Educational Assessment Platform. The system uses AI to analyze and extract questions from the documents, making it easier to create quizzes and exams without manual data entry.

## Features
- Import questions from .docx and .pdf files
- AI-powered question extraction and classification
- Review and edit extracted questions before saving
- Support for multiple question types (multiple choice, true/false, identification, essay)

## Setup

### Dependencies
The feature requires the following dependencies (already added to requirements.txt):
- python-docx==0.8.11
- PyPDF2==3.0.1
- openai==0.28.1

Install them using:
```
pip install -r requirements.txt
```

### OpenAI API Key
To use the AI-powered analysis, you need to set up an OpenAI API key:

1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key in your account dashboard
3. Set the API key as an environment variable:
   ```
   # On Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # On Linux/Mac
   export OPENAI_API_KEY=your_api_key_here
   ```

Alternatively, you can modify the `document_import.py` file to include your API key directly:

```python
class DocumentImporter:
    def __init__(self, api_key=None):
        self.api_key = api_key or "your_api_key_here"  # Replace with your actual API key
        if self.api_key:
            openai.api_key = self.api_key
```

## Usage

1. Log in as a teacher
2. From the dashboard, click on "Create Questionnaire" dropdown and select "Import Questionnaire"
3. Select the subject for the quiz
4. Upload a .docx or .pdf file containing questions
5. Choose whether to use AI for analysis (recommended)
6. Review the extracted questions
7. Edit any questions as needed
8. Enter a title for the quiz
9. Click "Save All Questions" to create the quiz

## Document Format Tips

For best results, format your document as follows:

### Multiple Choice Questions
```
1. What is the question text?
A. Option 1
B. Option 2
C. Option 3
D. Option 4
Correct Answer: B
```

### True/False Questions
```
2. Is this statement true?
True/False: True
```

### Identification Questions
```
3. What is the answer to this question?
Answer: The correct answer
```

### Essay Questions
```
4. Write an essay about this topic.
Word Limit: 500
```

## Troubleshooting

- If no questions are extracted, try improving the formatting of your document
- If AI analysis fails, you can disable it and the system will use pattern matching instead
- Make sure your OpenAI API key is valid and has sufficient credits
- Check the console for any error messages related to the document parsing

## Limitations

- The AI analysis works best with clearly formatted documents
- Very complex document layouts may not be parsed correctly
- The OpenAI API has rate limits and usage costs
- Large documents may take longer to process