FROM python:3.11-slim
WORKDIR /app
RUN pip install --upgrade pip
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only main --no-root --no-interaction --no-ansi
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
