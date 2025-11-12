from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# 1. `persist_directory`를 지정하여 기존 벡터 저장소를 로드합니다.
vectorstore = Chroma(
    collection_name="jamsil-matzip",
    persist_directory="./chroma_langchain_db",
    embedding_function=OpenAIEmbeddings()
)

# 2. 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
retriever = vectorstore.as_retriever()
