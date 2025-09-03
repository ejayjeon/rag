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
import time
import os
from pathlib import Path

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
        
        # 파일 관리 정보
        self.processed_files = {}  # {file_id: file_info}
        self.file_hashes = {}      # {file_path: content_hash}
        
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
    
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None, include_file_info: bool = True) -> dict:
        """이미지 분석 (파일 정보 포함)"""
        # 파일 존재 확인
        if not Path(image_path).exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        # 확장자 검증
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"지원하지 않는 이미지 형식입니다. 지원 형식: {valid_extensions}")
        
        # 파일 정보 생성
        file_info = self.get_file_info(image_path)
        
        default_prompt = """이 이미지를 자세히 분석해주세요:
        1. 주요 객체나 요소들
        2. 텍스트가 있다면 내용
        3. 차트나 그래프가 있다면 설명
        4. 전체적인 내용이나 맥락
        
        한국어로 상세하게 설명해주세요."""
        
        prompt = custom_prompt or default_prompt
        
        try:
            analysis_result = ""
            if self.provider == "openai" and self.openai_client:
                # OpenAI Vision API 사용
                analysis_result = self._analyze_with_openai(image_path, prompt)
            elif self.provider == "ollama" and ollama:
                # Ollama 사용
                response = ollama.generate(
                    model=self.model_name,
                    prompt=prompt,
                    images=[image_path],
                    stream=False
                )
                analysis_result = response['response']
            elif ChatOllama:
                # LangChain Ollama 사용 (이미지 지원 제한적)
                analysis_result = f"이미지 분석 기능을 사용하려면 ollama 패키지가 필요합니다. 현재는 기본 설명만 제공: {Path(image_path).name} 이미지 파일"
            else:
                analysis_result = f"이미지 분석 도구를 사용할 수 없습니다. ollama 또는 적절한 vision 모델이 필요합니다."
            
            # 결과 반환
            result = {
                'analysis': analysis_result,
                'file_info': file_info,
                'success': True
            }
            
            if include_file_info:
                result.update({
                    'file_id': file_info['file_id'],
                    'content_hash': file_info['content_hash'],
                    'analysis_timestamp': int(time.time() * 1000)
                })
            
            return result
                
        except Exception as e:
            self.logger.error(f"이미지 분석 오류: {str(e)}")
            error_result = {
                'analysis': f"이미지 분석 중 오류가 발생했습니다: {str(e)}",
                'file_info': file_info,
                'success': False,
                'error': str(e)
            }
            
            if include_file_info:
                error_result.update({
                    'file_id': file_info['file_id'],
                    'content_hash': file_info['content_hash']
                })
            
            return error_result
    
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
    
    def extract_text_from_image(self, image_path: str, include_file_info: bool = True) -> dict:
        """OCR을 통한 이미지에서 텍스트 추출 (파일 정보 포함)"""
        # 파일 존재 확인
        if not Path(image_path).exists():
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        
        # 파일 정보 생성
        file_info = self.get_file_info(image_path)
        
        try:
            extracted_text = ""
            if self.provider == "openai" and self.openai_client:
                # OpenAI Vision API로 텍스트 추출
                ocr_prompt = """이 이미지에서 텍스트를 정확히 추출해주세요. 
                모든 텍스트를 읽어서 그대로 출력해주세요. 
                텍스트가 없다면 '텍스트 없음'이라고 응답해주세요."""
                extracted_text = self._analyze_with_openai(image_path, ocr_prompt)
            elif pytesseract and Image:
                # Tesseract OCR 사용
                image = Image.open(image_path)
                extracted_text = pytesseract.image_to_string(image, lang='kor+eng')
                extracted_text = extracted_text.strip()
            else:
                self.logger.warning("OCR 기능을 사용하려면 pytesseract와 Pillow가 필요합니다.")
                extracted_text = f"OCR 도구를 사용할 수 없습니다. pytesseract와 Pillow 설치가 필요합니다."
            
            # 결과 반환
            result = {
                'extracted_text': extracted_text,
                'file_info': file_info,
                'success': True
            }
            
            if include_file_info:
                result.update({
                    'file_id': file_info['file_id'],
                    'content_hash': file_info['content_hash'],
                    'ocr_timestamp': int(time.time() * 1000)
                })
            
            return result
                
        except Exception as e:
            self.logger.error(f"OCR 처리 오류: {str(e)}")
            error_result = {
                'extracted_text': f"텍스트 추출 중 오류가 발생했습니다: {str(e)}",
                'file_info': file_info,
                'success': False,
                'error': str(e)
            }
            
            if include_file_info:
                error_result.update({
                    'file_id': file_info['file_id'],
                    'content_hash': file_info['content_hash']
                })
            
            return error_result
    
    def batch_analyze(self, image_paths: List[str], include_file_info: bool = True) -> List[dict]:
        """여러 이미지 배치 분석 (파일 정보 포함)"""
        results = []
        for path in image_paths:
            result = self.analyze_image(path, include_file_info=include_file_info)
            results.append(result)
        return results
    
    def get_file_info(self, file_path: str) -> dict:
        """파일 정보 반환 (ID, 해시, 메타데이터 포함)"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        # 파일 ID 생성
        file_id = self.generate_file_id(file_path)
        
        # 파일 메타데이터
        file_stat = os.stat(file_path)
        file_info = {
            'file_id': file_id,
            'name': Path(file_path).name,
            'path': file_path,
            'size': file_stat.st_size,
            'type': Path(file_path).suffix.lower(),
            'content_hash': self.file_hashes.get(file_path),
            'upload_timestamp': int(file_stat.st_mtime * 1000),
            'processed': True
        }
        
        # 처리된 파일 목록에 저장
        self.processed_files[file_id] = file_info
        
        return file_info
    
    def generate_file_id(self, file_path: str, file_content: bytes = None) -> str:
        """파일의 고유 ID 생성"""
        import hashlib
        
        if file_content is None:
            # 파일에서 직접 읽기
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                self.logger.error(f"파일 읽기 오류: {str(e)}")
                # 파일명과 시간으로 대체
                return f"{Path(file_path).name}_{int(time.time() * 1000)}"
        
        # MD5 해시 생성
        content_hash = hashlib.md5(file_content).hexdigest()[:12]
        timestamp = int(time.time() * 1000)
        filename = Path(file_path).name
        
        file_id = f"{filename}_{content_hash}_{timestamp}"
        
        # 해시 저장
        self.file_hashes[file_path] = content_hash
        
        return file_id
    
    def analyze_multiple_images_in_context(self, image_paths: List[str], context_prompt: str = None, include_file_info: bool = True) -> dict:
        """컨텍스트를 고려한 다중 이미지 순차 분석"""
        if not image_paths:
            return {
                'success': False,
                'error': '분석할 이미지가 없습니다.',
                'results': []
            }
        
        # 컨텍스트 프롬프트 설정
        if not context_prompt:
            context_prompt = """여러 이미지를 순차적으로 분석해주세요.
            각 이미지마다:
            1. 주요 객체나 요소들
            2. 텍스트가 있다면 내용
            3. 차트나 그래프가 있다면 설명
            4. 전체적인 내용이나 맥락
            
            그리고 모든 이미지 간의 연관성이나 공통점도 분석해주세요.
            한국어로 상세하게 설명해주세요."""
        
        try:
            all_results = []
            combined_analysis = ""
            
            # 각 이미지 개별 분석
            for i, image_path in enumerate(image_paths):
                # 개별 이미지 분석
                individual_result = self.analyze_image(image_path, include_file_info=include_file_info)
                
                if individual_result['success']:
                    all_results.append(individual_result)
                    
                    # 개별 분석 결과 추가
                    combined_analysis += f"\n\n--- 이미지 {i+1} 분석 결과 ---\n"
                    combined_analysis += f"파일: {individual_result['file_info']['name']}\n"
                    combined_analysis += individual_result['analysis']
                else:
                    # 오류가 있는 경우
                    all_results.append(individual_result)
                    combined_analysis += f"\n\n--- 이미지 {i+1} 분석 실패 ---\n"
                    combined_analysis += f"오류: {individual_result.get('error', '알 수 없는 오류')}"
            
            # 전체 결과 반환
            return {
                'success': True,
                'combined_analysis': combined_analysis,
                'individual_results': all_results,
                'total_images': len(image_paths),
                'successful_analyses': len([r for r in all_results if r['success']]),
                'context_prompt': context_prompt
            }
            
        except Exception as e:
            self.logger.error(f"다중 이미지 컨텍스트 분석 오류: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def update_image_context(self, new_image_path: str, existing_context: dict = None) -> dict:
        """기존 컨텍스트에 새 이미지 추가하여 분석 업데이트"""
        try:
            # 새 이미지 분석
            new_image_result = self.analyze_image(new_image_path, include_file_info=True)
            
            if not new_image_result['success']:
                return {
                    'success': False,
                    'error': f'새 이미지 분석 실패: {new_image_result.get("error", "알 수 없는 오류")}',
                    'existing_context': existing_context
                }
            
            # 기존 컨텍스트가 있으면 업데이트
            if existing_context and 'individual_results' in existing_context:
                updated_context = existing_context.copy()
                updated_context['individual_results'].append(new_image_result)
                updated_context['total_images'] += 1
                updated_context['successful_analyses'] += 1
                
                # 통합 분석 결과 업데이트
                if 'combined_analysis' in updated_context:
                    updated_context['combined_analysis'] += f"\n\n--- 새로 추가된 이미지 ---\n"
                    updated_context['combined_analysis'] += f"파일: {new_image_result['file_info']['name']}\n"
                    updated_context['combined_analysis'] += new_image_result['analysis']
                
                return {
                    'success': True,
                    'updated_context': updated_context,
                    'new_image_result': new_image_result,
                    'message': '기존 컨텍스트에 새 이미지가 추가되었습니다.'
                }
            else:
                # 기존 컨텍스트가 없으면 새로 생성
                return self.analyze_multiple_images_in_context([new_image_path])
                
        except Exception as e:
            self.logger.error(f"이미지 컨텍스트 업데이트 오류: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'existing_context': existing_context
            }
    
    def is_duplicate_file(self, file_path: str, other_file_path: str) -> bool:
        """두 파일이 동일한지 해시로 확인"""
        if file_path not in self.file_hashes or other_file_path not in self.file_hashes:
            return False
        
        return self.file_hashes[file_path] == self.file_hashes[other_file_path]
    
    def get_processed_files_summary(self) -> dict:
        """처리된 파일들의 요약 정보 반환"""
        summary = {
            'total_files': len(self.processed_files),
            'file_types': {},
            'total_size': 0,
            'files': []
        }
        
        for file_id, file_info in self.processed_files.items():
            file_type = file_info['type']
            if file_type not in summary['file_types']:
                summary['file_types'][file_type] = 0
            summary['file_types'][file_type] += 1
            summary['total_size'] += file_info['size']
            summary['files'].append(file_info)
        
        return summary
    
    def get_current_image_context(self) -> dict:
        """현재 처리된 이미지들의 컨텍스트 정보 반환"""
        return {
            'total_files': len(self.processed_files),
            'image_files': [info for info in self.processed_files.values() if info['type'] in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']],
            'file_hashes': self.file_hashes,
            'context_summary': self.get_processed_files_summary()
        }
    
    def clear_image_context(self) -> None:
        """이미지 컨텍스트 초기화"""
        self.processed_files.clear()
        self.file_hashes.clear()
        self.logger.info("이미지 컨텍스트가 초기화되었습니다.")
    
    def remove_image_from_context(self, file_path: str) -> bool:
        """특정 이미지를 컨텍스트에서 제거"""
        try:
            # 파일 ID로 찾기
            file_id_to_remove = None
            for file_id, file_info in self.processed_files.items():
                if file_info.get('path') == file_path:
                    file_id_to_remove = file_id
                    break
            
            if file_id_to_remove:
                # 처리된 파일 목록에서 제거
                removed_file = self.processed_files.pop(file_id_to_remove)
                
                # 해시에서도 제거
                if file_path in self.file_hashes:
                    self.file_hashes.pop(file_path)
                
                self.logger.info(f"이미지가 컨텍스트에서 제거되었습니다: {removed_file['name']}")
                return True
            else:
                self.logger.warning(f"컨텍스트에서 찾을 수 없는 이미지: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"이미지 컨텍스트 제거 오류: {str(e)}")
            return False
    
    def get_image_analysis_history(self) -> List[dict]:
        """이미지 분석 히스토리 반환"""
        history = []
        for file_id, file_info in self.processed_files.items():
            if file_info['type'] in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                history.append({
                    'file_id': file_id,
                    'name': file_info['name'],
                    'path': file_info.get('path', ''),
                    'content_hash': file_info.get('content_hash', ''),
                    'upload_timestamp': file_info.get('upload_timestamp', 0),
                    'size': file_info.get('size', 0)
                })
        
        # 시간순 정렬
        history.sort(key=lambda x: x.get('upload_timestamp', 0), reverse=True)
        return history
