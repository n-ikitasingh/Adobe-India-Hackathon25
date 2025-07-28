# Use lightweight Python base image
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# Install required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libpoppler-cpp-dev \
    && pip install --no-cache-dir PyMuPDF PyPDF2

# Copy your extractor script into container
COPY . .

# Run the script
CMD ["python", "process_pdfs.py"]
