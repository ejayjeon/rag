#!/usr/bin/env python3
"""
의존성 설치 스크립트

이 스크립트는 multimodal RAG 시스템에 필요한 모든 의존성을 설치합니다.
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        return False
    print(f"✅ Python 버전: {sys.version.split()[0]}")
    return True


def install_package(package_name, description=""):
    """패키지 설치"""
    print(f"📦 {description or package_name} 설치 중...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {package_name} 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 설치 실패: {e.stderr}")
        return False


def install_basic_dependencies():
    """기본 의존성 설치"""
    print("\n=== 기본 의존성 설치 ===")
    
    basic_packages = [
        ("pytest", "테스팅 프레임워크"),
        ("pytest-mock", "모킹 라이브러리"),
        ("requests", "HTTP 클라이언트"),
        ("Pillow", "이미지 처리 라이브러리"),
        ("streamlit", "웹 애플리케이션 프레임워크"),
    ]
    
    success_count = 0
    for package, description in basic_packages:
        if install_package(package, description):
            success_count += 1
    
    print(f"기본 패키지: {success_count}/{len(basic_packages)} 성공")
    return success_count == len(basic_packages)


def install_ai_dependencies():
    """AI/ML 의존성 설치"""
    print("\n=== AI/ML 의존성 설치 ===")
    
    ai_packages = [
        ("langchain", "LangChain 프레임워크"),
        ("langchain-community", "LangChain 커뮤니티 패키지"),
        ("langchain-text-splitters", "텍스트 분할기"),
        ("langchain-ollama", "Ollama 통합"),
        ("chromadb", "벡터 데이터베이스"),
        ("sentence-transformers", "임베딩 모델"),
    ]
    
    success_count = 0
    for package, description in ai_packages:
        if install_package(package, description):
            success_count += 1
    
    print(f"AI/ML 패키지: {success_count}/{len(ai_packages)} 성공")
    return success_count == len(ai_packages)


def install_optional_dependencies():
    """선택적 의존성 설치"""
    print("\n=== 선택적 의존성 설치 ===")
    
    optional_packages = [
        ("PyMuPDF", "PDF 처리 라이브러리"),
        ("pytesseract", "OCR 라이브러리"),
        ("ollama", "Ollama 클라이언트"),
    ]
    
    success_count = 0
    for package, description in optional_packages:
        if install_package(package, description):
            success_count += 1
    
    print(f"선택적 패키지: {success_count}/{len(optional_packages)} 성공")
    return success_count


def test_imports():
    """핵심 모듈 import 테스트"""
    print("\n=== Import 테스트 ===")
    
    test_modules = [
        ("langchain", "LangChain"),
        ("langchain_community.embeddings", "LangChain Community"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "Sentence Transformers"),
    ]
    
    success_count = 0
    for module, name in test_modules:
        try:
            __import__(module)
            print(f"✅ {name} import 성공")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name} import 실패: {e}")
    
    print(f"Import 테스트: {success_count}/{len(test_modules)} 성공")
    return success_count == len(test_modules)


def create_requirements_txt():
    """requirements.txt 생성"""
    print("\n=== requirements.txt 생성 ===")
    
    requirements_content = """# Multimodal RAG Dependencies

# Core dependencies
langchain>=0.3.0
langchain-community>=0.3.0
langchain-text-splitters>=0.3.0
langchain-ollama>=0.3.0
chromadb>=1.0.0
sentence-transformers>=5.0.0

# Utilities
requests>=2.32.0
Pillow>=10.0.0
streamlit>=1.28.0

# PDF and Image processing
PyMuPDF>=1.26.0
pytesseract>=0.3.10
ollama>=0.5.0

# Testing
pytest>=8.0.0
pytest-mock>=3.14.0
"""
    
    requirements_path = Path("requirements.txt")
    try:
        requirements_path.write_text(requirements_content)
        print(f"✅ requirements.txt 생성됨: {requirements_path.absolute()}")
        return True
    except Exception as e:
        print(f"❌ requirements.txt 생성 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("🚀 Multimodal RAG 의존성 설치 스크립트")
    print("=" * 50)
    
    # Python 버전 확인
    if not check_python_version():
        return 1
    
    # pip 업그레이드
    print("\n📦 pip 업그레이드...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                   capture_output=True)
    
    # 의존성 설치
    basic_success = install_basic_dependencies()
    ai_success = install_ai_dependencies() 
    optional_count = install_optional_dependencies()
    
    # Import 테스트
    import_success = test_imports()
    
    # requirements.txt 생성
    req_success = create_requirements_txt()
    
    # 결과 출력
    print("\n" + "=" * 50)
    print("📊 설치 결과:")
    print(f"✅ 기본 패키지: {'성공' if basic_success else '일부 실패'}")
    print(f"✅ AI/ML 패키지: {'성공' if ai_success else '일부 실패'}")
    print(f"✅ 선택적 패키지: {optional_count}개 설치됨")
    print(f"✅ Import 테스트: {'성공' if import_success else '일부 실패'}")
    print(f"✅ requirements.txt: {'생성됨' if req_success else '실패'}")
    
    if basic_success and ai_success and import_success:
        print("\n🎉 모든 필수 의존성이 성공적으로 설치되었습니다!")
        print("\n다음 명령어로 시스템을 테스트할 수 있습니다:")
        print("python run_tests.py")
        print("python example_usage.py")
        return 0
    else:
        print("\n⚠️  일부 의존성 설치에 실패했습니다.")
        print("수동으로 다음 명령어를 실행해보세요:")
        print("pip install langchain langchain-community chromadb sentence-transformers")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)