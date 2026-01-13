"""
MySQL 데이터를 Markdown으로 만들어 Pinecone에 임베딩하는 스크립트.
블로그 로더 대신 DB에서 불러온 레스토랑 데이터를 사용합니다.
"""

import os
import time
from typing import Dict, List

import pymysql
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# ==================== 설정 ====================
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
if not UPSTAGE_API_KEY:
    raise ValueError("UPSTAGE_API_KEY가 .env 파일에 설정되지 않았습니다")

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

if not MYSQL_CONFIG["password"]:
    raise ValueError("MYSQL_PASSWORD가 .env 파일에 설정되지 않았습니다")
if not MYSQL_CONFIG["database"]:
    raise ValueError("MYSQL_DATABASE가 .env 파일에 설정되지 않았습니다")

EMBEDDING_MODEL = "solar-embedding-1-large"
EMBEDDING_DIMENSION = 4096  # solar-embedding-1-large 출력 차원

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY가 .env 파일에 설정되지 않았습니다")

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "jamsil-restaurants-upstage")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "public")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")


# ==================== 함수 정의 ====================
def get_mysql_connection() -> pymysql.connections.Connection:
    """MySQL 연결 생성"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        print("✅ MySQL 연결 성공")
        return connection
    except Exception as exc:
        print(f"❌ MySQL 연결 실패: {exc}")
        raise


def fetch_restaurants_data(connection: pymysql.connections.Connection) -> List[Dict]:
    """음식점과 메뉴/날씨 태그를 조인하여 조회"""
    query = """
        SELECT
            r.id,
            r.name,
            r.category,
            r.description,
            r.naver_place_review_count as naver_review_count,
            r.phone,
            r.latitude,
            r.longitude,
            r.location_type,
            r.naver_id,
            r.homepage_url,
            r.main_thumbnail_url,
            GROUP_CONCAT(DISTINCT m.menu_name, ':', m.price ORDER BY m.price SEPARATOR ' | ') AS menus
        FROM restaurants r
        LEFT JOIN menus m ON r.id = m.restaurant_id 
            AND m.price >= 5900 
            AND m.price <= 20000
        GROUP BY r.id
        ORDER BY r.id
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"✅ {len(results)}개의 음식점 데이터 조회 완료")
            return results
    except Exception as exc:
        print(f"❌ 데이터 조회 실패: {exc}")
        raise



def create_optimized_embedding_text(restaurant: Dict) -> str:
    """검색 최적화된 텍스트 생성"""
    
    # 핵심 정보를 반복하여 가중치 부여
    core_info = f"{restaurant['name']} {restaurant['category']}"
    
    # 메뉴 정보 강조
    menus_text = ""
    if restaurant.get("menus"):
        menu_list = restaurant["menus"].split(" | ")
        menus_text = "\n".join(f"  - {menu}" for menu in menu_list)
    
    
    # 최적화된 순서로 조합
    optimized_text = f"""
# {core_info}

## 메뉴
{menus_text}

## 네이버 리뷰수: {restaurant.get('naver_review_count', '')}

## 특징:
{restaurant.get('description', '')}


## 위치: {restaurant.get('location_type', '')}

## metadata
- naver_id: {restaurant.get('naver_id', '')}
- homepage_url: {restaurant.get('homepage_url', '')}
- main_thumbnail_url: {restaurant.get('main_thumbnail_url', '')}

    """.strip()
    
    return optimized_text



def convert_to_langchain_documents(restaurants: List[Dict]) -> List[Document]:
    """MySQL 데이터를 LangChain Document 객체로 변환"""
    documents: List[Document] = []

    for restaurant in restaurants:
        content = create_optimized_embedding_text(restaurant)
        metadata = {
            "restaurant_id": restaurant["id"],
            "name": restaurant["name"],
            "category": restaurant["category"],
            "location_type": restaurant.get("location_type") or "",
            "latitude": float(restaurant["latitude"]),
            "longitude": float(restaurant["longitude"]),
            "main_thumbnail_url": restaurant.get("main_thumbnail_url") or "",
            "homepage_url": restaurant.get("homepage_url") or "",
            "naver_review_count": restaurant["naver_review_count"],
            "naver_id": restaurant.get("naver_id") or "",
            "phone": restaurant.get("phone") or ""
        }
        documents.append(Document(page_content=content, metadata=metadata))

    print(f"✅ {len(documents)}개의 Document 객체 생성 완료")
    return documents


def ensure_pinecone_index(pc: Pinecone) -> None:
    """필요 시 Pinecone 인덱스를 생성"""
    existing_indexes = set(pc.list_indexes().names())
    if PINECONE_INDEX_NAME in existing_indexes:
        print(f"ℹ️  기존 Pinecone 인덱스 사용: {PINECONE_INDEX_NAME}")
        return

    print(f"🆕 Pinecone 인덱스 생성: {PINECONE_INDEX_NAME}")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
    )

    print("⌛ 인덱스 준비 대기 중...")
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)
    print("✅ 인덱스 준비 완료")


def create_pinecone_vectorstore(documents: List[Document]) -> PineconeVectorStore:
    """Upstage 임베딩으로 Pinecone에 저장"""
    try:
        print(f"📦 Upstage 임베딩 모델 초기화: {EMBEDDING_MODEL}")
        embeddings = UpstageEmbeddings(model=EMBEDDING_MODEL)

        pc = Pinecone(api_key=PINECONE_API_KEY)
        ensure_pinecone_index(pc)

        print(
            "💾 Pinecone에 임베딩 중... "
            f"(총 {len(documents)}개 문서, 인덱스: {PINECONE_INDEX_NAME}, 네임스페이스: {PINECONE_NAMESPACE})"
        )

        vectorstore = PineconeVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            index_name=PINECONE_INDEX_NAME,
            namespace=PINECONE_NAMESPACE,
        )

        print("✅ Pinecone 저장 완료")
        return vectorstore
    except Exception as exc:
        print(f"❌ Pinecone 저장 실패: {exc}")
        raise


def test_search(vectorstore: PineconeVectorStore, query: str = "냉면") -> None:
    """임베딩 결과를 간단히 검색 테스트"""
    print(f"\n🔍 테스트 검색: '{query}'")
    results = vectorstore.similarity_search(query, k=3)

    print(f"검색 결과 {len(results)}개:")
    for idx, doc in enumerate(results, start=1):
        print(f"\n--- 결과 {idx} ---")
        print(f"이름: {doc.metadata.get('name')}")
        print(f"카테고리: {doc.metadata.get('category')}")
        print(f"위치: {doc.metadata.get('location_type')}")
        print(f"리뷰수: {doc.metadata.get('naver_review_count')}")


# ==================== 메인 실행 ====================
def main() -> None:
    """MySQL→Pinecone 전체 실행"""
    print("=" * 60)
    print("MySQL → Pinecone 임베딩 시작")
    print("=" * 60)

    connection = None
    try:
        connection = get_mysql_connection()
        restaurants = fetch_restaurants_data(connection)

        if not restaurants:
            print("⚠️  조회된 데이터가 없습니다.")
            return

        documents = convert_to_langchain_documents(restaurants)
        vectorstore = create_pinecone_vectorstore(documents)

        test_search(vectorstore, "순대국 가성비")
        test_search(vectorstore, "날씨 좋을 때 먹기 좋은 음식")

        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)
    except Exception as exc:
        print(f"\n❌ 오류 발생: {exc}")
        import traceback

        traceback.print_exc()
    finally:
        if connection:
            connection.close()
            print("MySQL 연결 종료")


if __name__ == "__main__":
    main()
