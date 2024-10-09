# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn gevent

# Copy the rest of the application code into the container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=3000
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 80

# Health check
HEALTHCHECK --interval=120s --retries=3 CMD curl --fail http://127.0.0.1:3000 || exit 1

# Use a more efficient command to run the Flask application
CMD ["gunicorn", "-b", "0.0.0.0:3000", "--worker-connections", "1000", "-k", "gevent", "app:create_app()"]
