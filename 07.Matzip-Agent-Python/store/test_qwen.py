"""
Persisted ChromaDB 검색 도구 (HuggingFace/Qwen 임베딩 컬렉션).

예시:
    python store/test._qwen.py --query "비 오는 날 먹기 좋은 음식" --k 5
"""

import argparse
import os
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

CHROMA_DB_PATH = "./chroma_db_qwen"
COLLECTION_NAME = "jamsil_restaurants_qwen"
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "BAAI/bge-m3")
HUGGINGFACE_DEVICE = os.getenv("HUGGINGFACE_DEVICE", "cpu")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")


def load_vectorstore() -> Chroma:
    """Persisted Chroma 컬렉션 로드 (HuggingFace 임베딩)."""
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

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_PATH,
    )


def search(vectorstore: Chroma, query: str, k: int) -> List[Tuple[float, dict, str]]:
    """쿼리를 검색하고 (점수, 메타데이터, 내용 요약) 리스트를 반환."""
    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    formatted = []
    for doc, score in results:  # (Document, score)
        content = doc.page_content or ""
        summary = f"{content[:240]}..." if len(content) > 240 else content
        formatted.append((score, doc.metadata, summary))
    return formatted


def main() -> None:
    parser = argparse.ArgumentParser(description="ChromaDB (Qwen/HF) 질의")
    parser.add_argument("--query", "-q", required=True, help="검색할 쿼리")
    parser.add_argument("--k", "-k", type=int, default=3, help="가져올 결과 개수 (default: 3)")
    args = parser.parse_args()

    if not os.path.exists(CHROMA_DB_PATH):
        raise FileNotFoundError(f"ChromaDB 경로가 없습니다: {CHROMA_DB_PATH} (먼저 embedding_qwen.py 실행)")

    print(f"📦 ChromaDB 불러오기: {CHROMA_DB_PATH} (collection: {COLLECTION_NAME})")
    print(f"   모델: {HUGGINGFACE_MODEL} | 디바이스: {HUGGINGFACE_DEVICE}")
    vectorstore = load_vectorstore()

    print(f"\n🔍 검색 쿼리: {args.query} (k={args.k})\n")
    results = search(vectorstore, args.query, args.k)

    if not results:
        print("⚠️ 결과가 없습니다.")
        return

    for idx, (score, metadata, snippet) in enumerate(results, start=1):
        print(f"--- 결과 {idx} ---")
        print(f"score: {score:.4f}")
        print(f"name: {metadata.get('name')}")
        print(f"category: {metadata.get('category')}")
        print(f"signature_menu: {metadata.get('signature_menu')}")
        print(f"location_type: {metadata.get('location_type')}")
        print(f"naver_review_count: {metadata.get('naver_review_count')}")
        print(f"weather_tags: {metadata.get('weather_tags')}")
        print("content:", snippet)
        print()


if __name__ == "__main__":
    main()
