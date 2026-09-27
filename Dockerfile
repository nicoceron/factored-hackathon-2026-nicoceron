FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable
RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "factored_banking.api:app", "--host", "0.0.0.0", "--port", "8000"]
