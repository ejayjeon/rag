"""
메인 실행 파일
"""
import argparse
from pathlib import Path
from src.rag_system import SimpleRAG


def main():
    parser = argparse.ArgumentParser(description='Simple RAG System')
    parser.add_argument(
        '--docs', 
        nargs='+', 
        required=True,
        help='문서 파일 경로들'
    )
    parser.add_argument(
        '--model', 
        choices=['openai', 'ollama'],
        default='openai',
        help='사용할 LLM 모델'
    )
    
    args = parser.parse_args()
    
    # RAG 시스템 초기화
    rag = SimpleRAG()
    
    # 문서 로드 및 벡터 저장소 생성
    print("문서를 로드하고 있습니다...")
    documents = rag.load_documents(args.docs)
    print(f"총 {len(documents)}개의 문서 청크를 로드했습니다.")
    
    print("벡터 저장소를 생성하고 있습니다...")
    rag.create_vectorstore(documents)
    print("벡터 저장소 생성 완료!")
    
    # QA 체인 설정
    print(f"{args.model} 모델로 QA 시스템을 초기화하고 있습니다...")
    rag.setup_qa_chain(args.model)
    print("QA 시스템 준비 완료!")
    
    # 대화형 질문
    print("\n🤖 RAG 시스템이 준비되었습니다!")
    print("질문을 입력하세요. 종료하려면 'quit'를 입력하세요.\n")
    
    while True:
        question = input("❓ 질문: ").strip()
        
        if question.lower() in ['quit', 'exit', '종료']:
            print("👋 RAG 시스템을 종료합니다.")
            break
            
        if not question:
            continue
            
        try:
            result = rag.ask_question(question)
            print(f"🤖 답변: {result['answer']}\n")
            
            # 소스 문서 정보 표시 (옵션)
            if result['source_documents']:
                print("📚 참조 문서:")
                for i, doc in enumerate(result['source_documents'][:2]):
                    source = doc.metadata.get('source', 'Unknown')
                    print(f"  {i+1}. {Path(source).name}")
                print()
                
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}\n")


if __name__ == "__main__":
    main()