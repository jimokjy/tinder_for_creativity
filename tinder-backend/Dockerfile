# Простой однослойный образ на Python — для FastAPI этого достаточно,
# многоступенчатая сборка тут не нужна (в отличие от фронтенда).
FROM python:3.12-slim

WORKDIR /app

# Ставим зависимости отдельным слоем — пересобирается только когда
# меняется requirements.txt, а не при каждом изменении кода.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
