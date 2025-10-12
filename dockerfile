# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file (if you don’t have, we’ll generate requirements.txt)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose the Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
