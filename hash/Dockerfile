FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# 캐싱 효율을 위해 종속성을 먼저 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY . .

# Gunicorn WSGI 서버 실행 (Cloud Run 표준 포트 바인딩)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
