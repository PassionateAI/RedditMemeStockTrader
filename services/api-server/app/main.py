"""
================================================================================
File: main.py
Description: 
    English: Entry point for the FastAPI application. 
             It exposes REST API endpoints for external services (like Airflow) to interact with the AI Agent.
    Korean: FastAPI 애플리케이션의 진입점입니다.
            외부 서비스(Airflow 등)가 AI 에이전트와 상호작용할 수 있도록 REST API 엔드포인트를 노출합니다.
================================================================================
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import MemeStockAgent

# English: Initialize the FastAPI app framework.
# Korean: FastAPI 앱 프레임워크를 초기화합니다.
app = FastAPI()

# English: Initialize the AI Agent instance once at startup (Singleton Pattern).
#          This avoids re-creating the OpenAI connection for every request.
# Korean: 시작 시 AI 에이전트 인스턴스를 한 번만 생성합니다 (싱글톤 패턴).
#         요청마다 OpenAI 연결을 다시 맺는 낭비를 방지합니다.
agent = MemeStockAgent()

# ------------------------------------------------------------------------------
# Data Transfer Object (DTO)
# ------------------------------------------------------------------------------
class AnalysisRequest(BaseModel):
    """
    English: Defines the expected request body structure.
    Korean: 요청 본문(Body)에 들어올 데이터 구조를 정의합니다.
    """
    text: str

# ------------------------------------------------------------------------------
# API Endpoints (라우트 정의)
# ------------------------------------------------------------------------------

@app.get("/")
def read_root():
    """
    English: Health Check Endpoint. Used to verify if the server is running.
    Korean: 헬스 체크 엔드포인트입니다. 서버가 살아있는지 확인할 때 사용합니다.
    """
    return {"status": "ok", "message": "Meme Stock Trader Brain is Running 🧠"}

@app.post("/analyze")
def analyze_text(request: AnalysisRequest):
    """
    English: Core Endpoint. Receives text from Airflow, processes it via Agent, and returns the result.
    Korean: 핵심 엔드포인트입니다. Airflow로부터 텍스트를 받아 에이전트를 통해 처리하고 결과를 반환합니다.
    """
    print(f"📥 Received text: {request.text[:30]}...")
    
    # English: Delegate the business logic to the Agent class (Separation of Concerns).
    # Korean: 비즈니스 로직 처리를 Agent 클래스에게 위임합니다 (관심사의 분리).
    result = agent.analyze(request.text)
    
    print(f"📤 Decision: {result}")
    return result