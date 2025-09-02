# mono-pic 📚

Transform your memories into beautiful stories using multimodal AI.

## Overview

mono-pic is a multimodal story generation application that creates personalized stories from your photos, audio recordings, and text files. Using advanced AI techniques, it analyzes visual content, speech, and text to craft coherent narratives.

## Current Version: v0.1.0-mvp

This is the MVP (Minimum Viable Product) version with basic functionality for testing the core concept.

### Features
- ✅ File upload interface (images, audio, text)
- ✅ Basic file processing pipeline
- ✅ Streamlit web interface
- ✅ Project structure and configuration
- 🚧 Story generation (placeholder in MVP)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mono-pic
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Upload your files:
   - **Images**: Photos that will inspire your story
   - **Audio**: Voice recordings with story elements
   - **Text**: Written notes or story fragments

4. Configure story settings and click "Generate Story"

## Project Structure

```
mono-pic/
├── src/
│   ├── core/              # Core pipeline and configuration
│   ├── processors/        # File processing modules
│   ├── analyzers/         # Content analysis modules
│   ├── matching/          # Multimodal matching logic
│   ├── generators/        # Story generation (v0.2.0+)
│   └── utils/             # Utility functions
├── templates/             # Story templates
├── tests/                 # Test files
├── versions/              # Version-specific implementations
├── app.py                 # Main Streamlit app
├── requirements.txt       # Dependencies
├── VERSION.md            # Version roadmap
└── README.md             # This file
```

## Roadmap

### v0.1.0-mvp (Current) ✅
- Basic file upload and processing
- Simple web interface
- Core project structure

### v0.2.0-enhanced (Next)
- Audio processing with STT
- Computer vision analysis
- Basic story generation
- Improved templates

### v0.3.0-multimodal
- Advanced multimodal matching
- Emotion detection
- Premium story templates
- Export functionality

### v1.0.0-stable
- Production-ready deployment
- Performance optimization
- Comprehensive testing
- Full documentation

## Contributing

This project follows semantic versioning and uses feature branch development:

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Submit pull request to `develop` branch

## License

[Add your license here]

## Support

For issues and feature requests, please use the GitHub issue tracker.