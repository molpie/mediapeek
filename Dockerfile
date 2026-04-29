FROM python:3.13-alpine3.23 AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    python-multipart

FROM python:3.13-alpine3.23 AS runtime

RUN apk add --no-cache ffmpeg \
    && apk cache clean 2>/dev/null || true

RUN addgroup -S mediapeek && adduser -S -G mediapeek mediapeek

COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /app

COPY app/main.py  /app/main.py
COPY static/      /app/static/

RUN chown -R mediapeek:mediapeek /app

USER mediapeek

ENV MEDIA_ROOT=/media \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
