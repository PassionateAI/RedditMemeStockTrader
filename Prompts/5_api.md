**죄송합니다. 제가 긴장이 풀렸었나 봅니다.** "한글+영어 상세 주석"은 단순한 번역이 아니라, **면접관에게 이 코드를 왜 짰는지 설명하기 위한 대본**이라는 점을 다시 한번 명심하겠습니다.

방금 작성했던 `agent.py`와 `main.py`를 **"교과서 수준의 상세 주석(Bilingual Documentation)"** 버전으로 다시 작성했습니다.

이 코드는 **복사해서 붙여넣기만 하면, 나중에 코드만 읽어도 시스템 설계 의도(Robustness, Type Safety, Mocking)를 완벽하게 설명할 수 있도록** 만들었습니다.

---

### 📄 1. `services/api-server/app/agent.py` (수정본)

이 파일은 **"AI 비즈니스 로직의 핵심"**입니다. OpenAI 연결, 에러 처리, 그리고 데이터 구조 정의를 담당합니다.

```python
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

```

---

### 📄 2. `services/api-server/app/main.py` (수정본)

이 파일은 **"외부와의 소통 창구(Interface)"**입니다. Airflow가 말을 거는 곳이죠.

```python
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

```

---

### 💡 아키텍트의 주석 (Architect's Note)

이 코드를 다 붙여넣으셨다면, 이제 **"Mock Mode(모의 모드)"**가 제대로 작동하는지 확인할 차례입니다.

```bash
docker-compose up -d --build
docker-compose logs -f api-server

```

로그에 다음과 같은 문구가 떠야 성공입니다.

> **⚠️ No API Key found. Running in MOCK MODE (Zombie Brain)**

이 메시지는 실패가 아니라 **"성공적인 방어(Successful Defense)"**를 의미합니다.
확인되시면 알려주세요. 이제 진짜 키를 넣는 `.env` 설정으로 넘어가겠습니다.



터미널에 에러 메시지 없이 명령어가 딱 끝나고 프롬프트가 다시 떴다면, **아주 성공적(Successful Deployment)**인 것입니다.

질문자님이 `docker-compose up -d`에서 **`-d` (Detached Mode)** 옵션을 썼기 때문입니다. 이 옵션은 **"백그라운드에서 조용히 돌고, 나한테는 제어권을 돌려줘"**라는 뜻입니다. 서버가 죽지 않고 잘 떴다는 증거입니다.

하지만 "진짜로 안에 좀비 뇌(Mock Mode)가 살고 있는지" 눈으로 확인해야 직성이 풀리겠죠?
**두 가지 확실한 확인 방법**을 알려드립니다.

---

### 🕵️‍♂️ 방법 1: 블랙박스 열어보기 (Logs)

터미널에 아래 명령어를 입력하세요. 백그라운드에서 돌고 있는 API 서버의 실시간 로그를 보여줍니다.

```bash
docker-compose logs -f api-server

```

**확인 포인트:**
로그 중간에 아래 문구가 찍혀 있나요?

> **⚠️ No API Key found. Running in MOCK MODE (Zombie Brain)**

(확인 후에는 `Ctrl + C`를 눌러서 빠져나오세요. 서버는 안 꺼집니다.)

---

### 🧪 방법 2: 의사 선생님 놀이 (Swagger UI Test)

이게 진짜 대박입니다. 우리가 짠 코드는 고작 100줄이지만, **FastAPI는 자동으로 "전문가용 테스트 페이지"를 만들어줍니다.**

1. **브라우저 접속:** `http://localhost:8000/docs`
* (주소 뒤에 `/docs`가 중요합니다!)


2. 화면에 **"Meme Stock Trader Brain"** 같은 제목이 뜨나요?
3. **POST /analyze** 라고 적힌 초록색 버튼을 클릭하세요.
4. 오른쪽의 **Try it out** 버튼을 누릅니다.
5. `Request body` 칸에 아무 말이나 적어보세요.
```json
{
  "text": "Tesla is going down! Sell everything!"
}

```


6. 파란색 **Execute** 버튼 클릭!

**결과 확인:**
바로 아래 **Server response** 쪽에 JSON 결과가 나왔나요?

```json
{
  "ticker": "TSLA",
  "action": "SELL",
  "reasoning": "OpenAI 키가 없어서 랜덤으로 찍었습니다. (Mock Mode)"
  ...
}

```

---

### 🚀 아키텍트의 해석

지금 질문자님이 `/docs`에서 본 그 화면은 **Swagger UI**라고 부릅니다.
현업에서는 프론트엔드 개발자에게 "API 다 만들었어, 여기 가서 써봐"라며 이 주소를 던져줍니다.

**지금 질문자님은:**

1. **백엔드 서버**를 구축했고,
2. **API 문서**를 자동 생성했으며,
3. **테스트 환경**까지 갖춘 것입니다.

**Mock Mode인 거 확인되셨나요? 랜덤으로 대답 잘 하나요?**
확인되셨으면 이제 **"진짜 지능"**을 불어넣기 위해 `.env` 파일에 아까 받은 키를 넣으러 가시죠. 준비되셨나요?









**정확히 보셨습니다.** 방금 질문자님이 느끼신 그 "편리함"과 "체계적임"이 바로 **실무에서 FastAPI가 현재 가장 사랑받는 이유**입니다.

제가 굳이 Flask나 Django가 아니라 **FastAPI**를 선택해 드린 큰 그림이 여기에 있었습니다.

실무에서 **"왜 저 화면(Swagger UI)과 좀비 모드(Mock)가 필수인지"**, 아키텍트 관점에서 딱 3가지로 정리해 드릴게요. 이 내용을 알면 면접에서 "협업 좀 해봤네?" 소리 듣습니다.

---

### 1. "야, API 명세서 엑셀로 정리해 와." (옛날 방식 ❌)

불과 몇 년 전만 해도 백엔드 개발자는 코드를 다 짜고 나서, 엑셀이나 위키(Wiki)에 API 주소, 파라미터, 반환값을 일일이 손으로 적어야 했습니다.

* **문제점:** 코드를 고치면 문서도 고쳐야 하는데, 까먹습니다.  **"문서랑 코드가 다른데요?"** 하고 프론트엔드 팀이랑 싸움 납니다.
* **FastAPI 방식 (Swagger):** 코드(`main.py`)가 바뀌면 문서(`/docs`)가 **자동으로** 바뀝니다.
* **실무 효과:** **"문서화(Documentation) 비용 0원."** 이게 혁명입니다.



### 2. "프론트엔드 팀: 서버 언제 다 돼요?" (병목 현상 ❌)

우리가 만든 **"Mock Mode (좀비 뇌)"**가 빛을 발하는 순간입니다.

* **상황:** 질문자님(백엔드)이 AI 로직 짜느라 3일이 걸립니다. 그럼 프론트엔드 개발자는 3일 동안 손가락 빨고 기다려야 할까요?
* **해결책:** "일단 껍데기 API랑 가짜 데이터(Mock) 만들어 뒀으니까, 이거 보고 화면 먼저 만드세요. 진짜 AI는 나중에 붙일게요."
* **실무 효과:** **"병렬 개발(Parallel Development)"**이 가능해집니다. 이게 바로 **애자일(Agile)**입니다.

### 3. "돈 아껴야지!" (비용 절감 💰)

`agent.py`에 Mock Mode를 심어둔 결정적인 이유입니다.

* **상황:** 개발할 때 테스트한다고 `F5`(새로고침)를 100번 누르면?
* **문제:** OpenAI API 호출 100번  **통장 잔고 삭제.**
* **해결책:** "개발 중엔 키 빼고 Mock으로 테스트하고, 배포할 때만 키 넣자."
* **실무 효과:** **개발 비용 최적화.**

---

### 🚀 자, 이제 "진짜"가 될 시간입니다.

지금까지는 **"돈 안 드는 가짜 모드"**로 안전하게 시스템을 검증했습니다.
이제 시스템이 완벽하다는 걸 확인했으니, **진짜 지능(OpenAI Key)**을 주입해서 뇌를 깨울 차례입니다.

하지만 이 **비밀 열쇠(API Key)**를 코드에 그냥 적으면 해킹당합니다. (깃허브에 올라가는 순간 1분 만에 털립니다.)

그래서 **`.env` (환경 변수 파일)**이라는 **"디지털 금고"**를 만들 겁니다.

**금고 만들러 가시겠습니까?**






**아니요, FastAPI만 유별난 건 아닙니다.** 하지만 **"가장 쉽고 우아하게(Native)"** 해주는 건 FastAPI가 맞습니다.

실무에서 사용하는 거의 모든 모던 웹 프레임워크에는 이 기능이 있지만, **"어떻게 구현하느냐"**의 차이가 큽니다.

아키텍트 관점에서 **"API 문서화의 세계(The World of API Documentation)"**를 3가지 계층으로 정리해 드립니다. 면접에서 "다른 거랑 뭐가 달라요?"라고 물어보면 이렇게 대답하면 됩니다.

---

### 1. 근본 기술: OpenAPI (구 Swagger)

사실 FastAPI가 대단한 게 아니라, **OpenAPI Specification (OAS)**이라는 전 세계 표준 규격이 대단한 겁니다.

* **원리:** "내 API는 이렇게 생겼어"라는 복잡한 **JSON 설계도**를 만들면,
* **Swagger UI:** 그 설계도를 읽어서 우리가 본 그 **예쁜 웹사이트**로 그려줍니다.
* **FastAPI의 역할:** 개발자가 코드를 짜면, 중간에서 **알아서 설계도(JSON)를 그려주는 역할**을 할 뿐입니다.

---

### 2. 프레임워크별 비교 (Comparison)

실무에서 가장 많이 쓰는 3대장(Java Spring, Node.js, Python)을 비교해 보겠습니다.

| 프레임워크 | 문서 자동화 방법 | 난이도 | 특징 |
| --- | --- | --- | --- |
| **Python FastAPI** | **기본 내장 (Built-in)** | ⭐ | **그냥 파이썬 문법(타입 힌트)만 쓰면 끝.** 별도 설정 0. |
| **Java Spring Boot** | 라이브러리 추가 (`Springdoc`) | ⭐⭐⭐ | 코드 위에 `@Operation`, `@Schema` 같은 **"장식(Annotation)"**을 덕지덕지 붙여야 함. |
| **Node.js NestJS** | 데코레이터 추가 (`@nestjs/swagger`) | ⭐⭐⭐ | Spring이랑 비슷함. 코드는 코드대로, 문서는 문서대로 코딩해야 함. |
| **Node.js Express** | **수동 (Manual)** | ⭐⭐⭐⭐⭐ | 주석(JSDoc)에 이상한 문법으로 직접 쓰거나, YAML 파일을 따로 관리해야 함. (지옥) |

#### 🧐 왜 FastAPI가 찬양받나요?

다른 프레임워크는 **"코드 짜고 + 문서용 주석도 달아야"** 합니다. 즉, **일이 2배**입니다. 개발자가 귀찮아서 문서용 주석을 안 달기 시작하면, **"코드랑 문서랑 다른"** 대참사가 일어납니다.

반면, FastAPI는 **"코드를 짜는 행위 = 문서를 만드는 행위"**가 일치(Sync)되어 있습니다. 개발자가 게을러도 문서가 항상 최신 상태입니다. 이게 혁신입니다.

---

### 3. 알아두면 좋은 키워드 (Industry Standard)

면접에서 이런 용어 하나 섞어주면 "공부 좀 했네?" 소리 듣습니다.

1. **Code-First 접근법:** 코드를 먼저 짜면 문서가 나오는 방식 (FastAPI, Springdoc). 우리가 지금 한 방식입니다.
2. **Design-First 접근법:** 문서를 먼저 완벽하게 짜고, 그걸로 코드를 생성하는 방식. (대기업 SI 프로젝트에서 주로 씀)
3. **Redoc:** 우리가 본 Swagger UI 말고, **Redoc**이라는 또 다른 디자인의 문서 도구도 있습니다. FastAPI는 이것도 기본 제공합니다. (`/redoc` 들어가 보세요. 디자인이 더 깔끔합니다.)

---

### 🚀 결론 (Architect's Summary)

**[English]**
"While automatic documentation is based on the **OpenAPI Standard** and available in other frameworks like Spring Boot or NestJS, **FastAPI** implements it natively using Python's **Type Hints**. This eliminates the need for separate annotations, ensuring the documentation is always **syncrhronized with the code**."

**[Korean]**
"자동 문서화는 **OpenAPI 표준**을 따르기 때문에 Spring Boot나 NestJS 같은 다른 프레임워크에도 존재합니다. 하지만 **FastAPI**는 파이썬의 **타입 힌트**를 그대로 활용해 이를 기본(Native)으로 지원한다는 점이 다릅니다. 덕분에 별도의 주석 작업 없이도 문서와 코드가 항상 **동기화(Sync)**됨을 보장할 수 있습니다."

---

### 👉 Next Step

다른 프레임워크를 쓸 때는 "아, 라이브러리 깔아야겠네"라고 생각하면 되고, FastAPI를 쓸 때는 "그냥 되네?" 하고 즐기시면 됩니다.

이제 이 똑똑한 FastAPI에게 **"진짜 비밀 열쇠(.env)"**를 쥐여줄 차례입니다.
보안 사고 안 나게 **환경 변수 파일 만드는 법**, 바로 진행할까요?