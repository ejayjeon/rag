#!/usr/bin/env python3
"""
Multimodal RAG 시스템 사용 예제

이 스크립트는 multimodal RAG 시스템의 다양한 기능을 시연합니다.
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src import MultimodalRAG, setup_logging


def main():
    """메인 실행 함수"""
    
    # 로깅 설정
    logger = setup_logging(level=logging.INFO)
    logger.info("=== Multimodal RAG 시스템 예제 시작 ===")
    
    try:
        # RAG 시스템 초기화
        logger.info("RAG 시스템 초기화 중...")
        rag = MultimodalRAG(
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
            llm_model="llama3.2:1b"  # 가벼운 모델 사용
        )
        logger.info("RAG 시스템 초기화 완료")
        
        # 테스트 데이터 디렉토리 설정
        test_data_dir = project_root / "test_data"
        text_dir = test_data_dir / "text"
        
        # 1. 텍스트 문서 추가
        logger.info("\n=== 1. 텍스트 문서 추가 ===")
        text_files = list(text_dir.glob("*.txt"))
        
        if text_files:
            for text_file in text_files:
                logger.info(f"텍스트 문서 추가: {text_file.name}")
                rag.add_text_document(str(text_file))
            logger.info(f"총 {len(text_files)}개의 텍스트 문서 추가 완료")
        else:
            logger.warning("텍스트 파일을 찾을 수 없습니다.")
        
        # 2. 검색 및 질답 테스트
        logger.info("\n=== 2. 검색 및 질답 테스트 ===")
        
        test_queries = [
            "Python의 주요 특징은 무엇인가요?",
            "인공지능의 발전 단계를 설명해주세요.",
            "웹 개발에서 사용되는 프론트엔드 기술은?",
            "머신러닝과 딥러닝의 차이점은?",
            "React.js의 특징을 알려주세요."
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- 질문 {i}: {query} ---")
            
            try:
                result = rag.search(query)
                
                print(f"\n질문: {query}")
                print(f"답변: {result.answer}")
                print(f"신뢰도: {result.confidence:.2f}")
                print(f"참조 문서 수: {len(result.sources)}")
                
                if result.sources:
                    print("참조 문서:")
                    for j, source in enumerate(result.sources[:2], 1):
                        source_name = source.metadata.get('source', 'Unknown')
                        content_preview = source.page_content[:100] + "..."
                        print(f"  {j}. {source_name}: {content_preview}")
                
                print("-" * 60)
                
            except Exception as e:
                logger.error(f"검색 중 오류 발생: {e}")
        
        # 3. 배치 문서 추가 테스트 (PDF나 이미지 파일이 있는 경우)
        logger.info("\n=== 3. 배치 문서 추가 테스트 ===")
        
        # PDF 파일 확인
        pdf_dir = test_data_dir / "pdf"
        pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
        
        # 이미지 파일 확인
        images_dir = test_data_dir / "images"
        image_files = []
        if images_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif']:
                image_files.extend(images_dir.glob(ext))
        
        all_test_files = [str(f) for f in text_files + pdf_files + image_files]
        
        if len(all_test_files) > len(text_files):
            logger.info("추가 문서 유형이 발견되어 배치 추가를 시도합니다...")
            try:
                rag.add_documents(all_test_files)
                logger.info("배치 문서 추가 완료")
            except Exception as e:
                logger.error(f"배치 문서 추가 중 오류: {e}")
        
        # 4. 시스템 정보 출력
        logger.info("\n=== 4. 시스템 정보 ===")
        print(f"처리된 총 문서 수: {len(all_test_files)}")
        print(f"- 텍스트 파일: {len(text_files)}")
        print(f"- PDF 파일: {len(pdf_files)}")
        print(f"- 이미지 파일: {len(image_files)}")
        
        logger.info("=== Multimodal RAG 시스템 예제 완료 ===")
        
    except Exception as e:
        logger.error(f"예제 실행 중 오류 발생: {e}", exc_info=True)
        return 1
    
    return 0


def demo_individual_processors():
    """개별 프로세서 데모"""
    logger = setup_logging(level=logging.INFO)
    logger.info("\n=== 개별 프로세서 데모 ===")
    
    try:
        from src.pdf_processor import PDFProcessor
        from src.image_analyzer import ImageAnalyzer
        
        # PDF 프로세서 테스트
        logger.info("PDF 프로세서 테스트...")
        pdf_processor = PDFProcessor()
        logger.info("PDF 프로세서 초기화 완료")
        
        # 이미지 분석기 테스트
        logger.info("이미지 분석기 테스트...")
        image_analyzer = ImageAnalyzer()
        logger.info("이미지 분석기 초기화 완료")
        
        logger.info("개별 프로세서 데모 완료")
        
    except Exception as e:
        logger.error(f"개별 프로세서 데모 중 오류: {e}")


if __name__ == "__main__":
    print("Multimodal RAG 시스템 예제")
    print("=" * 50)
    
    # 메인 예제 실행
    exit_code = main()
    
    print("\n" + "=" * 50)
    print("추가 데모를 실행하시겠습니까? (개별 프로세서 테스트)")
    response = input("y/N: ").strip().lower()
    
    if response in ['y', 'yes']:
        demo_individual_processors()
    
    print("\n프로그램을 종료합니다.")
    sys.exit(exit_code)