"""
Text analysis for extracting story elements from text files
"""

import re
from typing import Dict, Any, List

class TextAnalyzer:
    """Analyzes text data for story elements"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        # TODO: Implement proper NER
        entities = []
        
        # Simple regex-based extraction for MVP
        # Names (capitalized words)
        names = re.findall(r'\b[A-Z][a-z]+\b', text)
        for name in set(names):
            if len(name) > 2:  # Filter short words
                entities.append({
                    'text': name,
                    'type': 'PERSON',
                    'confidence': 0.7
                })
                
        # Places (words after prepositions)
        places = re.findall(r'\b(?:in|at|to|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        for place in set(places):
            entities.append({
                'text': place,
                'type': 'PLACE',
                'confidence': 0.6
            })
            
        return entities
        
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis"""
        # TODO: Implement proper sentiment analysis
        positive_words = ['happy', 'joy', 'love', 'wonderful', 'amazing', 'great', 'good', 'beautiful']
        negative_words = ['sad', 'angry', 'hate', 'terrible', 'awful', 'bad', 'horrible', 'ugly']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        
        if total_words == 0:
            polarity = 0.0
        else:
            polarity = (positive_count - negative_count) / total_words
            
        return {
            'polarity': max(-1.0, min(1.0, polarity * 10)),  # Scale and clamp
            'subjectivity': (positive_count + negative_count) / max(total_words, 1),
            'emotions': self._detect_emotions(text_lower)
        }
        
    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotions in text"""
        emotion_keywords = {
            'joy': ['happy', 'joy', 'excited', 'cheerful', 'delighted'],
            'sadness': ['sad', 'cry', 'tears', 'sorrow', 'grief'],
            'anger': ['angry', 'mad', 'furious', 'rage', 'irritated'],
            'fear': ['scared', 'afraid', 'frightened', 'terrified', 'anxious'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished'],
            'love': ['love', 'adore', 'cherish', 'affection', 'devoted']
        }
        
        detected_emotions = []
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_emotions.append(emotion)
                
        return detected_emotions
        
    def extract_story_structure(self, text: str) -> Dict[str, Any]:
        """Extract basic story structure elements"""
        # TODO: Implement story structure analysis
        sentences = text.split('.')
        paragraphs = text.split('\n\n')
        
        # Simple heuristics for story structure
        beginning = sentences[:len(sentences)//3] if len(sentences) > 3 else sentences
        middle = sentences[len(sentences)//3:2*len(sentences)//3] if len(sentences) > 6 else []
        end = sentences[2*len(sentences)//3:] if len(sentences) > 6 else []
        
        return {
            'beginning': '. '.join(beginning).strip(),
            'middle': '. '.join(middle).strip(),
            'end': '. '.join(end).strip(),
            'total_sentences': len(sentences),
            'total_paragraphs': len(paragraphs)
        }
        
    def identify_themes(self, text: str) -> List[str]:
        """Identify potential themes in the text"""
        # TODO: Implement proper theme identification
        theme_keywords = {
            'family': ['family', 'mother', 'father', 'parents', 'children', 'siblings', 'home'],
            'friendship': ['friend', 'friendship', 'buddy', 'companion', 'together'],
            'adventure': ['adventure', 'journey', 'explore', 'discover', 'travel', 'quest'],
            'love': ['love', 'romance', 'relationship', 'heart', 'affection'],
            'growing_up': ['grow', 'learn', 'mature', 'childhood', 'adult', 'change'],
            'nature': ['nature', 'forest', 'ocean', 'mountain', 'animals', 'trees', 'environment'],
            'courage': ['brave', 'courage', 'hero', 'overcome', 'challenge', 'strength'],
            'magic': ['magic', 'magical', 'wizard', 'fairy', 'enchanted', 'spell']
        }
        
        text_lower = text.lower()
        identified_themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                identified_themes.append(theme)
                
        return identified_themes
        
    def analyze(self, text_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis method"""
        content = text_data.get('content', '')
        
        if not content.strip():
            return {'error': 'No text content to analyze'}
            
        # Perform various analyses
        entities = self.extract_entities(content)
        sentiment = self.analyze_sentiment(content)
        structure = self.extract_story_structure(content)
        themes = self.identify_themes(content)
        
        return {
            'content': content,
            'entities': entities,
            'sentiment': sentiment,
            'story_structure': structure,
            'themes': themes,
            'readability': self._assess_readability(content),
            'metadata': text_data.get('metadata', {})
        }
        
    def _assess_readability(self, text: str) -> Dict[str, Any]:
        """Simple readability assessment"""
        words = text.split()
        sentences = text.split('.')
        
        if len(sentences) == 0 or len(words) == 0:
            return {'score': 0, 'level': 'unreadable'}
            
        avg_words_per_sentence = len(words) / len(sentences)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)
        
        # Simple readability score (0-100)
        score = max(0, 100 - (avg_words_per_sentence * 2) - (avg_chars_per_word * 5))
        
        if score >= 90:
            level = 'very_easy'
        elif score >= 80:
            level = 'easy'
        elif score >= 70:
            level = 'fairly_easy'
        elif score >= 60:
            level = 'standard'
        elif score >= 50:
            level = 'fairly_difficult'
        else:
            level = 'difficult'
            
        return {
            'score': score,
            'level': level,
            'avg_words_per_sentence': avg_words_per_sentence,
            'avg_chars_per_word': avg_chars_per_word
        }