# Dockerfile
# Multi-stage build for the portfolio optimisation tool
# Base image with Python 3.13 (official slim image)
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Copy only the necessary files for building
COPY pyproject.toml README.md ./
COPY portfolio_optimization/ ./portfolio_optimization/

# Install build dependencies (pip, build-essential optional)
RUN pip install --upgrade pip && \
    pip install .

# Second stage – runtime image (smaller)
FROM python:3.13-slim

WORKDIR /app

# Copy installed package from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Ensure the entrypoint script is available
ENV PATH="/usr/local/bin:${PATH}"

# Default command – show help
ENTRYPOINT ["portfolio-optimize", "--help"]
