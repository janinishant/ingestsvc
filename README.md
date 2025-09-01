# Ingest Service

FastAPI service for securely ingesting raw logs from fluent-bit log collector.

## Setup

### Using Docker

```bash
docker build -t ingestsvc .
docker run -p 8000:8000 ingestsvc
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check
- `GET /api/v1/ready` - Readiness check
- `POST /api/v1/ingest` - Ingest logs
- `POST /api/v1/ingest/batch` - Ingest batch logs

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black app/
isort app/

# Lint code
ruff check app/

# Type checking
mypy app/
```