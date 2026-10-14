FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# 종속성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# Gunicorn WSGI 실행
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
