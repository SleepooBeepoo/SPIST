"""Document Import Module

This module serves as a bridge between the quiz module and the document processor.
It handles the importing of questions from document files (.docx, .pdf).
"""

import os
import docx  # python-docx package
import PyPDF2
from werkzeug.utils import secure_filename
from document_processor import DocumentProcessor

class DocumentImport:
    """Class to handle importing questions from document files"""
    
    def __init__(self):
        """Initialize the document importer"""
        self.processor = DocumentProcessor()
    
    def import_questions_from_file(self, file, upload_dir=None, use_ai=True):
        """Import questions from a document file
        
        Args:
            file: The uploaded file object
            upload_dir: The directory to save the file to (optional)
            use_ai: Whether to use AI to extract questions
            
        Returns:
            Tuple[List[Dict], Optional[str]]: A tuple containing the list of extracted questions
                and an optional error message
        """
        if not upload_dir:
            # Use default upload directory if none provided
            upload_dir = os.path.join('uploads', 'documents')
            
            # Ensure the upload directory exists
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
        
        try:
            # Save the uploaded file
            file_path = self.processor.save_uploaded_file(file, upload_dir)
            
            # Process the file to extract questions
            questions, error = self.processor.process_file(file_path, use_ai=use_ai)
            
            return questions, error
        except Exception as e:
            return [], f"Error importing questions: {str(e)}"

# Create a singleton instance for easy importing
document_import = DocumentImport()

# Function to directly import questions from a file
def import_questions(file, upload_dir=None, use_ai=True):
    """Import questions from a document file
    
    Args:
        file: The uploaded file object
        upload_dir: The directory to save the file to (optional)
        use_ai: Whether to use AI to extract questions
        
    Returns:
        Tuple[List[Dict], Optional[str]]: A tuple containing the list of extracted questions
            and an optional error message
    """
    return document_import.import_questions_from_file(file, upload_dir, use_ai)