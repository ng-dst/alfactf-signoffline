FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn gevent

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=3000
ENV FLASK_ENV=production

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:3000", "--worker-connections", "1000", "-k", "gevent", "app:create_app()"]
