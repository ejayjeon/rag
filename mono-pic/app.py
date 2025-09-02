"""
Streamlit app for mono-pic multimodal story generation
"""

import streamlit as st
import tempfile
import os
from pathlib import Path

# Import our modules
from src.core.pipeline import StoryPipeline
from src.core.config import Config
from src.processors.file_handler import FileHandler

def main():
    st.set_page_config(
        page_title="mono-pic - Multimodal Story Generator",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 mono-pic")
    st.subheader("Transform your memories into beautiful stories")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Settings")
        
        # Story settings
        story_length = st.selectbox(
            "Story Length",
            ["Short", "Medium", "Long"],
            index=1
        )
        
        story_style = st.selectbox(
            "Story Style", 
            ["Creative", "Realistic", "Fairytale", "Adventure"],
            index=0
        )
        
        # Template selection
        template = st.selectbox(
            "Template",
            ["Basic", "Premium"],
            index=0
        )
        
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Upload Your Files")
        
        # File uploaders
        audio_files = st.file_uploader(
            "Upload Audio Files 🎵",
            type=['mp3', 'wav', 'm4a'],
            accept_multiple_files=True,
            help="Upload audio recordings to extract story elements"
        )
        
        image_files = st.file_uploader(
            "Upload Images 🖼️",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            accept_multiple_files=True,
            help="Upload images that will inspire your story"
        )
        
        text_files = st.file_uploader(
            "Upload Text Files 📝",
            type=['txt', 'md'],
            accept_multiple_files=True,
            help="Upload text files with story ideas or content"
        )
        
        # Generate button
        if st.button("✨ Generate Story", type="primary", use_container_width=True):
            generate_story(audio_files, image_files, text_files, story_length, story_style, template)
    
    with col2:
        st.header("Preview")
        
        # File preview
        all_files = []
        if audio_files:
            all_files.extend([(f, "Audio") for f in audio_files])
        if image_files:
            all_files.extend([(f, "Image") for f in image_files])  
        if text_files:
            all_files.extend([(f, "Text") for f in text_files])
            
        if all_files:
            st.write(f"📁 {len(all_files)} files ready to process:")
            
            for file_obj, file_type in all_files:
                with st.expander(f"{file_type}: {file_obj.name}"):
                    if file_type == "Image":
                        st.image(file_obj, width=300)
                    elif file_type == "Text":
                        content = str(file_obj.read(), "utf-8")
                        st.text_area("Content", content[:500] + "..." if len(content) > 500 else content, height=100)
                        file_obj.seek(0)  # Reset file pointer
                    else:
                        st.write(f"File size: {file_obj.size} bytes")
        else:
            st.info("Upload files to see preview here")

def generate_story(audio_files, image_files, text_files, story_length, story_style, template):
    """Generate story from uploaded files"""
    
    # Check if we have any files
    all_files = (audio_files or []) + (image_files or []) + (text_files or [])
    if not all_files:
        st.error("Please upload at least one file to generate a story!")
        return
        
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize configuration
        config = Config()
        config.update({
            'story_length': story_length.lower(),
            'story_style': story_style.lower(), 
            'template': template.lower()
        })
        
        # Initialize pipeline
        pipeline = StoryPipeline(config)
        file_handler = FileHandler(config)
        
        # Process files
        status_text.text("Processing files...")
        progress_bar.progress(25)
        
        processed_files = []
        
        # Save uploaded files temporarily and process them
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_paths = []
            
            # Save all uploaded files
            for file_obj in all_files:
                temp_file_path = os.path.join(temp_dir, file_obj.name)
                with open(temp_file_path, 'wb') as f:
                    f.write(file_obj.getbuffer())
                temp_file_paths.append(temp_file_path)
                
            # Process files
            processed_files = file_handler.process_multiple_files(temp_file_paths)
            
        progress_bar.progress(50)
        status_text.text("Analyzing content...")
        
        # For MVP, show processed results instead of full story generation
        progress_bar.progress(100)
        status_text.text("Story generated successfully!")
        
        # Display results
        st.success("🎉 Processing Complete!")
        
        # Show analysis results
        with st.expander("📊 Analysis Results", expanded=True):
            for i, result in enumerate(processed_files):
                st.subheader(f"File {i+1}: {result.get('source', 'Unknown')}")
                
                if result.get('type') == 'error':
                    st.error(f"Error processing file: {result.get('error')}")
                else:
                    st.write(f"**Type:** {result.get('type', 'Unknown')}")
                    
                    if result.get('type') == 'image':
                        metadata = result.get('metadata', {})
                        st.write(f"**Dimensions:** {metadata.get('width')}x{metadata.get('height')}")
                        
                    elif result.get('type') == 'audio':
                        speech_data = result.get('speech_data', {})
                        st.write(f"**Duration:** {speech_data.get('duration', 0)} seconds")
                        st.write(f"**Language:** {speech_data.get('language', 'Unknown')}")
                        
                    elif result.get('type') == 'text':
                        metadata = result.get('metadata', {})
                        st.write(f"**Word count:** {metadata.get('word_count', 0)}")
                        
        # MVP placeholder for story output
        with st.expander("📖 Generated Story (MVP - Placeholder)", expanded=True):
            st.markdown(f"""
            ## A {story_style} Story
            
            *Generated from your {len(all_files)} uploaded files*
            
            Once upon a time, in a world filled with memories and moments captured in pictures and sounds...
            
            [This is a placeholder for the MVP version. The full story generation will be implemented in v0.2.0]
            
            **Story Elements Detected:**
            - Files processed: {len(processed_files)}
            - Style: {story_style}
            - Length: {story_length}
            - Template: {template}
            """)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        progress_bar.progress(0)
        status_text.text("Error occurred during processing")

if __name__ == "__main__":
    main()