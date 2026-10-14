# 1. 경량화된 Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 2. 파이썬 버퍼링 비활성화 및 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 3. 작업 디렉터리 생성 및 의존성 복사/설치
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사
COPY . .

# 5. gunicorn을 사용해 프로덕션 서버 실행 (Cloud Run 표준 구성)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
