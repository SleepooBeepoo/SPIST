import re
import statistics
import os
import sys
from collections import Counter

class AIContentDetector:
    """A simplified and robust service for detecting AI-generated content in text submissions"""
    
    def __init__(self):
        """Initialize the detector with local detection capabilities only"""
        pass
    
    def detect(self, text):
        """Detect if content is AI-generated using local analysis methods"""
        try:
            if not text or len(text.strip()) < 10:
                return self._format_result(0, 'Text too short for analysis', [])
                
            return self._detect_locally(text)
        except Exception as e:
            print(f"Error in AI detection: {str(e)}")
            return self._format_result(0, 'Error during analysis', [{'name': 'Error', 'value': str(e)}])
    
    def _detect_locally(self, text, additional_features=None):
        """Use local heuristics to detect AI-generated content without external dependencies"""
        features = additional_features or []
        
        try:
            # Simple tokenization without NLTK dependency
            sentences = self._split_into_sentences(text)
            words = self._split_into_words(text)
            
            # Basic statistics
            word_count = len(words)
            sentence_count = len(sentences)
            avg_sentence_length = word_count / max(sentence_count, 1)
            
            # Calculate sentence length variance (AI tends to have more uniform sentence lengths)
            if sentence_count > 1:
                sentence_lengths = [len(self._split_into_words(s)) for s in sentences]
                
                # Calculate variance manually if there are enough sentences
                if len(sentence_lengths) > 1:
                    mean = sum(sentence_lengths) / len(sentence_lengths)
                    variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                else:
                    variance = 0
                    
                sentence_length_variance_normalized = min(variance / 10, 1)  # Normalize to 0-1 range
            else:
                sentence_length_variance_normalized = 0
            
            # Check for formal academic phrases (common in AI writing)
            formal_phrases = [
                'furthermore', 'moreover', 'in conclusion', 'subsequently', 'nevertheless',
                'in addition', 'consequently', 'thus', 'hence', 'therefore', 'in summary',
                'in essence', 'in other words', 'to illustrate', 'for instance'
            ]
            formal_count = sum(1 for phrase in formal_phrases if phrase.lower() in text.lower())
            formal_ratio = formal_count / max(sentence_count, 1)
            
            # Check for repetitive phrases
            text_lower = text.lower()
            word_list = self._split_into_words(text_lower)
            bigrams = [' '.join(word_list[i:i+2]) for i in range(len(word_list)-1)]
            bigram_counts = {}
            for bigram in bigrams:
                bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1
            repetition_score = sum(count for phrase, count in bigram_counts.items() if count > 1) / max(len(bigrams), 1)
            
            # Calculate base score
            base_score = 0
            
            # Very long average sentence length might indicate AI
            if avg_sentence_length > 25:
                base_score += 25
            elif avg_sentence_length > 20:
                base_score += 15
            elif avg_sentence_length > 15:
                base_score += 5
            
            # Low sentence length variance might indicate AI
            base_score += (1 - sentence_length_variance_normalized) * 20
            
            # High formal phrase usage might indicate AI
            base_score += formal_ratio * 30
            
            # High repetition might indicate AI
            base_score += repetition_score * 15
            
            # Cap the score at 100
            ai_score = min(base_score, 100)
            
            # Add features for the report
            features.extend([
                {'name': 'Word Count', 'value': word_count},
                {'name': 'Sentence Count', 'value': sentence_count},
                {'name': 'Avg. Sentence Length', 'value': f"{avg_sentence_length:.1f}"},
                {'name': 'Formal Phrases', 'value': formal_count},
                {'name': 'Repetition Score', 'value': f"{repetition_score:.2f}"},
            ])
            
            confidence = self._get_confidence_level(ai_score)
            
            return self._format_result(ai_score, confidence, features)
        except Exception as e:
            print(f"Error in local detection: {str(e)}")
            return self._format_result(0, 'Error during analysis', [{'name': 'Error', 'value': str(e)}])
    
    def _split_into_sentences(self, text):
        """Split text into sentences without using NLTK"""
        # Simple sentence splitting by common sentence terminators
        text = text.replace('\n', ' ')
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1\n\2', text)
        text = re.sub(r'([.!?])([\'\"])\s+([A-Z])', r'\1\2\n\3', text)
        return [s.strip() for s in text.split('\n') if s.strip()]
    
    def _split_into_words(self, text):
        """Split text into words without using NLTK"""
        # Remove punctuation and split by whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text.split() if w]
    
    def _get_confidence_level(self, score):
        """Determine confidence level based on score"""
        if score > 70:
            return {'message': 'High probability of AI-generated content', 'level': 'danger'}
        elif score > 40:
            return {'message': 'Moderate probability of AI-generated content', 'level': 'warning'}
        else:
            return {'message': 'Low probability of AI-generated content', 'level': 'success'}
    
    def _format_result(self, score, confidence, features):
        """Format the detection result"""
        return {
            'score': round(score, 1),
            'confidence': confidence['message'],
            'level': confidence['level'],
            'features': features
        }