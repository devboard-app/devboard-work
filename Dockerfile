FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

RUN SECRET_KEY=dummy INTERNAL_API_KEY=dummy JWT_SECRET=dummy CORE_SERVICE_URL=dummy EMAIL_SERVICE_URL=dummy DB_NAME=dummy DB_USER=dummy DB_PASSWORD=dummy python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate && uvicorn work.asgi:application --host 0.0.0.0 --port 8000"]
