# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install required Python libraries
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Add entrypoint script to handle both monitoring and query tools
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Copy the Python scripts to the container
COPY monitor.py query.py usage.py initial-run.py find-unused.py /app/

# Environment variables for database configuration
ENV DB_HOST=localhost
ENV DB_NAME=docker_monitor
ENV DB_USER=root
ENV DB_PASSWORD=password

# Optional support for Docker secrets (set paths)
ENV DB_HOST_SECRET=/run/secrets/db_host
ENV DB_NAME_SECRET=/run/secrets/db_name
ENV DB_USER_SECRET=/run/secrets/db_user
ENV DB_PASSWORD_SECRET=/run/secrets/db_password

# Entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

