"""
Persisted ChromaDB 검색 도구.

예시:
    python store/test.py --query "냉면" --k 3
"""

import argparse
import os
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "jamsil_restaurants"
EMBEDDING_MODEL = "text-embedding-3-small"


def load_vectorstore() -> Chroma:
    """Persisted Chroma 컬렉션 로드."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )


def search(vectorstore: Chroma, query: str, k: int) -> List[Tuple[float, dict, str]]:
    """쿼리를 검색하고 (점수, 메타데이터, 내용 요약) 리스트를 반환."""
    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    formatted = []
    for doc, score in results:  # Chroma returns (Document, score)
        content = doc.page_content or ""
        summary = f"{content[:200]}..." if len(content) > 200 else content
        formatted.append((score, doc.metadata, summary))
    return formatted


def main() -> None:
    parser = argparse.ArgumentParser(description="ChromaDB 질의")
    parser.add_argument("--query", "-q", required=True, help="검색할 쿼리")
    parser.add_argument("--k", "-k", type=int, default=3, help="가져올 결과 개수 (default: 3)")
    args = parser.parse_args()

    print(f"📦 ChromaDB 불러오기: {CHROMA_DB_PATH} (collection: {COLLECTION_NAME})")
    vectorstore = load_vectorstore()

    print(f"🔍 검색 쿼리: {args.query} (k={args.k})\n")
    results = search(vectorstore, args.query, args.k)

    if not results:
        print("⚠️ 결과가 없습니다.")
        return

    for idx, (score, metadata, snippet) in enumerate(results, start=1):
        print(f"--- 결과 {idx} ---")
        print(f"score: {score:.4f}")
        print(f"id: {metadata.get('restaurant_id')}")
        print(f"name: {metadata.get('name')}")
        print(f"category: {metadata.get('category')}")
        print(f"naver_id: {metadata.get('naver_id')}")
        print(f"signature_menu: {metadata.get('signature_menu')}")
        print(f"location_type: {metadata.get('location_type')}")
        print(f"naver_review_count: {metadata.get('naver_review_count')}")
        print(f"weather_tags: {metadata.get('weather_tags')}")
        print("content:", snippet)
        print()


if __name__ == "__main__":
    main()
