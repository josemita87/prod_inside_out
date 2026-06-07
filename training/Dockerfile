FROM python:3.11-slim

# Bring in the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

# Add src to the PYTHONPATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# uv: compile bytecode and copy packages into the environment
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install necessary dependencies (openjdk required by H2O)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    curl \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo (needed to build some native wheels)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy only the dependency manifests first to leverage layer caching
COPY pyproject.toml uv.lock /app/

# Install dependencies into the project environment
RUN uv sync --frozen --no-dev

# Copy the rest of the source code into the container
COPY . /app

# Expose the H2O web UI / REST port
EXPOSE 54321

# Define the command to run the application
CMD ["uv", "run", "--no-sync", "python", "/app/src/main.py"]
