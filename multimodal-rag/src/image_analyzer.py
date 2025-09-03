# 안전한 import with 폴백
try:
    import ollama
except ImportError:
    ollama = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    try:
        from langchain.llms import Ollama as ChatOllama
    except ImportError:
        ChatOllama = None

# OpenAI Vision 지원 추가
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

try:
    from PIL import Image
except ImportError:
    try:
        import PIL.Image as Image
    except ImportError:
        Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from typing import Optional, List
import logging
import base64
import io

class ImageAnalyzer:
    """이미지 분석 전용 클래스"""
    
    def __init__(
        self, 
        model_name: str = "llava", 
        provider: str = "ollama",
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # OpenAI 클라이언트 초기화
        if provider == "openai" and api_key and OpenAI:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
        
        # 의존성 확인
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """이미지 분석에 필요한 의존성 확인"""
        missing_deps = []
        
        if self.provider == "openai":
            if not OpenAI or not openai:
                missing_deps.append("openai")
            if not self.api_key:
                missing_deps.append("OpenAI API key")
        elif self.provider == "ollama":
            if not ollama and not ChatOllama:
                missing_deps.append("ollama 또는 langchain_ollama")
        
        if not Image:
            missing_deps.append("PIL (Pillow)")
        
        if missing_deps:
            deps_str = ", ".join(missing_deps)
            self.logger.warning(f"일부 의존성이 누락됨: {deps_str}")
            self.logger.warning("이미지 분석 기능이 제한될 수 있습니다.")
    
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None) -> str:
        """이미지 분석"""
        # 파일 존재 확인
        from pathlib import Path
        if not Path(image_path).exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        # 확장자 검증
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"지원하지 않는 이미지 형식입니다. 지원 형식: {valid_extensions}")
        
        default_prompt = """이 이미지를 자세히 분석해주세요:
        1. 주요 객체나 요소들
        2. 텍스트가 있다면 내용
        3. 차트나 그래프가 있다면 설명
        4. 전체적인 내용이나 맥락
        
        한국어로 상세하게 설명해주세요."""
        
        prompt = custom_prompt or default_prompt
        
        try:
            if self.provider == "openai" and self.openai_client:
                # OpenAI Vision API 사용
                return self._analyze_with_openai(image_path, prompt)
            elif self.provider == "ollama" and ollama:
                # Ollama 사용
                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    images=[image_path],
                    stream=False
                )
                return response['response']
            elif ChatOllama:
                # LangChain Ollama 사용 (이미지 지원 제한적)
                return f"이미지 분석 기능을 사용하려면 ollama 패키지가 필요합니다. 현재는 기본 설명만 제공: {Path(image_path).name} 이미지 파일"
            else:
                return f"이미지 분석 도구를 사용할 수 없습니다. ollama 또는 적절한 vision 모델이 필요합니다."
                
        except Exception as e:
            self.logger.error(f"이미지 분석 오류: {str(e)}")
            return f"이미지 분석 중 오류가 발생했습니다: {str(e)}"
    
    def _analyze_with_openai(self, image_path: str, prompt: str) -> str:
        """OpenAI Vision API를 사용한 이미지 분석"""
        try:
            # 이미지를 base64로 인코딩
            base64_image = self._encode_image_to_base64(image_path)
            
            # OpenAI Vision API 호출
            response = self.openai_client.chat.completions.create(
                model=self.model_name,  # gpt-4-vision-preview 또는 gpt-4o
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI Vision API 오류: {str(e)}")
            return f"OpenAI Vision API 분석 중 오류가 발생했습니다: {str(e)}"
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        try:
            if not Image:
                raise ImportError("PIL (Pillow) 라이브러리가 필요합니다")
            
            # PIL로 이미지 열기 및 최적화
            with Image.open(image_path) as img:
                # 이미지 크기 조정 (OpenAI API 제한에 맞춤)
                max_size = (2048, 2048)  # OpenAI의 권장 최대 크기
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # RGB로 변환 (RGBA나 다른 모드 처리)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # JPEG 형태로 압축하여 base64 인코딩
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                buffer.seek(0)
                
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"이미지 인코딩 오류: {str(e)}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> str:
        """OCR을 통한 이미지에서 텍스트 추출"""
        # 파일 존재 확인
        from pathlib import Path
        if not Path(image_path).exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            
        try:
            if self.provider == "openai" and self.openai_client:
                # OpenAI Vision API로 텍스트 추출
                ocr_prompt = """이 이미지에서 텍스트를 정확히 추출해주세요. 
                모든 텍스트를 읽어서 그대로 출력해주세요. 
                텍스트가 없다면 '텍스트 없음'이라고 응답해주세요."""
                return self._analyze_with_openai(image_path, ocr_prompt)
            elif pytesseract and Image:
                # Tesseract OCR 사용
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, lang='kor+eng')
                return text.strip()
            else:
                self.logger.warning("OCR 기능을 사용하려면 pytesseract와 Pillow가 필요합니다.")
                return f"OCR 도구를 사용할 수 없습니다. pytesseract와 Pillow 설치가 필요합니다."
                
        except Exception as e:
            self.logger.error(f"OCR 처리 오류: {str(e)}")
            return f"텍스트 추출 중 오류가 발생했습니다: {str(e)}"
    
    def batch_analyze(self, image_paths: List[str]) -> List[str]:
        """여러 이미지 배치 분석"""
        results = []
        for path in image_paths:
            result = self.analyze_image(path)
            results.append(result)
        return results