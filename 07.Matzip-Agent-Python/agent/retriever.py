import os

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
from pinecone import Pinecone

load_dotenv()

UPSTAGE_MODEL = os.getenv("UPSTAGE_EMBEDDING_MODEL", "solar-embedding-1-large")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY가 .env 파일에 설정되지 않았습니다")

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "jamsil-restaurants-upstage")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "public")

# UpstageEmbeddings requires an explicit model name; missing model raises a validation error.
embeddings = UpstageEmbeddings(model=UPSTAGE_MODEL)

pc = Pinecone(api_key=PINECONE_API_KEY)
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    raise ValueError(
        f"Pinecone 인덱스 '{PINECONE_INDEX_NAME}'가 없습니다. "
        "임베딩 스크립트를 먼저 실행해 주세요."
    )

vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
    namespace=PINECONE_NAMESPACE,
)

# 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
retriever = vectorstore.as_retriever()
