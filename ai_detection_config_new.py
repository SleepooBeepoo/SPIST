# AI Detection Configuration (Simplified)

class AIDetectionConfig:
    """Configuration for the simplified AI content detection system"""
    
    # Default settings
    DETECTION_THRESHOLD = 50  # Score threshold for considering content as AI-generated
    
    # Feature weights (can be adjusted for better detection)
    WEIGHTS = {
        'sentence_length': 1.0,      # Weight for sentence length analysis
        'sentence_variance': 1.0,     # Weight for sentence variance analysis
        'formal_phrases': 1.0,        # Weight for formal academic phrase detection
        'repetition': 1.0             # Weight for repetitive pattern detection
    }
    
    @staticmethod
    def get_setup_instructions():
        return """
        AI Content Detection System
        
        This system uses a simplified local detection algorithm that doesn't require
        external API keys or dependencies. It analyzes text patterns commonly found
        in AI-generated content to provide a probability score.
        
        The detection is based on several factors:
        - Sentence length and variance
        - Use of formal academic phrases
        - Repetitive patterns in the text
        
        No configuration is required to use this feature.
        """