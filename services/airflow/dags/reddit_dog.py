"""
================================================================================
Project: Reddit Meme Stock Trader
File: reddit_dag.py
Description: 
    English: This DAG orchestrates the data pipeline. It extracts Reddit posts 
             and sends them to the AI API Server for sentiment analysis.
    Korean: 이 DAG는 데이터 파이프라인을 조율합니다. 레딧 게시글을 수집(Extract)하여
            AI API 서버로 전송해 감성 분석(Analysis)을 수행합니다.
Author: User (Meme Stock Engineer)
================================================================================
"""

import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import json
import logging
import psycopg2

# ------------------------------------------------------------------------------
# 1. Configuration (환경 설정)
# ------------------------------------------------------------------------------

# English: Service Discovery URL. 
# Inside Docker Compose, we use the service name 'api-server' as the hostname.
# Korean: 서비스 디스커버리 URL입니다. 
# 도커 컴포즈 내부에서는 'api-server'라는 서비스 이름을 호스트 주소로 사용합니다.
# (localhost를 쓰면 Airflow 컨테이너 자기 자신을 찾게 되어 에러가 납니다.)
API_URL = "http://api-server:8000/analyze"

DB_CONN_INFO = {
    "host": "postgres",
    "port": "5432",
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow"
}

# English: Load Slack Webhook URL from environment variable.
# Korean: 환경 변수에서 슬랙 웹훅 URL을 안전하게 가져옵니다.
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

# English: Default arguments applied to all tasks in this DAG.
# Korean: 이 DAG의 모든 태스크(Task)에 공통으로 적용되는 기본 설정값입니다.
default_args = {
    'owner': 'airflow',
    
    # English: If True, wait for the previous run to complete before starting.
    # Korean: True일 경우, 이전 회차 실행이 끝나야만 다음 회차를 실행합니다.
    'depends_on_past': False,
    
    # English: The logical start date of the DAG. 
    # Korean: DAG의 논리적 시작 날짜입니다. (이 날짜 이후부터 스케줄링됨)
    'start_date': datetime(2024, 1, 1),
    
    # English: Disable email alerts for simplicity.
    # Korean: 간단한 실습을 위해 이메일 알림은 끕니다.
    'email_on_failure': False,
    'email_on_retry': False,
    
    # English: Retry logic for robustness. If a task fails, try 1 more time.
    # Korean: 안정성을 위한 재시도 로직입니다. 실패 시 1회 더 시도합니다.
    'retries': 1,
    
    # English: Wait 5 minutes before retrying.
    # Korean: 재시도하기 전에 5분을 기다립니다.
    'retry_delay': timedelta(minutes=5),
}

# ------------------------------------------------------------------------------
# 2. Python Functions (실제 작업 함수)
# ------------------------------------------------------------------------------

def fetch_reddit_data(**context):
    """
    Task 1: Extract Data (데이터 수집)
    
    English:
        Fetches raw text data from Reddit (currently mocked).
        Returns the data, which is automatically pushed to XCom for the next task.
    Korean:
        레딧에서 원본 텍스트 데이터를 가져옵니다 (현재는 가짜 데이터 사용).
        반환된 데이터는 자동으로 XCom(Airflow 내부 데이터 저장소)에 저장되어
        다음 태스크에서 사용할 수 있게 됩니다.
    """
    logging.info("Starting to fetch data from Reddit...")
    
    # English: Mock data simulation. Later, we will use 'praw' library here.
    # Korean: 가짜 데이터 시뮬레이션입니다. 나중에 여기에 'praw' 라이브러리를 연결합니다.
    mock_data = [
        "GME is going to the moon! 🚀 (Gamestop)",
        "NVIDIA earning calls are looking great. AI is the future.",
        "I lost all my money on Tesla puts. Elon why?",
        "Apple vision pro is too expensive but technology is amazing."
    ]
    
    logging.info(f"Successfully fetched {len(mock_data)} posts.")
    
    # English: The return value is stored in Airflow's XCom (Cross-Communication).
    # Korean: 이 함수의 리턴값은 Airflow의 XCom(교차 통신) 저장소에 저장됩니다.
    return mock_data

def analyze_data(**context):
    """
    Task 2: Transform & Load (분석 및 저장)
    | 문법         | 의미        | 타입    |
    | ---------- | --------- | ----- |
    | `*args`    | 위치 인자 묶음  | tuple |
    | `**kwargs` | 키워드 인자 묶음 | dict  |

    English:
        Pulls data from the previous task (XCom) and sends it to the AI API.
    Korean:
        이전 태스크(XCom)에서 데이터를 가져와 AI API 서버로 전송합니다.
    """
    # English: Access the Task Instance (ti) to pull data from XCom.
    # Korean: 태스크 인스턴스(ti) 객체를 통해 XCom에서 데이터를 당겨옵니다(Pull).
    ti = context['ti']
    reddit_posts = ti.xcom_pull(task_ids='fetch_reddit_data')
    
    if not reddit_posts:
        raise ValueError("No data received from Reddit! (데이터가 없습니다)")

    logging.info(f"Sending {len(reddit_posts)} posts to AI Brain at {API_URL}...")

    results = []
    
    for post in reddit_posts:
        try:
            # English: Send HTTP POST request to the API Server Container.
            # Korean: API 서버 컨테이너로 HTTP POST 요청을 보냅니다.
            payload = {"text": post}
            response = requests.post(API_URL, json=payload)
            
            # English: Check if the request was successful (200 OK).
            # Korean: 요청이 성공했는지(200 OK) 확인합니다.
            response.raise_for_status()
            
            analysis_result = response.json()
            logging.info(f"Analysis Result: {analysis_result}")
            results.append(analysis_result)
            
        except Exception as e:
            # English: Log the error but continue processing other posts.
            # Korean: 에러를 기록하되, 다른 게시글 처리는 계속 진행합니다.
            logging.error(f"Failed to analyze post: {post}. Error: {e}")

    logging.info(f"Total Analysis Completed: {len(results)} items.")
    return results

def notify_slack(**context):
    """
    Task 3: Send Notification (슬랙 알림 전송)
    
    English: Formats the analysis results and sends a message to Slack.
    Korean: 분석 결과를 포맷팅하여 슬랙으로 메시지를 전송합니다.
    """
    ti = context['ti']
    # English: Pull analysis results from the previous task (analyze_data).
    # Korean: 이전 태스크(AI 분석)의 결과를 가져옵니다.
    analysis_results = ti.xcom_pull(task_ids='analyze_data')
    
    if not analysis_results:
        logging.info("No results to report.")
        return

    if not SLACK_WEBHOOK:
        raise ValueError("Slack Webhook URL is missing in .env!")

    # English: Create a rich message format (Blocks).
    # Korean: 가독성 좋은 메시지 포맷(블록)을 만듭니다.
    message_text = "🚀 *AI Meme Stock Analysis Report* 🚀\n\n"
    
    for item in analysis_results:
        emoji = "🟢" if item.get('action') == "BUY" else "🔴" if item.get('action') == "SELL" else "⚪"
        
        message_text += f"{emoji} *{item.get('ticker')}*: {item.get('action')} (Confidence: {item.get('confidence')})\n"
        message_text += f"> 🗣 {item.get('reasoning')}\n"
        message_text += "---\n"

    payload = {"text": message_text}

    # Send to Slack
    response = requests.post(SLACK_WEBHOOK, json=payload)
    logging.info(f"Slack Notification Sent: {response.status_code}")


# ------------------------------------------------------------------------------
# 3. DAG Definition (워크플로우 정의)
# ------------------------------------------------------------------------------

with DAG(
    'reddit_meme_stock_pipeline',       # English: Unique ID of the DAG
    default_args=default_args,          # English: Apply default args defined above
    description='A pipeline to analyze Reddit stocks using AI',
    
    # English: Schedule to run once a day. (Cron expression or timedelta)
    # Korean: 하루에 한 번 실행되도록 스케줄링합니다.
    schedule_interval=timedelta(days=1),
    
    # English: If False, do not run for past dates since start_date.
    # Korean: False로 설정하면, 시작 날짜부터 오늘까지 밀린 작업을 한꺼번에 실행하지 않습니다.
    catchup=False,
    
    tags=['meme', 'stock', 'ai'],
) as dag:

    # --------------------------------------------------------------------------
    # Task Definitions (작업 정의)
    # --------------------------------------------------------------------------
    
    # Task 1: Fetch Data
    t1 = PythonOperator(
        task_id='fetch_reddit_data',     # English: Unique ID for this task
        python_callable=fetch_reddit_data, # English: The Python function to execute
        provide_context=True,            # English: Inject Airflow context (needed for XCom)
    )

    # Task 2: Analyze Data
    t2 = PythonOperator(
        task_id='analyze_data',
        python_callable=analyze_data,
        provide_context=True,
    )

    t3 = PythonOperator(
        task_id='notify_slack',
        python_callable=notify_slack,
        provide_context=True,
    )

    # --------------------------------------------------------------------------
    # Dependency Definition (순서 연결)
    # --------------------------------------------------------------------------
    
    # English: t1 must complete successfully before t2 starts.
    # Korean: t1(수집)이 성공적으로 끝나야 t2(분석)가 시작됩니다.
    t1 >> t2 >> t3

    