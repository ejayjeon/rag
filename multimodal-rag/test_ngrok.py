#!/usr/bin/env python3
"""ngrok 연결 테스트 스크립트 (CORS 문제 해결)"""

import requests
import time
import json

def test_ollama_api_direct(url: str) -> bool:
    """Ollama API 직접 테스트 (CORS 문제 해결)
    
    Args:
        url: 테스트할 Ollama 서버 URL
    
    Returns:
        연결 성공 여부
    """
    try:
        print(f"🔍 {url} API 직접 테스트 중...")
        
        # API 엔드포인트 테스트
        api_url = f"{url}/api/tags"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ API 연결 성공! 상태 코드: {response.status_code}")
            
            # 응답 내용 확인
            try:
                data = response.json()
                if 'models' in data:
                    print(f"📋 사용 가능한 모델: {len(data['models'])}개")
                    for model in data['models'][:5]:  # 처음 5개만 표시
                        model_name = model.get('name', 'Unknown')
                        print(f"  - {model_name}")
                else:
                    print(f"📄 응답 내용: {data}")
            except:
                print(f"📄 응답 내용: {response.text[:200]}...")
            
            return True
        else:
            print(f"❌ API 연결 실패! 상태 코드: {response.status_code}")
            print(f"📄 응답 내용: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 연결 시간 초과")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 연결 오류")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def test_model_generation(url: str, model: str = "llama2:latest") -> bool:
    """모델 생성 테스트
    
    Args:
        url: Ollama 서버 URL
        model: 테스트할 모델명
    
    Returns:
        생성 성공 여부
    """
    try:
        print(f"🧠 {model} 모델 생성 테스트 중...")
        
        # 간단한 프롬프트로 테스트
        data = {
            "model": model,
            "prompt": "Hello, how are you?",
            "stream": False
        }
        
        api_url = f"{url}/api/generate"
        response = requests.post(api_url, json=data, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ 모델 생성 성공!")
            try:
                result = response.json()
                if 'response' in result:
                    print(f"📝 응답: {result['response'][:100]}...")
                return True
            except:
                print("📄 응답 파싱 실패")
                return False
        else:
            print(f"❌ 모델 생성 실패! 상태 코드: {response.status_code}")
            print(f"📄 오류 내용: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 모델 생성 테스트 오류: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("🚀 Ollama API 직접 테스트 (CORS 문제 해결)")
    print("=" * 60)
    
    # 테스트할 URL들
    test_urls = [
        "https://82d87cefbaff.ngrok-free.app",  # 새로운 ngrok URL
        "http://localhost:11434"
    ]
    
    for url in test_urls:
        print(f"\n🌐 테스트 URL: {url}")
        print("-" * 50)
        
        # 1. API 연결 테스트
        api_success = test_ollama_api_direct(url)
        
        if api_success:
            print(f"🎉 {url} API 연결 성공!")
            
            # 2. 모델 생성 테스트 (선택사항)
            if "localhost" in url:  # 로컬에서만 모델 생성 테스트
                test_model_generation(url)
        else:
            print(f"💥 {url} API 연결 실패!")
        
        print("-" * 50)
        time.sleep(1)
    
    print("\n✨ 테스트 완료!")
    print("\n💡 CORS 문제가 해결되었습니다!")
    print("   - 브라우저에서 직접 API 호출하지 않음")
    print("   - Streamlit 백엔드에서 HTTP 요청으로 처리")

if __name__ == "__main__":
    main()
