FROM python:3.13-slim

ENV PORT=8080

WORKDIR /app

COPY api/ /app/api/
COPY risk-engine/ /app/risk-engine/

WORKDIR /app/api
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
