# ==============================================================================
# 1. Base Image (기초 공사)
# 과거의 문제: Python 3.8을 써서 최신 라이브러리(yfinance)가 문법 에러를 냄.
# 해결책: Python 3.11이 설치된 최신 Airflow 2.10.3 버전으로 기반을 교체함.
# ==============================================================================
FROM apache/airflow:2.10.3-python3.11

# ==============================================================================
# 2. System Dependencies (OS 레벨 설치)
# 설명: Python 라이브러리 중(pandas, numpy 등)은 C언어로 된 코드를 컴파일해야 할 때가 있음.
# 이때 gcc 같은 컴파일러가 없으면 설치 도중 에러가 터짐.
# 해결책: root 권한으로 잠시 바꿔서 필수 컴파일 도구(build-essential)를 미리 깔아둠.
# ==============================================================================
USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# 3. User Switch (보안 설정)
# 설명: 계속 root로 실행하면 보안상 위험함. 다시 일반 유저(airflow)로 돌아옴.
# ==============================================================================
USER airflow

# ==============================================================================
# 4. Dependency Definition (주문서 복사)
# 설명: 내 컴퓨터에 있는 requirements.txt를 도커 컨테이너 안으로 집어넣음.
# ==============================================================================
COPY requirements.txt /requirements.txt

# ==============================================================================
# 5. Pip Install with Constraints (핵심 해결책: 족보 사용)
# 과거의 문제: 그냥 pip install 하면, Airflow가 쓰는 라이브러리와 내가 설치한 게 버전 충돌남.
# 해결책: '--constraint' 옵션을 사용.
#        "Airflow 공식 팀이 검증한 버전 조합(Constraints)"을 참조해서
#        서로 싸우지 않는 안전한 버전만 골라서 설치하도록 강제함.
# ==============================================================================
RUN pip install --no-cache-dir \
    -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.11.txt"