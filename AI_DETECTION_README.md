# AI Content Detection Feature

This document provides information about the enhanced AI content detection feature implemented in the Educational Assessment Platform.

## Overview

The AI content detection feature helps teachers identify potentially AI-generated content in student essay submissions. The system uses a combination of natural language processing techniques and can optionally integrate with specialized AI detection APIs for more accurate results.

## Features

- Advanced local detection using NLP techniques
- Integration with external AI detection APIs (GPTZero and Originality.ai)
- Detailed analysis with multiple detection metrics
- Fallback to local detection if API calls fail

## How to Use

1. When grading essay submissions, click the "Check for AI Content" button next to the essay.
2. The system will analyze the text and display a detection score along with detailed metrics.
3. Use this information to help evaluate the authenticity of student submissions.

## Configuration

By default, the system uses local detection methods that don't require external API keys. For more accurate results, you can configure the system to use specialized AI detection APIs.

### Setting Up External API Integration

1. Create a `.env` file in the root directory of the project
2. Add your API keys and provider choice:

```
# Choose one: 'local', 'gptzero', or 'originality'
AI_DETECTION_PROVIDER=local

# If using GPTZero
GPTZERO_API_KEY=your_api_key_here

# If using Originality.ai
ORIGINALITY_API_KEY=your_api_key_here
```

3. Restart the application for changes to take effect

### Obtaining API Keys

- **GPTZero**: Sign up at [gptzero.me](https://gptzero.me) and obtain an API key from their developer dashboard.
- **Originality.ai**: Create an account at [originality.ai](https://originality.ai) and generate an API key in your account settings.

## Technical Details

The AI detection system uses the following techniques:

- Sentence length analysis
- Formal language pattern detection
- Repetition analysis
- Sentence variance measurement

When using external APIs, the system will fall back to local detection if the API call fails for any reason.

## Dependencies

The AI detection feature requires the following Python packages:

- nltk
- requests
- statistics

These dependencies are automatically included in the `requirements.txt` file.