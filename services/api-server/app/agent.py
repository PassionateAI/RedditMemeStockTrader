"""
================================================================================
File: agent.py
Description: 
    English: Defines the AI Agent responsible for analyzing text sentiment.
             It uses OpenAI GPT models but falls back to a 'Mock Mode' if no API key is found.
             This ensures the system remains robust (Fault Tolerance).
    Korean: 텍스트 감성을 분석하는 AI 에이전트를 정의합니다.
            OpenAI GPT 모델을 사용하지만, API 키가 없을 경우 '모의(Mock) 모드'로 전환됩니다.
            이는 시스템이 죽지 않고 계속 동작하게 하는 내결함성(Fault Tolerance)을 보장합니다.
Author: User (Meme Stock Engineer)
================================================================================
"""

import os
import json
import random
from openai import OpenAI
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# 1. Data Schema Definition (데이터 구조 정의)
# ------------------------------------------------------------------------------
class StockDecision(BaseModel):
    """
    English: Pydantic Model to enforce strict data structure on AI output.
             This prevents the AI from hallucinating invalid formats. (Type Safety)
    Korean: AI 출력의 데이터 구조를 강제하기 위한 Pydantic 모델입니다.
            AI가 이상한 포맷의 데이터를 뱉는 환각(Hallucination) 현상을 방지합니다. (타입 안전성)
    """
    ticker: str = Field(description="The stock ticker symbol (e.g., TSLA, GME)")
    sentiment: str = Field(description="Sentiment: 'positive', 'negative', or 'neutral'")
    action: str = Field(description="Decision: 'BUY', 'SELL', or 'HOLD'")
    confidence: float = Field(description="Confidence score (0.0 - 1.0)")
    reasoning: str = Field(description="Short explanation in Korean")

# ------------------------------------------------------------------------------
# 2. AI Agent Class (AI 에이전트 클래스)
# ------------------------------------------------------------------------------
class MemeStockAgent:
    def __init__(self):
        """
        English: Initializes the OpenAI client securely using environment variables.
                 Implements a 'Circuit Breaker' pattern: if no key, disable AI calls.
        Korean: 환경 변수를 사용하여 OpenAI 클라이언트를 안전하게 초기화합니다.
                '서킷 브레이커' 패턴을 구현하여, 키가 없으면 AI 호출을 차단하고 Mock 모드로 전환합니다.
        """
        # English: Load API Key from .env file (Security Best Practice)
        # Korean: .env 파일에서 API 키 로드 (보안 모범 사례)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            print("✅ OpenAI Client Connected (Brain Online)")
        else:
            print("⚠️ No API Key found. Running in MOCK MODE (Zombie Brain)")

    def analyze(self, text: str) -> dict:
        """
        English: The main public method to process text.
                 It decides whether to use Real AI or Mock Data based on client status.
        Korean: 텍스트를 처리하는 메인 메서드입니다.
                클라이언트 상태에 따라 실제 AI를 쓸지, 가짜 데이터를 쓸지 결정합니다.
        """
        # English: Guard Clause - If client is not ready, return mock data immediately.
        # Korean: 보호 절 (Guard Clause) - 클라이언트가 준비 안 됐으면 즉시 가짜 데이터 반환.
        if not self.client:
            return self._mock_analysis(text)

        try:
            # English: Prompt Engineering - Giving the AI a persona (Role Playing).
            # Korean: 프롬프트 엔지니어링 - AI에게 페르소나(역할)를 부여합니다.
            system_prompt = """
            You are a reckless WallStreetBets trader. 
            Analyze the given Reddit post and decide whether to BUY, SELL, or HOLD.
            Output must be valid JSON matching the schema.
            Reply in Korean for the 'reasoning' field.
            """
            
            # English: Call OpenAI API with JSON mode enabled for deterministic output.
            # Korean: 결정론적 출력을 위해 JSON 모드를 활성화하여 OpenAI API를 호출합니다.
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze: {text}"}
                ]
            )
            
            # English: Parse the JSON string into a Python dictionary.
            # Korean: JSON 문자열을 파이썬 딕셔너리로 파싱합니다.
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # English: Fallback for missing keys (Defensive Programming).
            # Korean: 키 누락에 대비한 대비책 (방어적 프로그래밍).
            if "ticker" not in result: result["ticker"] = "UNKNOWN"
            
            return result

        except Exception as e:
            # English: Error Handling - Log the error and fail gracefully (Graceful Degradation).
            # Korean: 에러 처리 - 에러를 로그에 남기고 우아하게 실패합니다 (시스템 셧다운 방지).
            print(f"❌ AI Analysis Failed: {e}")
            return self._mock_analysis(text)

    def _mock_analysis(self, text: str) -> dict:
        """
        English: Internal helper method to generate fake data for testing/fallback.
        Korean: 테스트나 장애 대응(Fallback)을 위해 가짜 데이터를 생성하는 내부 도우미 메서드입니다.
        """
        tickers = ["GME", "TSLA", "NVDA", "AAPL", "AMC"]
        actions = ["BUY", "SELL", "HOLD"]
        
        return {
            "ticker": random.choice(tickers),
            "sentiment": "neutral",
            "action": random.choice(actions),
            "confidence": round(random.uniform(0.1, 0.9), 2),
            "reasoning": "OpenAI 키가 없어서 랜덤으로 찍었습니다. (Mock Mode)"
        }