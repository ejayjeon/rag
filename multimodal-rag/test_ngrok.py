#!/usr/bin/env python3
"""ngrok 연결 테스트 스크립트"""

import requests
import time

def test_ngrok_connection(url: str) -> bool:
    """ngrok 연결 테스트
    
    Args:
        url: 테스트할 ngrok URL
    
    Returns:
        연결 성공 여부
    """
    try:
        print(f"🔍 {url} 연결 테스트 중...")
        
        # 기본 연결 테스트
        response = requests.get(f"{url}/api/tags", timeout=10)
        if response.status_code == 200:
            print(f"✅ 연결 성공! 상태 코드: {response.status_code}")
            
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
            print(f"❌ 연결 실패! 상태 코드: {response.status_code}")
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

def main():
    """메인 함수"""
    print("🚀 ngrok Ollama 연결 테스트")
    print("=" * 50)
    
    # 테스트할 URL들
    test_urls = [
        "https://872621f41ae7.ngrok-free.app",
        "http://localhost:11434"
    ]
    
    for url in test_urls:
        print(f"\n🌐 테스트 URL: {url}")
        success = test_ngrok_connection(url)
        
        if success:
            print(f"🎉 {url} 연결 성공!")
        else:
            print(f"💥 {url} 연결 실패!")
        
        print("-" * 30)
        time.sleep(1)
    
    print("\n✨ 테스트 완료!")

if __name__ == "__main__":
    main()
