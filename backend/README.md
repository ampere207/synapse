"""Backend README"""
# Synapse Backend

FastAPI backend for Synapse - AI Meeting Intelligence Platform.

## Tech Stack

- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Realtime and queue infrastructure
- **Qdrant** - Vector database for embeddings
- **Gemini API** - AI model for intelligence extraction
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

## Project Structure

```
backend/
├── app/
│   ├── api/               # API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── organizations.py  # Organizations
│   │   └── meetings.py   # Meetings
│   ├── core/             # Core utilities
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Database setup
│   │   └── security.py   # JWT and hashing
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── realtime/         # WebSocket and realtime
│   ├── ai_pipeline/      # AI processing
│   │   ├── provider.py   # AI provider abstraction
│   │   ├── queue.py      # Async processing queue
│   │   └── batching.py   # Transcript batching
│   ├── workers/          # Background workers
│   └── main.py          # FastAPI app
├── migrations/           # Database migrations
├── Dockerfile
└── requirements.txt
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- Docker (for containerized setup)

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Docker Setup

```bash
# From root directory
docker-compose up backend

# API will be available at http://localhost:8000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Organizations
- `POST /api/organizations/` - Create organization
- `GET /api/organizations/{org_id}` - Get organization

### Meetings
- `POST /api/organizations/{org_id}/meetings` - Create meeting
- `GET /api/organizations/{org_id}/meetings/{meeting_id}` - Get meeting
- `PATCH /api/organizations/{org_id}/meetings/{meeting_id}` - Update meeting

### WebSocket
- `WS /ws/meetings/{org_id}/{meeting_id}?token={jwt_token}` - Realtime meeting updates

## Configuration

Environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://synapse:synapse@localhost:5432/synapse

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini API
GEMINI_API_KEY=your-api-key

# Qdrant
QDRANT_URL=http://localhost:6333

# Frontend
FRONTEND_URL=http://localhost:3000

# Debug
DEBUG=True
```

## AI Pipeline

The backend implements a staged asynchronous AI processing system:

1. **Realtime Layer**: Transcript chunks stream to frontend without AI processing
2. **Batching Layer**: Chunks accumulate into semantic windows
3. **Async Queue**: Batches queued for AI processing (Redis-based)
4. **Processing**: AI extraction happens asynchronously
5. **Updates**: Results sent back incrementally to frontend

This minimizes Gemini API calls and costs while maintaining realtime responsiveness.

## Database Models

- **User** - User accounts
- **Organization** - Workspace/organization
- **OrganizationMember** - Member roles and permissions
- **Meeting** - Meeting sessions
- **Transcript** - Full meeting transcript
- **TranscriptChunk** - Streamed transcript segments
- **GraphNode** - Intelligence graph nodes
- **GraphEdge** - Graph relationships
- **Decision** - Extracted decisions
- **ActionItem** - Extracted action items
- **AIProcessingJob** - Async AI jobs
- **UploadedFile** - File uploads

## WebSocket Messages

### Client to Server

```json
{
  "type": "transcript_chunk",
  "speaker": "John",
  "text": "Let's discuss the Q4 roadmap",
  "timestamp": 120,
  "sequence_number": 5
}
```

```json
{
  "type": "graph_update",
  "nodes": [...],
  "edges": [...]
}
```

### Server to Client

```json
{
  "type": "user_joined",
  "user_id": "...",
  "username": "..."
}
```

```json
{
  "type": "decision_extracted",
  "title": "...",
  "description": "..."
}
```

## Development

```bash
# Run tests
pytest

# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Deployment

For production:

1. Update `SECRET_KEY` with strong random value
2. Set `DEBUG=False`
3. Configure database with production PostgreSQL
4. Set up Redis cluster for reliability
5. Configure Gemini API key
6. Use environment-specific settings
7. Enable HTTPS/TLS
8. Set up monitoring and logging
