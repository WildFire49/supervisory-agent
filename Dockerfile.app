# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /code
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code and other necessary files
COPY ./app /code/app
COPY ./data /code/data
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini
COPY ./start.sh /code/start.sh

# Make startup script executable
RUN chmod +x /code/start.sh

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with migrations
CMD ["/code/start.sh"]
