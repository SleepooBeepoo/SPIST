import re
import nltk
import requests
import json
import statistics
import os
import sys
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import Counter

# Download necessary NLTK data (will only download if not already present)
def download_nltk_data():
    try:
        # Set NLTK_DATA environment variable to a writable location if not set
        if not os.environ.get('NLTK_DATA'):
            nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
            os.environ['NLTK_DATA'] = nltk_data_dir
            if not os.path.exists(nltk_data_dir):
                os.makedirs(nltk_data_dir, exist_ok=True)
                print(f"Created NLTK data directory: {nltk_data_dir}")
        
        # Check for punkt tokenizer
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        # Check for stopwords
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("Downloading stopwords...")
            nltk.download('stopwords', quiet=True)
            
        return True
    except Exception as e:
        print(f"Error downloading NLTK data: {str(e)}")
        return False

# Initialize NLTK data
nltk_initialized = download_nltk_data()

class AIContentDetector:
    """A service for detecting AI-generated content in text submissions"""
    
    def __init__(self, api_key=None, api_provider='local'):
        """Initialize the detector with optional API credentials"""
        self.api_key = api_key
        self.api_provider = api_provider  # 'local', 'gptzero', or 'originality'
        
        # Verify NLTK initialization
        if not nltk_initialized and self.api_provider == 'local':
            print("WARNING: NLTK data initialization failed. Local detection may not work properly.")
    
    def detect(self, text):
        """Detect if content is AI-generated using the configured provider"""
        try:
            if not text or len(text.strip()) < 10:
                return self._format_result(0, 'Text too short for analysis', [])
                
            if self.api_provider == 'gptzero' and self.api_key:
                return self._detect_with_gptzero(text)
            elif self.api_provider == 'originality' and self.api_key:
                return self._detect_with_originality(text)
            else:
                return self._detect_locally(text)
        except Exception as e:
            print(f"Error in AI detection: {str(e)}")
            return self._format_result(0, 'Error during analysis', [{'name': 'Error', 'value': str(e)}])
    
    def _detect_with_gptzero(self, text):
        """Use GPTZero API to detect AI-generated content"""
        try:
            url = "https://api.gptzero.me/v2/predict/text"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
            data = {"document": text}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Extract the relevant information from GPTZero response
                ai_score = result.get('documents', [{}])[0].get('completely_generated_prob', 0) * 100
                confidence = self._get_confidence_level(ai_score)
                features = [
                    {'name': 'GPTZero AI Score', 'value': f"{ai_score:.1f}%"},
                    {'name': 'Document Classification', 'value': result.get('documents', [{}])[0].get('document_classification', 'Unknown')}
                ]
                return self._format_result(ai_score, confidence, features)
            else:
                # Fall back to local detection if API fails
                return self._detect_locally(text, [{'name': 'API Error', 'value': f"GPTZero API returned status {response.status_code}"}])
        except Exception as e:
            # Fall back to local detection if API call fails
            return self._detect_locally(text, [{'name': 'API Error', 'value': str(e)}])
    
    def _detect_with_originality(self, text):
        """Use Originality.ai API to detect AI-generated content"""
        try:
            url = "https://api.originality.ai/api/v1/scan/ai"
            headers = {
                "X-OAI-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            data = {"content": text}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Extract the relevant information from Originality.ai response
                ai_score = result.get('ai_score', 0) * 100
                confidence = self._get_confidence_level(ai_score)
                features = [
                    {'name': 'Originality.ai Score', 'value': f"{ai_score:.1f}%"},
                    {'name': 'AI Model', 'value': result.get('ai_model', 'Unknown')}
                ]
                return self._format_result(ai_score, confidence, features)
            else:
                # Fall back to local detection if API fails
                return self._detect_locally(text, [{'name': 'API Error', 'value': f"Originality.ai API returned status {response.status_code}"}])
        except Exception as e:
            # Fall back to local detection if API call fails
            return self._detect_locally(text, [{'name': 'API Error', 'value': str(e)}])
    
    def _detect_locally(self, text, additional_features=None):
        """Use local heuristics to detect AI-generated content"""
        features = additional_features or []
        
        try:
            # Tokenize the text
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            # Basic statistics
            word_count = len(words)
            sentence_count = len(sentences)
            avg_sentence_length = word_count / max(sentence_count, 1)
        except Exception as e:
            print(f"Error in text tokenization: {str(e)}")
            # Fallback to simple tokenization
            sentences = text.split('.')
            words = text.lower().split()
            word_count = len(words)
            sentence_count = len(sentences)
            avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Calculate sentence length variance (AI tends to have more uniform sentence lengths)
        try:
            if sentence_count > 1:
                try:
                    sentence_lengths = [len(word_tokenize(s)) for s in sentences]
                except Exception:
                    # Fallback to simple word counting if tokenization fails
                    sentence_lengths = [len(s.split()) for s in sentences]
                
                try:
                    sentence_length_variance = statistics.variance(sentence_lengths) if len(sentence_lengths) > 1 else 0
                except Exception as e:
                    print(f"Error calculating variance: {str(e)}")
                    sentence_length_variance = 0
                    
                sentence_length_variance_normalized = min(sentence_length_variance / 10, 1)  # Normalize to 0-1 range
            else:
                sentence_length_variance_normalized = 0
        except Exception as e:
            print(f"Error in sentence length analysis: {str(e)}")
            sentence_length_variance_normalized = 0
        
        # Check for formal academic phrases (common in AI writing)
        try:
            formal_phrases = [
                'furthermore', 'moreover', 'in conclusion', 'subsequently', 'nevertheless',
                'in addition', 'consequently', 'thus', 'hence', 'therefore', 'in summary',
                'in essence', 'in other words', 'to illustrate', 'for instance'
            ]
            formal_count = sum(1 for phrase in formal_phrases if phrase in text.lower())
            formal_ratio = formal_count / max(sentence_count, 1)
        except Exception as e:
            print(f"Error in formal phrase detection: {str(e)}")
            formal_ratio = 0
        
        # Check for repetitive phrases (AI sometimes repeats patterns)
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
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