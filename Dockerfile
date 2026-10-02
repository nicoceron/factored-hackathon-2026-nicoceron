FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable
RUN useradd --create-home --uid 10001 appuser && mkdir /state && chown appuser:appuser /state
ENV CLARO_DB=/state/claro.sqlite
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/healthz',timeout=3)"
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn factored_banking.api:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log"]
