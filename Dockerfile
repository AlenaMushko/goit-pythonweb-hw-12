FROM python:3.12-slim

ENV APP_HOME=/hw_10-app-container
ENV APP_PORT=8003

WORKDIR $APP_HOME

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8003

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8003}"]