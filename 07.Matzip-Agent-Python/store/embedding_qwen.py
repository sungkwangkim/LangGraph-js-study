"""
MySQL 데이터를 ChromaDB로 임베딩하는 스크립트
"""

import pymysql
import os
from typing import Dict, List

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

# .env 파일 로드
load_dotenv()

# ==================== 설정 ====================
# 임베딩 모델 선택
EMBEDDING_TYPE = os.getenv('EMBEDDING_TYPE', 'openai')  # 'openai' 또는 'huggingface'

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if EMBEDDING_TYPE == 'openai' and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다")

# HuggingFace 모델 설정 (기본값은 공개로 쉽게 받는 bge-m3)
HUGGINGFACE_MODEL = os.getenv('HUGGINGFACE_MODEL', 'BAAI/bge-m3')
HUGGINGFACE_DEVICE = os.getenv('HUGGINGFACE_DEVICE', 'cpu')  # 'cpu' 또는 'cuda'
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')  # 비공개 모델 사용 시 설정

# MySQL 연결 정보
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# MySQL 필수 설정 확인
if not MYSQL_CONFIG['password']:
    raise ValueError("MYSQL_PASSWORD가 .env 파일에 설정되지 않았습니다")
if not MYSQL_CONFIG['database']:
    raise ValueError("MYSQL_DATABASE가 .env 파일에 설정되지 않았습니다")

# ChromaDB 설정
CHROMA_DB_PATH = "./chroma_db_qwen"  # ChromaDB 저장 경로
COLLECTION_NAME = "jamsil_restaurants_qwen"  # 컬렉션명

# 임베딩 모델 설정 (OpenAI)
EMBEDDING_MODEL = "text-embedding-3-small"  # 또는 "text-embedding-3-large"


# ==================== 함수 정의 ====================

def get_mysql_connection():
    """MySQL 연결 생성"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        print("✅ MySQL 연결 성공")
        return connection
    except Exception as e:
        print(f"❌ MySQL 연결 실패: {e}")
        raise


def fetch_restaurants_data(connection) -> List[Dict]:
    """
    MySQL에서 음식점 데이터 조회
    restaurants, menus, weather_tags를 조인하여 가져옴
    """
    query = """
        SELECT
            r.id,
            r.name,
            r.category,
            r.signature_menu,
            r.description,
            r.naver_review_count,
            r.phone,
            r.latitude,
            r.longitude,
            r.location_type,
            r.naver_id,
            r.homepage_url,
            r.main_thumbnail_url,
            GROUP_CONCAT(DISTINCT m.menu_name, ':', m.price ORDER BY m.price SEPARATOR ' | ') AS menus,
            GROUP_CONCAT(DISTINCT wt.tag_name SEPARATOR ', ') AS weather_tags
        FROM restaurants r
        LEFT JOIN menus m ON r.id = m.restaurant_id 
            AND m.price >= 7000 
            AND m.price <= 20000
        LEFT JOIN restaurant_weather_tags rwt ON r.id = rwt.restaurant_id
        LEFT JOIN weather_tags wt ON rwt.weather_tag_id = wt.id
        GROUP BY r.id
        ORDER BY r.id
    """
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"✅ {len(results)}개의 음식점 데이터 조회 완료")
            return results
    except Exception as e:
        print(f"❌ 데이터 조회 실패: {e}")
        raise


def create_markdown_document(restaurant: Dict) -> str:
    """
    음식점 데이터를 Markdown 형식으로 변환
    """
    # 메뉴 정보 파싱
    menus_text = ""
    if restaurant['menus']:
        menu_list = restaurant['menus'].split(' | ')
        menus_text = "\n".join([f"  - {menu}" for menu in menu_list])
    
    # Markdown 생성
    markdown = f"""# {restaurant['name']}

## 기본 정보
- **카테고리**: {restaurant['category']}
- **대표메뉴**: {restaurant['signature_menu'] or '정보 없음'}
- **위치 타입**: {restaurant['location_type'] or '일반 음식점'}
- **전화번호**: {restaurant['phone'] or '정보 없음'}
- **네이버 리뷰수**: {restaurant['naver_review_count']}

## 메뉴
{menus_text if menus_text else '  - 메뉴 정보 없음'}

## 설명
{restaurant['description'] or '설명 없음'}

## 날씨 태그
{restaurant['weather_tags'] or '태그 없음'}

## 위치 정보
- 위도: {restaurant['latitude']}
- 경도: {restaurant['longitude']}
"""
    
    return markdown.strip()


def create_optimized_embedding_text(restaurant: Dict) -> str:
    """검색 최적화된 텍스트 생성"""
    
    # 핵심 정보를 반복하여 가중치 부여
    core_info = f"{restaurant['name']} {restaurant['category']}"
    
    # 메뉴 정보 강조
    menus_text = ""
    if restaurant.get("menus"):
        menu_list = restaurant["menus"].split(" | ")
        menus_text = "\n".join(f"  - {menu}" for menu in menu_list)
    
    # 시그니처 메뉴 강조
    signature = restaurant.get('signature_menu', '')
    signature_emphasized = f"{signature} {signature} {signature}" if signature else ""
    
    
    # 최적화된 순서로 조합
    optimized_text = f"""
# {core_info}
{signature_emphasized}

## 메뉴
{menus_text}


{restaurant.get('description', '')}
위치: {restaurant.get('location_type', '')}
날씨태그: {restaurant.get('weather_tags', '')}
    """.strip()
    
    return optimized_text

def convert_to_langchain_documents(restaurants: List[Dict]) -> List[Document]:
    """
    MySQL 데이터를 LangChain Document 객체로 변환
    """
    documents = []
    
    for restaurant in restaurants:
        # Markdown 텍스트 생성
        content = create_optimized_embedding_text(restaurant)
        
        # 메타데이터 준비
        metadata = {
            'restaurant_id': restaurant['id'],
            'name': restaurant['name'],
            'category': restaurant['category'],
            'location_type': restaurant['location_type'] or '',
            'latitude': float(restaurant['latitude']),
            'longitude': float(restaurant['longitude']),
            'main_thumbnail_url': restaurant['main_thumbnail_url'] or '',
            'homepage_url': restaurant['homepage_url'] or '',
            'naver_review_count': restaurant['naver_review_count'],
            'naver_id': restaurant['naver_id'] or '',
            'phone': restaurant['phone'] or '',
            'signature_menu': restaurant['signature_menu'] or '',
            'weather_tags': restaurant['weather_tags'] or ''
        }
        
        # Document 객체 생성
        doc = Document(
            page_content=content,
            metadata=metadata
        )
        documents.append(doc)
    
    print(f"✅ {len(documents)}개의 Document 객체 생성 완료")
    return documents


def create_chromadb_vectorstore(documents: List[Document]):
    """
    ChromaDB에 임베딩하여 저장 (OpenAI 또는 HuggingFace 선택 가능)
    """
    try:
        # 임베딩 모델 선택
        if EMBEDDING_TYPE == 'openai':
            print(f"📦 OpenAI 임베딩 모델 초기화: {EMBEDDING_MODEL}")
            embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY
            )
            print(f"   총 {len(documents)}개 문서 처리 예상 시간: 약 {len(documents) * 0.5}초")
            
        elif EMBEDDING_TYPE == 'huggingface':
            print(f"📦 HuggingFace 임베딩 모델 초기화: {HUGGINGFACE_MODEL}")
            print(f"   디바이스: {HUGGINGFACE_DEVICE}")
            print("   ⚠️  모델이 로컬에 없으면 다운로드가 필요합니다 (토큰/네트워크 확인).")

            embeddings = HuggingFaceEmbeddings(
                model_name=HUGGINGFACE_MODEL,
                model_kwargs={
                    "device": HUGGINGFACE_DEVICE,
                    "trust_remote_code": True,
                    "token": HUGGINGFACE_TOKEN,
                },
                encode_kwargs={
                    "normalize_embeddings": True,
                    "batch_size": 8,
                },
            )
            print(f"   총 {len(documents)}개 문서 처리 중...")
        else:
            raise ValueError(f"지원하지 않는 EMBEDDING_TYPE: {EMBEDDING_TYPE}")
        
        # ChromaDB 디렉토리 생성
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        
        # ChromaDB에 저장
        print(f"💾 ChromaDB에 임베딩 중...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=CHROMA_DB_PATH
        )
        
        print(f"✅ ChromaDB 저장 완료: {CHROMA_DB_PATH}")
        print(f"   임베딩 모델: {EMBEDDING_TYPE}")
        print(f"   컬렉션명: {COLLECTION_NAME}")
        return vectorstore
        
    except Exception as e:
        print(f"❌ ChromaDB 생성 실패: {e}")
        raise


def test_search(vectorstore, query: str = "냉면"):
    """
    임베딩 결과 테스트 검색
    """
    print(f"\n🔍 테스트 검색: '{query}'")
    results = vectorstore.similarity_search(query, k=3)
    
    print(f"검색 결과 {len(results)}개:")
    for i, doc in enumerate(results, 1):
        print(f"\n--- 결과 {i} ---")
        print(f"이름: {doc.metadata['name']}")
        print(f"카테고리: {doc.metadata['category']}")
        print(f"대표메뉴: {doc.metadata['signature_menu']}")
        print(f"위치: {doc.metadata['location_type']}")
        print(f"리뷰수: {doc.metadata['naver_review_count']}")


# ==================== 메인 실행 ====================

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("MySQL → ChromaDB 임베딩 시작")
    print("=" * 60)
    
    connection = None
    try:
        # 1. MySQL 연결
        connection = get_mysql_connection()
        
        # 2. 데이터 조회
        restaurants = fetch_restaurants_data(connection)
        
        if not restaurants:
            print("⚠️  조회된 데이터가 없습니다.")
            return
        
        # 3. LangChain Document 변환
        documents = convert_to_langchain_documents(restaurants)
        
        # 4. ChromaDB에 임베딩 및 저장
        vectorstore = create_chromadb_vectorstore(documents)
        
        # 5. 테스트 검색
        test_search(vectorstore, "회덮밥 맛집")
        test_search(vectorstore, "순대국 맛집")
        
        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # MySQL 연결 종료
        if connection:
            connection.close()
            print("MySQL 연결 종료")


if __name__ == "__main__":
    main()
