"""Service layer for AI content detection functionality"""
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
from typing import Dict, Any, Tuple, List, Optional
from flask import current_app
import logging

class AIDetectionService:
    """Service for detecting AI-generated content in text submissions"""
    
    def __init__(self, api_key: Optional[str] = None, api_provider: str = 'local'):
        """Initialize the detector with optional API credentials
        
        Args:
            api_key: Optional API key for external detection services
            api_provider: The provider to use ('local' or external service name)
        """
        self.api_key = api_key
        self.api_provider = api_provider
        self.initialize_nltk()
    
    def initialize_nltk(self) -> bool:
        """Initialize NLTK data required for text analysis
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Set NLTK_DATA environment variable to a writable location if not set
            if not os.environ.get('NLTK_DATA'):
                nltk_data_dir = os.path.join(current_app.root_path, '..', 'nltk_data')
                os.environ['NLTK_DATA'] = nltk_data_dir
                if not os.path.exists(nltk_data_dir):
                    os.makedirs(nltk_data_dir, exist_ok=True)
                    current_app.logger.info(f"Created NLTK data directory: {nltk_data_dir}")
            
            # Check for punkt tokenizer
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                current_app.logger.info("Downloading punkt tokenizer...")
                nltk.download('punkt', quiet=True)
            
            # Check for stopwords
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                current_app.logger.info("Downloading stopwords...")
                nltk.download('stopwords', quiet=True)
                
            return True
        except Exception as e:
            current_app.logger.error(f"Error initializing NLTK data: {str(e)}")
            return False
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text for AI-generated content indicators
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if self.api_provider != 'local':
                return self._analyze_with_external_api(text)
            
            # Local analysis implementation
            result = {
                'ai_probability': 0.0,
                'human_probability': 0.0,
                'indicators': {},
                'confidence': 0.0,
                'verdict': 'unknown'
            }
            
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Skip analysis if text is too short
            if len(cleaned_text.split()) < 50:
                result['verdict'] = 'insufficient_text'
                result['confidence'] = 0.0
                return result
            
            # Perform various analyses
            indicators = {}
            
            # Analyze sentence structure
            sentence_metrics = self._analyze_sentence_structure(cleaned_text)
            indicators.update(sentence_metrics)
            
            # Analyze vocabulary diversity
            vocab_metrics = self._analyze_vocabulary(cleaned_text)
            indicators.update(vocab_metrics)
            
            # Calculate overall probability
            ai_indicators = sum(1 for score in indicators.values() if score > 0.7)
            human_indicators = sum(1 for score in indicators.values() if score < 0.3)
            total_indicators = len(indicators)
            
            if total_indicators > 0:
                ai_probability = ai_indicators / total_indicators
                human_probability = human_indicators / total_indicators
                
                # Determine verdict
                if ai_probability > 0.7:
                    verdict = 'ai_generated'
                    confidence = ai_probability
                elif human_probability > 0.7:
                    verdict = 'human_written'
                    confidence = human_probability
                else:
                    verdict = 'uncertain'
                    confidence = max(ai_probability, human_probability)
                
                result['ai_probability'] = round(ai_probability, 2)
                result['human_probability'] = round(human_probability, 2)
                result['indicators'] = indicators
                result['confidence'] = round(confidence, 2)
                result['verdict'] = verdict
            
            return result
        except Exception as e:
            current_app.logger.error(f"Error analyzing text: {str(e)}")
            return {
                'error': str(e),
                'verdict': 'error',
                'confidence': 0.0
            }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis
        
        Args:
            text: The raw text to preprocess
            
        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _analyze_sentence_structure(self, text: str) -> Dict[str, float]:
        """Analyze sentence structure for AI indicators
        
        Args:
            text: The preprocessed text to analyze
            
        Returns:
            Dictionary of sentence structure metrics
        """
        sentences = sent_tokenize(text)
        
        # Skip if too few sentences
        if len(sentences) < 3:
            return {'sentence_variety': 0.5}
        
        # Calculate sentence length statistics
        sentence_lengths = [len(s.split()) for s in sentences]
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        std_dev = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # AI text often has more uniform sentence lengths
        sentence_variety = min(1.0, std_dev / (avg_length * 0.5))
        
        return {
            'sentence_variety': round(sentence_variety, 2),
            'avg_sentence_length': round(avg_length, 2)
        }
    
    def _analyze_vocabulary(self, text: str) -> Dict[str, float]:
        """Analyze vocabulary diversity for AI indicators
        
        Args:
            text: The preprocessed text to analyze
            
        Returns:
            Dictionary of vocabulary metrics
        """
        words = word_tokenize(text.lower())
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        content_words = [w for w in words if w.isalpha() and w not in stop_words]
        
        # Skip if too few words
        if len(content_words) < 50:
            return {'lexical_diversity': 0.5}
        
        # Calculate lexical diversity (unique words / total words)
        unique_words = set(content_words)
        lexical_diversity = len(unique_words) / len(content_words)
        
        # AI text often has higher lexical diversity
        ai_probability_from_diversity = lexical_diversity * 1.5 if lexical_diversity > 0.6 else lexical_diversity
        ai_probability_from_diversity = min(1.0, ai_probability_from_diversity)
        
        return {
            'lexical_diversity': round(lexical_diversity, 2),
            'unique_word_count': len(unique_words),
            'total_word_count': len(content_words)
        }
    
    def _analyze_with_external_api(self, text: str) -> Dict[str, Any]:
        """Analyze text using an external API
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing analysis results from the external API
        """
        try:
            # This is a placeholder for external API integration
            # In a real implementation, this would make an API call to the specified provider
            current_app.logger.warning("External API analysis not implemented. Using local analysis.")
            
            # Fall back to local analysis
            return self.analyze_text(text)
        except Exception as e:
            current_app.logger.error(f"Error with external API: {str(e)}")
            return {
                'error': str(e),
                'verdict': 'error',
                'confidence': 0.0
            }