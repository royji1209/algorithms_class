# 경량화된 Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 표준 출력 버퍼링 비활성화 (Cloud Logging 실시간 확인용)
ENV PYTHONUNBUFFERED=1

# 작업 디렉터리 설정
WORKDIR /app

# 종속성 파일 복사 및 설치 (캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Cloud Run 기본 포트 환경변수 설정
ENV PORT=8080

# Gunicorn WSGI 서버 실행 (동시 요청 처리 최적화)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

