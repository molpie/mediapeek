FROM python:3.12-alpine

RUN apk add --no-cache ffmpeg

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart

COPY app/main.py /app/main.py
COPY static/ /app/static/

ENV MEDIA_ROOT=/media

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
