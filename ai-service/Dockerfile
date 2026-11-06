FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src src
RUN pip install --no-cache-dir .
RUN useradd --system --uid 10001 app && chown -R app:app /app
USER app
EXPOSE 8090
CMD ["uvicorn", "booktalk_ai.api:app", "--host", "0.0.0.0", "--port", "8090"]
