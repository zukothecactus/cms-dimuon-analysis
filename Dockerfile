FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# UV for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy the dependency files first to leverage Docekr layering cache
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --locked --no-dev

COPY . .

ENTRYPOINT ["uv", "run", "python", "-m", "dimuon.cli"]

CMD ["--help"]