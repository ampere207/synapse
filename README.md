"""Main project README"""
# Synapse

**AI Meeting Intelligence Platform**

Transform meetings, transcripts, and discussions into living operational intelligence graphs.

## 🎯 What is Synapse?

Synapse is **NOT**:
- A transcription tool
- An AI summarizer
- A chatbot

Synapse **IS**:
- An operational intelligence graph system
- A platform for execution continuity
- A visualization system for organizational memory

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.12+ (for local backend development)
- API keys for Gemini and speech-to-text services

### Start with Docker Compose

```bash
# Clone repository
cd synapse

# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your-gemini-key
DEEPGRAM_API_KEY=your-deepgram-key
EOF

# Start all services
docker-compose up

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# PostgreSQL: localhost:5432
# Redis: localhost:6379
# Qdrant: http://localhost:6333
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Start server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

## 📁 Project Structure

```
synapse/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile
├── frontend/            # Next.js frontend
│   ├── app/            # App router pages
│   ├── src/            # Source code
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml   # Docker orchestration
└── README.md
```

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Next.js 15 (TypeScript, React)
- TailwindCSS
- shadcn/ui
- Zustand (state management)
- React Query
- React Flow (graph visualization)

**Backend:**
- FastAPI (Python 3.12+)
- PostgreSQL
- Redis (Pub/Sub, queuing)
- Qdrant (vector search)

**AI/ML:**
- Gemini API
- Deepgram or AssemblyAI (STT)

**Deployment:**
- Docker Compose

### Core Features

- ✅ User authentication with JWT
- ✅ Organization/workspace system
- ✅ Meeting session management
- ✅ Live transcript streaming via WebSocket
- ✅ Transcript/summary uploads
- ✅ Async AI processing pipeline
- ✅ Graph visualization
- ✅ Multi-user collaboration
- ✅ Multi-tenant isolation
- ✅ Realtime updates

### AI Pipeline

```
Realtime Transcript Stream
         ↓
    Batching Window (120s or 1000 tokens)
         ↓
  Redis Processing Queue
         ↓
  Async AI Worker (Gemini API)
         ↓
Extract: Decisions, Actions, Topics
         ↓
Build: Relationship Graphs
         ↓
Incremental Graph Updates → Frontend
```

## 🔐 Security & Multi-Tenancy

- JWT-based authentication
- Row-level security (RLS) in database
- Organization isolation at API level
- WebSocket token validation
- Secure file uploads to Supabase

## 📊 Database Schema

Core entities:
- **Users** - User accounts
- **Organizations** - Workspaces
- **Meetings** - Meeting sessions
- **Transcripts** - Speech-to-text output
- **Graphs** - Intelligence graphs
- **Decisions** - Extracted decisions
- **ActionItems** - Extracted actions
- **AIProcessingJobs** - Async job tracking

## 🔌 API Overview

### REST Endpoints

```
POST   /api/auth/register           - Register user
POST   /api/auth/login              - Login user
POST   /api/organizations/          - Create organization
GET    /api/organizations/{id}      - Get organization
POST   /api/organizations/{id}/meetings           - Create meeting
GET    /api/organizations/{id}/meetings/{mid}    - Get meeting
PATCH  /api/organizations/{id}/meetings/{mid}    - Update meeting
```

### WebSocket

```
WS /ws/meetings/{org_id}/{meeting_id}?token={jwt}
```

Real-time message types:
- `transcript_chunk` - Realtime transcript
- `graph_update` - Graph visualization updates
- `decision_extracted` - AI-extracted decisions
- `action_extracted` - AI-extracted actions
- `user_joined` / `user_left` - Presence

## 🔧 Configuration

Create `.env` file in root:

```env
# Database
DATABASE_URL=postgresql://synapse:synapse@localhost:5432/synapse

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=dev-secret-key-change-in-production

# APIs
GEMINI_API_KEY=your-api-key
DEEPGRAM_API_KEY=your-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Debug
DEBUG=True
```

## 📝 Usage Flow

1. **User Registration** → Sign up and create account
2. **Organization Setup** → Create workspace/organization
3. **Start Meeting** → Create new meeting session
4. **Live Transcription** → Enable realtime transcript capture
5. **Realtime Updates** → See decisions/actions as they're extracted
6. **Graph Visualization** → View relationship graphs
7. **Export/Share** → Share meeting intelligence with team

## 🚀 Deployment

### Docker Production Build

```bash
# Build images
docker-compose build

# Run with production settings
docker-compose -f docker-compose.yml up -d

# Run with workers
docker-compose --profile workers up -d
```

### Environment for Production

```env
DEBUG=False
SECRET_KEY=strong-random-key-here
FRONTEND_URL=https://your-domain.com
DATABASE_URL=postgresql://user:pass@your-prod-db:5432/synapse
```

## 🛠️ Development

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload

# Run AI worker
python -m app.workers.ai_worker

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check
```

## 📚 Documentation

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit PR

## 📄 License

MIT

## 🙋 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

**Built with ❤️ for operational intelligence.**

Synapse v0.1.0 - Phase 1 Foundation
