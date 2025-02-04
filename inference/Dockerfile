# Use Python slim image
FROM python:3.11-slim

# Add src to the PYTHONPATH
ENV PYTHONPATH=/app

ENV PYTHONBUFFERED=1

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    curl \
    openjdk-17-jre-headless \
    && pip install poetry==1.8.3 \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
# Set the working directory
WORKDIR /app

# Copy only the poetry files first to leverage caching
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry install --no-interaction --no-ansi --verbose


# Copy the rest of the application code
COPY . /app

# Run the application
CMD ["poetry", "run", "python", "src/main.py"]