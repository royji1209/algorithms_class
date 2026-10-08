FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# requirements.txt 파일이 루트에 실제로 존재하는지 확인
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

