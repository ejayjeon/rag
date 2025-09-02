# Test Data Directory

이 디렉토리는 multimodal RAG 시스템 테스트를 위한 샘플 데이터를 포함합니다.

## 디렉토리 구조

```
test_data/
├── pdf/          # PDF 파일 테스트용
├── images/       # 이미지 파일 테스트용  
├── text/         # 텍스트 파일 테스트용
│   ├── sample_document.txt
│   ├── ai_article.txt
│   └── web_development.txt
└── README.md
```

## 사용법

### 텍스트 파일
- `sample_document.txt`: Python 프로그래밍 언어에 대한 기본 정보
- `ai_article.txt`: 인공지능 기술의 현재와 미래에 대한 설명
- `web_development.txt`: 웹 개발 기술 스택과 트렌드 정보

### PDF 파일
PDF 샘플 파일을 추가하여 PDF 처리 기능을 테스트할 수 있습니다.

### 이미지 파일
이미지 분석 및 OCR 기능 테스트를 위한 샘플 이미지를 추가할 수 있습니다.

## 테스트 방법

```python
from src import MultimodalRAG

# RAG 시스템 초기화
rag = MultimodalRAG()

# 텍스트 문서 추가
rag.add_text_document("test_data/text/sample_document.txt")

# 검색 테스트
result = rag.search("Python의 특징은 무엇인가요?")
print(result.answer)
```

## 추가 테스트 데이터

실제 테스트를 위해 다음과 같은 파일들을 추가할 수 있습니다:

1. **PDF 파일**: 기술 문서, 논문, 보고서
2. **이미지 파일**: 차트, 그래프, 텍스트가 포함된 이미지
3. **다양한 형식의 텍스트 파일**: 마크다운, JSON 등