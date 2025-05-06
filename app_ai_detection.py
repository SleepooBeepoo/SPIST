# AI Detection endpoint for integration into app.py

# This file contains the updated AI detection endpoint that should be integrated
# into the main app.py file to replace the existing implementation.

@app.route('/check_ai_content/<int:submission_id>', methods=['POST'])
@login_required
def check_ai_content(submission_id):
    """Check if an essay submission contains AI-generated content"""
    from flask import jsonify
    from ai_detection_service_new import AIContentDetector
    
    try:
        if current_user.role != 'teacher':
            return jsonify({'error': 'Unauthorized', 'level': 'danger'}), 403
        
        # Validate submission exists
        submission = StudentSubmission.query.get(submission_id)
        if not submission:
            return jsonify({
                'error': 'Submission not found',
                'level': 'danger',
                'score': 0,
                'confidence': 'Error: Submission not found',
                'features': []
            }), 404
            
        # Validate quiz_submission exists
        if not submission.quiz_submission:
            return jsonify({
                'error': 'Quiz submission not found',
                'level': 'danger',
                'score': 0,
                'confidence': 'Error: Quiz submission not found',
                'features': []
            }), 404
            
        quiz = submission.quiz_submission.quiz
        
        # Verify teacher owns the quiz
        if quiz.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'level': 'danger'}), 403
        
        # Get the essay text
        essay_text = submission.submitted_answer
        if not essay_text or len(essay_text.strip()) < 10:
            return jsonify({
                'error': 'Essay text too short for analysis',
                'level': 'warning',
                'score': 0,
                'confidence': 'Text too short for analysis',
                'features': []
            }), 200
        
        # Initialize the detector with the new simplified implementation
        detector = AIContentDetector()
        
        # Get the detection result
        result = detector.detect(essay_text)
        
        # Return JSON response
        return jsonify(result)
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in check_ai_content: {str(e)}")
        # Always return a JSON response even when an error occurs
        return jsonify({
            'error': 'The AI detection service encountered an error. Please try again later.',
            'level': 'danger',
            'score': 0,
            'confidence': 'Error during analysis',
            'features': [{'name': 'Error Details', 'value': str(e)}]
        }), 500

# Instructions for integration:
# 1. Replace the existing check_ai_content function in app.py with this implementation
# 2. Update imports at the top of app.py to use ai_detection_service_new instead of ai_detection_service
# 3. No need to import ai_detection_config_new as it's not used directly in this endpoint