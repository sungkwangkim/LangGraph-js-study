from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

url_list = [
  "https://m.blog.naver.com/ban__di/223783862789",
  "https://lazyyellow.tistory.com/87",
  "https://funktionalflow.com/%EC%9E%A0%EC%8B%A4-%EB%A7%9B%EC%A7%91/",
]

# 1. 블로그 글들을 로드합니다.
loader = WebBaseLoader(
    web_paths=url_list
)

# 2. load()를 실행하면 리스트의 모든 URL을 로드합니다.
docs = loader.load()

# 3. 블로그 글들을 작은 조각(chunk)으로 나눕니다.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)


doc_splits = text_splitter.split_documents(docs)


# 3. 각 텍스트 조각을 벡터(숫자로 된 표현)로 변환하고,
# Chroma 벡터 데이터베이스에 저장합니다.
vectorstore = Chroma.from_documents(
    collection_name="jamsil-matzip",
    documents=doc_splits,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_langchain_db"
)

# 4. 저장된 벡터 데이터베이스를 기반으로 검색기(retriever)를 만듭니다.
retriever = vectorstore.as_retriever()
