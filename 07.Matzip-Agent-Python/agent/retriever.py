import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_upstage import UpstageEmbeddings

load_dotenv()

UPSTAGE_MODEL = os.getenv("UPSTAGE_EMBEDDING_MODEL", "solar-embedding-1-large")
PERSIST_DIR = "./chroma_db_upstage"
COLLECTION_NAME = "jamsil_restaurants_upstage"

# UpstageEmbeddings requires an explicit model name; missing model raises a validation error.
embeddings = UpstageEmbeddings(model=UPSTAGE_MODEL)

# `persist_directory`를 지정하여 기존 벡터 저장소를 로드합니다.
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=PERSIST_DIR,
    embedding_function=embeddings,
)

# 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
retriever = vectorstore.as_retriever()
