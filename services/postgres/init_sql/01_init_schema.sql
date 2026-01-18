-- 1. 주식 분석 메인 로그 (수행 이력 관리용)
CREATE TABLE IF NOT EXISTS market_analysis_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50),          -- Airflow의 Dag Run ID (추적용)
    ticker VARCHAR(10) NOT NULL,
    price_at_run FLOAT,          -- 실행 시점 가격
    rsi_value FLOAT,
    ai_decision VARCHAR(20),      -- BUY, SELL, HOLD
    ai_confidence FLOAT,
    analysis_report_kr TEXT,      -- 한국어 분석 내용
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 레딧 감성 분석 로그
CREATE TABLE IF NOT EXISTS reddit_sentiment_log (
    id SERIAL PRIMARY KEY,
    post_id VARCHAR(20) UNIQUE,
    subreddit VARCHAR(50),
    title TEXT,
    sentiment_score FLOAT,        -- -1.0 ~ 1.0 (부정 ~ 긍정)
    sentiment_label VARCHAR(10),  -- BULLISH, BEARISH
    ai_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 시스템 운영 로그 (성능 및 장애 모니터링용)
CREATE TABLE IF NOT EXISTS system_job_log (
    id SERIAL PRIMARY KEY,
    dag_name VARCHAR(100),
    task_name VARCHAR(100),
    status VARCHAR(20),           -- SUCCESS, FAIL
    execution_time INTERVAL,      -- 실행 소요 시간
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 설정 (운영 관점의 필수 요소)
CREATE INDEX idx_market_ticker ON market_analysis_log(ticker);
CREATE INDEX idx_reddit_created ON reddit_sentiment_log(created_at);