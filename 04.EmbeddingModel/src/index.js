import { OpenAIEmbeddings } from "@langchain/openai";
import OpenAI from "openai";
import { GoogleGenerativeAIEmbeddings } from "@langchain/google-genai";
import { config } from "dotenv";

// upstage curl로 호출하고 받은 값
import { kingResponse } from '../sample/king.js';
import { koreanKingResponse } from '../sample/koreanKing.js';

// .env 파일에서 환경 변수 로드
config();

/*
 * =========================================
 * 코사인 유사도 계산 헬퍼 함수
 * =========================================
 * LangChain.js는 파이썬 라이브러리와 달리
 * 내장된 코사인 유사도 함수를 직접 제공하지 않으므로,
 * 벡터 계산을 위한 함수를 만듭니다.
 */

/**
 * 두 벡터의 내적(Dot Product)을 계산합니다.
 * @param {number[]} vecA
 * @param {number[]} vecB
 * @returns {number}
 */
function dotProduct(vecA, vecB) {
  let product = 0;
  for (let i = 0; i < vecA.length; i++) {
    product += vecA[i] * vecB[i];
  }
  return product;
}

/**
 * 벡터의 크기(Magnitude)를 계산합니다. (L2 norm)
 * @param {number[]} vec
 * @returns {number}
 */
function magnitude(vec) {
  let sumOfSquares = 0;
  for (let i = 0; i < vec.length; i++) {
    sumOfSquares += vec[i] * vec[i];
  }
  return Math.sqrt(sumOfSquares);
}

/**
 * 두 벡터 간의 코사인 유사도를 계산합니다.
 * (A · B) / (||A|| * ||B||)
 * @param {number[]} vecA
 * @param {number[]} vecB
 * @returns {number}
 */
function cosineSimilarity(vecA, vecB) {
  if (vecA.length !== vecB.length) {
    throw new Error("벡터의 차원이 다릅니다.");
  }
  const magA = magnitude(vecA);
  const magB = magnitude(vecB);
  
  if (magA === 0 || magB === 0) {
    return 0; // 0으로 나누기 방지
  }
  
  return dotProduct(vecA, vecB) / (magA * magB);
}


/*
 * =========================================
 * 메인 비교 로직
 * =========================================
 */
async function compareEmbeddingModels() {
  const text1 = "king";
  const text2 = "왕";

  console.log(`비교할 단어: "${text1}" vs "${text2}"`);
  console.log("=".repeat(40));

//   // --- 1. OpenAI 임베딩 ---
  try {
    console.log("\n🚀 OpenAI 모델 테스트 중...");
    
    // (다른 모델: text-embedding-ada-002)
    const openaiEmbeddings = new OpenAIEmbeddings({
      model: "text-embedding-3-large"
    });
    
    // embedQuery를 사용해 각 텍스트를 벡터로 변환
    const vecOpenAI1 = await openaiEmbeddings.embedQuery(text1);
    const vecOpenAI2 = await openaiEmbeddings.embedQuery(text2);

    // 유사도 계산
    const similarityOpenAI = cosineSimilarity(vecOpenAI1, vecOpenAI2);
    
    console.log(`[OpenAI] 모델: ${openaiEmbeddings.model}`);
    console.log(`[OpenAI] 벡터 차원: ${vecOpenAI1.length}`);
    console.log(`[OpenAI] 유사도 점수: ${similarityOpenAI.toFixed(6)}`);

  } catch (error) {
    console.error("[OpenAI] 오류 발생:", error.message);
    console.log("OPENAI_API_KEY가 .env 파일에 올바르게 설정되었는지 확인하세요.");
  }

  // --- 2. Google AI 임베딩 ---
  try {
    console.log("\n🚀 Google AI (Google) 모델 테스트 중...");
    
    // (기본 모델: text-embedding-004)
    const googleAIEmbeddings = new GoogleGenerativeAIEmbeddings({
      model: "text-embedding-004"
    }); 
    
    // embedQuery를 사용해 각 텍스트를 벡터로 변환
    const vecGoogle1 = await googleAIEmbeddings.embedQuery(text1);
    const vecGoogle2 = await googleAIEmbeddings.embedQuery(text2);

    // 유사도 계산
    const similarityGoogle = cosineSimilarity(vecGoogle1, vecGoogle2);
    
    console.log(`[Google AI] 모델: ${googleAIEmbeddings.model}`);
    console.log(`[Google AI] 벡터 차원: ${vecGoogle1.length}`);
    console.log(`[Google AI] 유사도 점수: ${similarityGoogle.toFixed(6)}`);

  } catch (error) {
    console.error("[Google AI] 오류 발생:", error.message);
    console.log("Google Cloud 인증(gcloud auth application-default login) 및 GOOGLE_PROJECT_ID가 올바르게 설정되었는지 확인하세요.");
  }


  // --- 3. Upstage 임베딩 ---
  try {
    console.log("\n🚀 Upstage 모델 테스트 중...");
    

    // NOTE: Upstage Embedding Model은 LangChain.js에서 제대로 동작하지 않음
    // const apiKey = "up_c6AhsMfjR4c4M6dDecLaEdRXOJ0gy";
    // const openai = new OpenAI({
    //     apiKey: apiKey,
    //     baseURL: "https://api.upstage.ai/v1"
    // });
    
    // embedQuery를 사용해 각 텍스트를 벡터로 변환
    // const vecUpstage1 = await openai.embeddings.create({
    //     input: text1,
    //     model: "embedding-query",
    // });
    // const vecUpstage2 = await openai.embeddings.create({
    //     input: text2,
    //     model: "embedding-query",
    // });

    // console.log(vecUpstage1.data[0].embedding);
    // console.log(vecUpstage2);


    // 유사도 계산
    const similarityUpstage = cosineSimilarity(kingResponse.data[0].embedding, koreanKingResponse.data[0].embedding);
    
    console.log(`[Upstage AI] 모델: embedding-query`);
    console.log(`[Upstage AI] 벡터 차원: ${kingResponse.data[0].embedding.length}`);
    console.log(`[Upstage AI] 유사도 점수: ${similarityUpstage}`);

  } catch (error) {
    console.error("[Upstage AI] 오류 발생:", error.message);
    console.log("UPSTAGE_API_KEY가 .env 파일에 올바르게 설정되었는지 확인하세요.");
  }
}

// 비교 함수 실행
compareEmbeddingModels();