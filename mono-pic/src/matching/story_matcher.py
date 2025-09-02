"""
Core story matching logic to combine multimodal inputs
"""

from typing import Dict, Any, List, Optional

class StoryMatcher:
    """Matches and combines story elements from different modalities"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
    def match_characters(self, audio_analysis: Dict, image_analysis: Dict, text_analysis: Dict = None) -> List[Dict[str, Any]]:
        """Match characters across different modalities"""
        matched_characters = []
        
        # Get characters from each modality
        audio_chars = audio_analysis.get('story_elements', {}).get('characters', [])
        image_chars = image_analysis.get('story_elements', {}).get('characters', [])
        text_chars = text_analysis.get('entities', []) if text_analysis else []
        
        # Simple character matching logic
        # TODO: Implement sophisticated matching algorithm
        
        # Add image-based characters as primary
        for img_char in image_chars:
            character = {
                'name': img_char.get('type', 'Unknown'),
                'visual_description': img_char.get('description', ''),
                'modalities': ['image'],
                'confidence': 0.7
            }
            matched_characters.append(character)
            
        # Try to match with audio mentions
        for audio_char in audio_chars:
            # Simple name matching
            char_name = audio_char.get('name', '')
            if char_name:
                # Look for existing character
                existing = next((c for c in matched_characters if char_name.lower() in c['name'].lower()), None)
                if existing:
                    existing['modalities'].append('audio')
                    existing['audio_description'] = audio_char.get('description', '')
                    existing['confidence'] = min(1.0, existing['confidence'] + 0.2)
                else:
                    # New character from audio
                    matched_characters.append({
                        'name': char_name,
                        'audio_description': audio_char.get('description', ''),
                        'modalities': ['audio'],
                        'confidence': 0.6
                    })
                    
        return matched_characters
        
    def match_settings(self, audio_analysis: Dict, image_analysis: Dict, text_analysis: Dict = None) -> Dict[str, Any]:
        """Match setting information across modalities"""
        # Get settings from each modality
        audio_setting = audio_analysis.get('story_elements', {}).get('setting', {})
        image_setting = image_analysis.get('story_elements', {}).get('setting', {})
        
        # Combine setting information
        combined_setting = {
            'location': None,
            'time': None,
            'mood': None,
            'weather': None,
            'confidence': 0.0
        }
        
        # Image provides visual setting info
        if image_setting.get('location'):
            combined_setting['location'] = image_setting['location']
            combined_setting['confidence'] += 0.4
            
        # Audio provides temporal and contextual info
        if audio_setting.get('time'):
            combined_setting['time'] = audio_setting['time']
            combined_setting['confidence'] += 0.3
            
        # Combine mood information
        image_mood = image_analysis.get('mood', {})
        audio_sentiment = audio_analysis.get('sentiment', {})
        
        if image_mood.get('overall_mood'):
            combined_setting['mood'] = image_mood['overall_mood']
            combined_setting['confidence'] += 0.2
            
        return combined_setting
        
    def match_themes(self, audio_analysis: Dict, image_analysis: Dict, text_analysis: Dict = None) -> List[str]:
        """Match and combine themes from different modalities"""
        all_themes = []
        
        # Collect themes from all modalities
        audio_themes = audio_analysis.get('story_elements', {}).get('themes', [])
        image_themes = image_analysis.get('story_elements', {}).get('themes', [])
        text_themes = text_analysis.get('themes', []) if text_analysis else []
        
        # Combine and deduplicate themes
        all_themes.extend(audio_themes)
        all_themes.extend(image_themes)
        all_themes.extend(text_themes)
        
        # Remove duplicates while preserving order
        unique_themes = []
        for theme in all_themes:
            if theme not in unique_themes:
                unique_themes.append(theme)
                
        return unique_themes
        
    def resolve_conflicts(self, audio_analysis: Dict, image_analysis: Dict, text_analysis: Dict = None) -> Dict[str, Any]:
        """Resolve conflicts between different modalities"""
        conflicts = []
        resolutions = {}
        
        # Example: conflicting mood information
        audio_sentiment = audio_analysis.get('sentiment', {}).get('polarity', 0)
        image_mood = image_analysis.get('mood', {}).get('overall_mood', 'neutral')
        
        # Simple conflict resolution logic
        if audio_sentiment > 0.5 and image_mood in ['sad', 'dark', 'gloomy']:
            conflicts.append({
                'type': 'mood_conflict',
                'audio_mood': 'positive',
                'image_mood': image_mood,
                'resolution': 'Use audio as primary (more explicit)'
            })
            resolutions['mood'] = 'positive'
        elif audio_sentiment < -0.5 and image_mood in ['happy', 'bright', 'cheerful']:
            conflicts.append({
                'type': 'mood_conflict',
                'audio_mood': 'negative',
                'image_mood': image_mood,
                'resolution': 'Use audio as primary (more explicit)'
            })
            resolutions['mood'] = 'negative'
            
        return {
            'conflicts': conflicts,
            'resolutions': resolutions
        }
        
    def calculate_story_coherence(self, matched_elements: Dict[str, Any]) -> float:
        """Calculate how coherent the combined story elements are"""
        coherence_score = 0.0
        
        # Factor 1: Character consistency (30%)
        characters = matched_elements.get('characters', [])
        multi_modal_chars = [c for c in characters if len(c.get('modalities', [])) > 1]
        char_score = len(multi_modal_chars) / max(len(characters), 1) if characters else 0
        coherence_score += char_score * 0.3
        
        # Factor 2: Setting consistency (25%)
        setting = matched_elements.get('setting', {})
        setting_confidence = setting.get('confidence', 0)
        coherence_score += setting_confidence * 0.25
        
        # Factor 3: Theme alignment (20%)
        themes = matched_elements.get('themes', [])
        theme_score = min(1.0, len(themes) / 3)  # Ideal: 2-4 themes
        coherence_score += theme_score * 0.2
        
        # Factor 4: Conflict resolution (25%)
        conflicts = matched_elements.get('conflicts', {}).get('conflicts', [])
        conflict_score = 1.0 - (len(conflicts) / 10)  # Penalize conflicts
        coherence_score += max(0, conflict_score) * 0.25
        
        return min(1.0, coherence_score)
        
    def match_multimodal_story(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Main method to match story elements across all modalities"""
        # Separate analysis results by type
        audio_analysis = None
        image_analysis = None
        text_analysis = None
        
        for result in analysis_results:
            if result.get('type') == 'audio':
                audio_analysis = result
            elif result.get('type') == 'image':
                image_analysis = result
            elif result.get('type') == 'text':
                text_analysis = result
                
        # If we don't have at least 2 modalities, return simple result
        if not (audio_analysis and image_analysis):
            return {
                'error': 'Need at least audio and image analysis for story matching',
                'available_modalities': [r.get('type') for r in analysis_results]
            }
            
        # Match story elements
        matched_characters = self.match_characters(audio_analysis, image_analysis, text_analysis)
        matched_setting = self.match_settings(audio_analysis, image_analysis, text_analysis)
        matched_themes = self.match_themes(audio_analysis, image_analysis, text_analysis)
        
        # Resolve conflicts
        conflict_resolution = self.resolve_conflicts(audio_analysis, image_analysis, text_analysis)
        
        # Combine all matched elements
        matched_story = {
            'characters': matched_characters,
            'setting': matched_setting,
            'themes': matched_themes,
            'conflicts': conflict_resolution,
            'modalities_used': [r.get('type') for r in analysis_results],
            'coherence_score': 0.0
        }
        
        # Calculate coherence score
        matched_story['coherence_score'] = self.calculate_story_coherence(matched_story)
        
        return matched_story