"""
================================================================================
File: real_quant_dag.py
Author: User (System Architect)
Date: 2026-01-18

Description:
    [English]
    Real-world Quantitative Trading Pipeline.
    1. Ingestion: Fetches OHLCV (Open, High, Low, Close, Volume) data & News via Yahoo Finance.
    2. Processing: Calculates RSI (Relative Strength Index) using Pandas.
    3. Reasoning: Aggregates Technical (RSI) & Fundamental (News) data and asks OpenAI for a decision.
    4. Notification: Sends a formatted report to Slack.

    [Korean]
    실전 퀀트 트레이딩 파이프라인입니다.
    1. 수집: 야후 파이낸스를 통해 OHLCV(시가, 고가, 저가, 종가, 거래량) 및 최신 뉴스를 수집합니다.
    2. 가공: Pandas를 사용하여 RSI(상대강도지수) 기술적 지표를 직접 계산합니다.
    3. 판단: 기술적 지표(RSI)와 기본적 분석(뉴스)을 결합하여 AI에게 최종 투자 판단을 요청합니다.
    4. 알림: 분석된 결과를 슬랙으로 전송합니다.
================================================================================
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import requests
import json
import logging
import os
import psycopg2

# ------------------------------------------------------------------------------
# 1. Configuration & Constants (설정 및 상수 정의)
# ------------------------------------------------------------------------------
# English: Target stock tickers to monitor.
# Korean: 감시할 종목 리스트입니다. (미국 우량 기술주 위주)
TARGET_TICKERS = ["LAES", "RKLB", "PLTR", "AMD", "MSFT"]

# English: Internal API Service URL (Docker Service Name used).
# Korean: 내부 API 서버 주소입니다. Docker 네트워크 상의 서비스 이름('api-server')을 사용합니다.
API_URL = "http://api-server:8000/analyze"

# English: Slack Webhook URL from environment variables for security.
# Korean: 보안을 위해 .env 파일에서 슬랙 웹훅 URL을 로드합니다.
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

# 운영 환경에서 Postgres 접속 정보 (Docker Network 내부망 기준)
# 로컬 외부 툴은 5433으로 접속하지만, 컨테이너끼리는 5432를 사용함
DB_CONN_INFO = {
    "host": "postgres",
    "port": "5432",
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow"
}

default_args = {
    'owner': 'quant_architect',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# ------------------------------------------------------------------------------
# 2. Technical Analysis Logic (기술적 분석 로직)
# ------------------------------------------------------------------------------
def calculate_rsi(series, period=14):
    """
    [Function: RSI Calculator]
    Calculates the Relative Strength Index (RSI) manually using Pandas.
    
    Args:
        series (pd.Series): A pandas series of stock closing prices.
        period (int): Lookback period (Standard is 14 days).
        
    Returns:
        float: The latest RSI value (0 ~ 100).
        
    Logic:
        RSI = 100 - (100 / (1 + RS))
        Where RS = Average Gain / Average Loss
    """
    # 1. Calculate price difference from the previous day (전일 대비 가격 차이 계산)
    delta = series.diff(1)
    
    # 2. Separate Gains and Losses (상승분과 하락분 분리)
    # where(condition, other): 조건이 참이면 그대로, 거짓이면 0으로 대체
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0) # 하락분은 양수로 변환하여 계산
    
    # 3. Calculate Moving Average (이동평균 계산)
    # rolling(window=14).mean(): 최근 14일간의 평균을 구함
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 4. Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # 5. Calculate Final RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Return the most recent RSI value (가장 최근일자의 RSI 반환)
    return rsi.iloc[-1]

# ------------------------------------------------------------------------------
# 3. Airflow Tasks (파이프라인 단계별 정의)
# ------------------------------------------------------------------------------

def fetch_market_data(**context):
    """
    [Task 1: Data Ingestion]
    Fetches real-time data from Yahoo Finance and creates a data packet for AI.
    """
    logging.info("🚀 Starting Market Data Collection...")
    market_report = []

    for ticker in TARGET_TICKERS:
        try:
            # Step A: Fetch Price Data (주가 데이터 수집)
            # period="1mo": Fetches last 1 month of data to calculate 14-day RSI.
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if df.empty:
                logging.warning(f"⚠️ No data found for {ticker}")
                continue

            # Step B: Calculate Technical Indicator (지표 계산)
            current_rsi = round(calculate_rsi(df['Close']), 2)
            current_price = round(df['Close'].iloc[-1], 2)
            
            # Step C: Generate Technical Signal (기술적 신호 판별)
            # RSI < 30: Oversold (Too cheap -> Buy Signal)
            # RSI > 70: Overbought (Too expensive -> Sell Signal)
            if current_rsi < 35:
                tech_signal = "OVERSOLD (Potential BUY opportunity)"
            elif current_rsi > 70:
                tech_signal = "OVERBOUGHT (Potential SELL warning)"
            else:
                tech_signal = "NEUTRAL (Wait and see)"

            # Step D: Fetch Fundamental News (뉴스 수집)
            # Gets top 3 recent news headlines to detect market sentiment.
            news_list = stock.news[:3]
            news_summary = ""
            for news in news_list:
                title = news.get('title', 'No Title')
                news_summary += f"- {title}\n"

            # Step E: Construct Payload (데이터 패키징)
            # This dictionary will be passed to the next task via XCom.
            payload = {
                "ticker": ticker,
                "price": current_price,
                "rsi": current_rsi,
                "technical_signal": tech_signal,
                "news": news_summary
            }
            market_report.append(payload)
            logging.info(f"✅ Processed {ticker}: RSI={current_rsi}")

        except Exception as e:
            logging.error(f"❌ Failed to process {ticker}: {e}")

    # Push data to XCom (Airflow's internal messaging system)
    return market_report

def analyze_with_ai(**context):
    """
    [Task 2: AI Reasoning]
    Sends the collected data to the API Server (OpenAI) for a comprehensive decision.
    """
    ti = context['ti']
    # Pull data from Task 1 (fetch_market_data)
    market_data = ti.xcom_pull(task_ids='fetch_market_data')
    
    if not market_data:
        logging.info("No market data to analyze.")
        return []

    final_decisions = []

    for data in market_data:
        # 프롬프트 수정: 2개 국어(English & Korean)로 답변 요구
        prompt = f"""
        [Role]
        You are a Wall Street Quant Trader.
        
        [Data]
        Target: {data['ticker']}
        Price: ${data['price']}
        Technical Indicator: RSI {data['rsi']} ({data['technical_signal']})
        
        Recent News:
        {data['news']}
        
        [Instruction]
        Synthesize the technical signal and news sentiment.
        - Analyze strictly based on the provided data.
        - Output MUST be a JSON format.
        
        [Output Format]
        {{
            "action": "BUY" or "SELL" or "HOLD",
            "confidence": 0.0 ~ 1.0,
            "reasoning_en": "One sentence summary in English.",
            "reasoning_kr": "한국어 한 문장 요약."
        }}
        """
        
        try:
            # Call API Server
            response = requests.post(API_URL, json={"text": prompt})
            result = response.json()

            # 🚨 [Bug Fix] 여기가 핵심입니다!
            # AI가 준 결과(result)에는 'ticker'가 없습니다.
            # 우리가 가지고 있던 원본 데이터(data)에서 이름표를 다시 붙여줘야 합니다.
            result['ticker'] = data['ticker']  # 👈 이름표 복구 완료
            
            # Merge AI result with original data for the report
            result['rsi'] = data['rsi']
            result['price'] = data['price']
            final_decisions.append(result)
            
        except Exception as e:
            logging.error(f"❌ AI Analysis Failed for {data['ticker']}: {e}")

    return final_decisions


def save_results_to_db(**context):
    """
    [Step 3] 분석 결과 PostgreSQL 적재 (Persistence)
    - Airflow run_id를 함께 저장하여 실행 이력 추적 가능하도록 설계
    - 트랜잭션 관리를 통해 데이터 일관성 보장
    """
    ti = context['ti']
    decisions = ti.xcom_pull(task_ids='analyze_with_ai')
    if not decisions:
        logging.info("No data to save.")
        return

    # 운영 추적을 위한 고유 실행 ID 추출
    dag_run_id = context['run_id']
    
    insert_query = """
    INSERT INTO market_analysis_log 
    (run_id, ticker, price_at_run, rsi_value, ai_decision, ai_confidence, analysis_report_kr)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    try:
        conn = psycopg2.connect(**DB_CONN_INFO)
        cur = conn.cursor()
        for d in decisions:
            cur.execute(insert_query, (
                dag_run_id,
                d['ticker'],
                d['price'],
                d['rsi'],
                d.get('action', 'HOLD'),
                d.get('confidence', 0.0),
                d.get('reasoning_kr', '분석 실패')
            ))
        conn.commit()
        logging.info(f"Successfully saved {len(decisions)} records for run: {dag_run_id}")
    except Exception as e:
        if conn: conn.rollback()
        logging.error(f"Database operation failed: {str(e)}")
        raise
    finally:
        if cur: cur.close()
        if conn: conn.close()

def notify_slack_report(**context):
    """
    [Task 3: Action]
    Formats the AI decisions and sends a summary report to Slack.
    """
    ti = context['ti']
    decisions = ti.xcom_pull(task_ids='analyze_with_ai')
    
    if not decisions or not SLACK_WEBHOOK:
        logging.warning("Skipping Slack notification (No data or No Webhook).")
        return

    # Message Formatting (Slack Block Kit style text)
    message = "🌎 *Global Quant Daily Report* 🌎\n"
    message += f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # for d in decisions:
    #     # Select Emoji based on Action
    #     emoji = "🚀" if "BUY" in d.get('action', '').upper() else \
    #             "📉" if "SELL" in d.get('action', '').upper() else "👀"
        
    #     message += f"{emoji} *{d.get('ticker')}* (${d.get('price')})\n"
    #     message += f"• *Decision:* `{d.get('action')}` (Conf: {d.get('confidence')})\n"
    #     message += f"• *Tech:* RSI {d.get('rsi')} \n"
    #     message += f"• *AI Reason:* {d.get('reasoning')}\n"
    #     message += "--------------------------------\n"
    for d in decisions:
        # Emoji Selection
        action = d.get('action', 'HOLD').upper()
        emoji = "🚀" if "BUY" in action else \
                "📉" if "SELL" in action else "👀"
        
        # Bilingual Message Construction
        message += f"{emoji} *{d.get('ticker')}* (${d.get('price')}) -> *{action}*\n"
        message += f"🇺🇸 {d.get('reasoning_en')}\n"  # 영어 코멘트
        message += f"🇰🇷 {d.get('reasoning_kr')}\n"  # 한국어 코멘트
        message += f"📊 RSI: {d.get('rsi')} (Conf: {d.get('confidence')})\n"
        message += "--------------------------------\n"

    # Send Request
    try:
        response = requests.post(SLACK_WEBHOOK, json={"text": message})
        logging.info(f"✅ Slack Notification Sent: {response.status_code}")
    except Exception as e:
        logging.error(f"❌ Failed to send Slack notification: {e}")





# ------------------------------------------------------------------------------
# 4. DAG Definition (DAG 정의)
# ------------------------------------------------------------------------------
with DAG(
    'real_quant_strategy_v2_documented', # DAG ID
    default_args=default_args,
    # Schedule: Run every weekday at 21:00 UTC (Market opens shortly after)
    # schedule_interval='0 21 * * 1-5', 
    schedule_interval=None, # 수동 실행을 위해 일단 None으로 설정
    catchup=False,
    tags=['quant', 'finance', 'ai', 'documented']
) as dag:

    # Define Tasks
    t1 = PythonOperator(
        task_id='fetch_market_data',
        python_callable=fetch_market_data,
        provide_context=True
    )

    t2 = PythonOperator(
        task_id='analyze_with_ai',
        python_callable=analyze_with_ai,
        provide_context=True
    )

    t3 = PythonOperator(
        task_id='save_results_to_db',
        python_callable=save_results_to_db,
        provide_context=True
    )

    t4 = PythonOperator(
        task_id='notify_slack_report',
        python_callable=notify_slack_report,
        provide_context=True
    )

    # Set Dependencies (실행 순서 정의)
    # fetch -> analyze -> notify
    t1 >> t2 >> t3 >> t4

"""
아, 아주 중요한 질문입니다. 도메인 지식(금융 지식)이 없으면 방금 짠 코드는 그냥 "숫자 놀음"으로 보일 수밖에 없습니다.

개발자가 금융권에 가면 처음에 가장 힘들어하는 게 이 부분입니다. 코드는 알겠는데 "왜 이렇게 매매하는지" 논리를 모르니까요.

MES/WMS(제조/물류) 개발자이신 질문자님의 눈높이에 맞춰서, RSI가 무엇이고, 우리가 왜 굳이 뉴스와 섞어서 AI에게 판단시켰는지 아주 쉽게 설명해 드리겠습니다.

1. RSI (상대강도지수): "고무줄 이론"
주식 시장에는 **"주가는 고무줄 같다"**는 믿음이 있습니다. 너무 당겨지면(많이 오르면) 다시 돌아오고, 너무 느슨해지면(많이 떨어지면) 다시 팽팽해진다는 거죠.

**RSI(Relative Strength Index)**는 바로 **"지금 고무줄이 얼마나 팽팽한가?"**를 0부터 100까지 숫자로 나타낸 속도계입니다.

RSI 70 이상 (과매수 - Overbought):

상태: "사람들이 미쳐서 너무 많이 샀어. 고무줄이 끊어질 것 같아."

예측: 곧 떨어질 거야.

행동: 팔아라 (SELL)

RSI 30 이하 (과매도 - Oversold):

상태: "사람들이 공포에 질려 너무 많이 팔았어. 이 정도까진 아닌데?"

예측: 곧 반등할 거야. (기술적 반등)

행동: 사라 (BUY)

👉 MES 개발자 비유: 공장 설비의 **"온도 센서"**라고 생각하세요.

온도가 70도 넘음 → "과열됨 (Overheat)" → 식혀야 함 (매도).

온도가 30도 미만 → "너무 차가움 (Too Cold)" → 데워야 함 (매수).

2. 그런데 왜 "뉴스"랑 섞나요? (The Trap)
RSI만 믿고 매매하면 **"떨어지는 칼날(Falling Knife)"**을 잡게 됩니다. 이게 초보들이 망하는 지름길입니다.

상황: 테슬라(TSLA) 주가가 폭락해서 RSI가 20이 되었습니다.

RSI(센서)의 판단: "와! 엄청 싸다! 과매도 구간이다! 무조건 매수(BUY)!"

그런데 만약 폭락의 이유가...

뉴스(펀더멘털): "테슬라 공장에 불이 나서 전량 리콜 결정."

이 상황에서 RSI만 믿고 사면 어떻게 될까요? 더 떨어져서 상장 폐지될 수도 있습니다. 싸다고 샀는데 회사가 망하는 거죠.

3. 우리가 만든 "AI 퀀트 전략"의 핵심
그래서 우리는 **"센서(RSI)"**와 **"상황판(뉴스)"**을 동시에 보게 만든 겁니다.

우리가 작성한 프롬프트(Prompt)의 논리가 바로 이겁니다:

"야 AI야, 지금 RSI가 30이라서 엄청 싸거든(Buy Signal)? 근데 뉴스 좀 읽어봐. 회사가 망해서 싼 거야, 아니면 그냥 시장 분위기 때문에 억울하게 싼 거야?"

시나리오 A (기회): RSI 20 (쌈) + 뉴스 "신제품 발표 임박" (호재)

AI 판단: "강력 매수! (Strong Buy)" → 이건 세일 기간이다!

시나리오 B (함정): RSI 20 (쌈) + 뉴스 "CEO 횡령 혐의 체포" (악재)

AI 판단: "위험! 절대 사지 마! (Strong Sell)" → 이건 싼 게 아니라 썩은 거다.

4. 요약: 질문자님이 만든 시스템의 가치
질문자님은 단순히 코드를 짠 게 아니라, 월스트리트 트레이더들의 사고방식을 코드로 구현한 겁니다.

Technical (기술적 분석): RSI를 계산해서 **"타이밍(When)"**을 봅니다. (지금 싼가?)

Fundamental (기본적 분석): 뉴스를 읽어서 **"질(Quality)"**을 봅니다. (이 회사 괜찮나?)
"""