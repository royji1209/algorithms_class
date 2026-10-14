# 1. 경량화된 Python 3.11 슬림 이미지
FROM python:3.11-slim

# 2. 환경변수 설정
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 3. 작업 디렉터리 지정
WORKDIR /app

# 4. bin 폴더 안의 requirements.txt 복사 및 패키지 설치
COPY bin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. bin 폴더 안의 소스 파일들(main.py 등)을 컨테이너 /app으로 복사
COPY bin/ .

# 6. gunicorn 실행
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
