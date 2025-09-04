import subprocess
import sys

def main():
    # Streamlit 앱 실행
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "src/interfaces/streamlit_app.py"
    ])

if __name__ == "__main__":
    main()