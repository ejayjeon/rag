#!/usr/bin/env python3
"""
테스트 실행 스크립트

pytest를 사용하여 모든 테스트를 실행하고 결과를 출력합니다.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """테스트 실행"""
    print("=== Multimodal RAG 시스템 테스트 실행 ===\n")
    
    # 프로젝트 루트 디렉토리
    project_root = Path(__file__).parent
    test_dir = project_root / "test"
    
    # pytest 명령어 구성
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(test_dir),
        "-v",  # verbose 출력
        "--tb=short",  # 간단한 traceback
        "--color=yes",  # 컬러 출력
        # "--cov=src",  # 커버리지 측정 (pytest-cov 설치 필요)
        # "--cov-report=term-missing",  # 커버리지 리포트
    ]
    
    try:
        # 테스트 실행
        print(f"실행 명령어: {' '.join(pytest_cmd)}\n")
        result = subprocess.run(pytest_cmd, cwd=project_root, capture_output=False)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ 모든 테스트가 성공적으로 통과했습니다!")
        else:
            print("❌ 일부 테스트가 실패했습니다.")
            print(f"종료 코드: {result.returncode}")
        
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest를 찾을 수 없습니다.")
        print("다음 명령어로 pytest를 설치하세요:")
        print("pip install pytest pytest-mock")
        return 1
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        return 1


def run_specific_test(test_file):
    """특정 테스트 파일 실행"""
    project_root = Path(__file__).parent
    test_path = project_root / "test" / test_file
    
    if not test_path.exists():
        print(f"❌ 테스트 파일을 찾을 수 없습니다: {test_path}")
        return 1
    
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    try:
        result = subprocess.run(pytest_cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        return 1


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        # 특정 테스트 파일 실행
        test_file = sys.argv[1]
        print(f"특정 테스트 실행: {test_file}")
        return run_specific_test(test_file)
    else:
        # 모든 테스트 실행
        return run_tests()


if __name__ == "__main__":
    print("Multimodal RAG 테스트 실행기")
    print("사용법:")
    print("  python run_tests.py                    # 모든 테스트 실행")
    print("  python run_tests.py test_utils.py      # 특정 테스트 실행")
    print()
    
    exit_code = main()
    sys.exit(exit_code)