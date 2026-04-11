FROM python:3.13-slim

ENV PORT=8080
ENV QUEST_DB_PATH=/app/data/quest.db

WORKDIR /app

COPY api/ /app/api/
COPY quantum-engine/ /app/quantum-engine/

RUN mkdir -p /app/data

WORKDIR /app/api
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
