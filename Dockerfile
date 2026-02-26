FROM python:3.11-slim

WORKDIR /app

COPY ai-dental-receptionist/backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ai-dental-receptionist/backend .

EXPOSE 8000

CMD ["python", "app.py"]