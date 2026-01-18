# ------------------------------------------------------------------------------
# 1. Base Image
# ------------------------------------------------------------------------------
# We start with a lightweight Python 3.11 Linux image.
# 우리는 가벼운 리눅스 기반 파이썬 3.11 이미지로 시작합니다.
FROM python:3.11-slim

# ------------------------------------------------------------------------------
# 2. Working Directory
# ------------------------------------------------------------------------------
# Set the working directory inside the container to /app.
# 컨테이너 내부의 작업 폴더를 /app으로 설정합니다.
WORKDIR /app

# ------------------------------------------------------------------------------
# 3. Dependencies
# ------------------------------------------------------------------------------
# Copy the requirements file first to leverage Docker cache.
# 도커 캐시 기능을 활용하기 위해 라이브러리 목록 파일만 먼저 복사합니다.
COPY requirements.txt .

# Install Python libraries.
# 파이썬 라이브러리들을 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------------------------
# 4. Copy Code
# ------------------------------------------------------------------------------
# Copy all the remaining code from the local folder to the container.
# 나머지 모든 소스 코드를 컨테이너 안으로 복사합니다.
COPY . .

# ------------------------------------------------------------------------------
# 5. Runtime Command
# ------------------------------------------------------------------------------
# Start the Uvicorn server (FastAPI).
# host 0.0.0.0 is crucial for Docker networking.
# FastAPI 서버를 실행합니다. 0.0.0.0 설정은 도커 외부 접속을 위해 필수입니다.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]