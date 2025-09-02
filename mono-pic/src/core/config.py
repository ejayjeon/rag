"""
Configuration management for mono-pic
"""

import os
from typing import Dict, Any

class Config:
    """Configuration manager for the application"""
    
    def __init__(self):
        self.settings = {
            # API Keys
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            
            # Model settings
            'speech_model': 'whisper-1',
            'vision_model': 'gpt-4-vision-preview',
            'text_model': 'gpt-4',
            
            # Processing settings
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'supported_audio_formats': ['.mp3', '.wav', '.m4a'],
            'supported_image_formats': ['.jpg', '.jpeg', '.png'],
            
            # Story generation
            'story_length': 'medium',  # short, medium, long
            'story_style': 'creative',
            
            # Output settings
            'output_format': 'html',
            'template': 'basic'
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.settings[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values"""
        self.settings.update(updates)