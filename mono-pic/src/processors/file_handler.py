"""
Universal file handler for different input types
"""

import os
from typing import List, Dict, Any, Union
from .audio_processor import AudioProcessor
from .image_processor import ImageProcessor

class FileHandler:
    """Universal file handler that routes files to appropriate processors"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.audio_processor = AudioProcessor(config)
        self.image_processor = ImageProcessor(config)
        
        # File type mappings
        self.audio_extensions = ['.mp3', '.wav', '.m4a', '.flac']
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        self.text_extensions = ['.txt', '.md']
        
    def detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension"""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext in self.audio_extensions:
            return 'audio'
        elif ext in self.image_extensions:
            return 'image'
        elif ext in self.text_extensions:
            return 'text'
        else:
            return 'unknown'
            
    def validate_file(self, file_path: str) -> bool:
        """Validate file exists and is accessible"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
        
    def process_text_file(self, file_path: str) -> Dict[str, Any]:
        """Process text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            'type': 'text',
            'source': file_path,
            'content': content,
            'metadata': {
                'file_size': os.path.getsize(file_path),
                'word_count': len(content.split()),
                'char_count': len(content)
            }
        }
        
    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file"""
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_type = self.detect_file_type(file_path)
        
        if file_type == 'audio':
            return self.audio_processor.process(file_path)
        elif file_type == 'image':
            return self.image_processor.process(file_path)
        elif file_type == 'text':
            return self.process_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
            
    def process_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple files"""
        results = []
        
        for file_path in file_paths:
            try:
                result = self.process_single_file(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    'type': 'error',
                    'source': file_path,
                    'error': str(e)
                })
                
        return results
        
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        return {
            'audio': self.audio_extensions,
            'image': self.image_extensions,
            'text': self.text_extensions
        }