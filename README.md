# Jurema Chatbot API

A FastAPI-based chatbot using the Jurema-7B model with Redis for session management and PostgreSQL for data persistence.

## Features

- **FastAPI** web framework for high performance
- **Jurema-7B** model integration via Transformers and LangChain
- **Redis** for session management and conversation history caching
- **PostgreSQL** for persistent data storage
- **Docker** containerization for easy deployment
- **uv** for fast dependency management

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Start all services:
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`

### Manual Setup

1. Install dependencies with uv:
   ```bash
   uv sync
   ```

2. Start PostgreSQL and Redis services locally

3. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis URLs
   ```

4. Run the application:
   ```bash
   uv run python -m src.chatbot_api.api.main
   ```

## API Endpoints

- `GET /` - Root endpoint
- `POST /chat` - Send a message to the chatbot
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation

## Example Usage

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Olá, como você está?", "session_id": "test-session"}'
```

## Project Structure

```
src/chatbot_api/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── main.py          # FastAPI application
├── core/
│   ├── __init__.py
│   └── config.py        # Configuration settings
├── models/
│   ├── __init__.py
│   ├── schemas.py       # Pydantic models
│   └── database.py      # SQLAlchemy models
├── services/
│   ├── __init__.py
│   └── chatbot.py       # LangChain + Jurema-7B integration
└── database/
    ├── __init__.py
    └── database.py      # PostgreSQL setup
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `MODEL_NAME` - Hugging Face model name (default: Jurema-br/Jurema-7B)
- `MAX_NEW_TOKENS` - Maximum tokens for model generation
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `DEBUG` - Enable debug mode (default: false)