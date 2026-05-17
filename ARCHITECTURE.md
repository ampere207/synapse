"""Architecture documentation"""
# Synapse Architecture

## Overview

Synapse is built with a **scalable, modular architecture** designed for realtime operational intelligence extraction from meetings.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Synapse Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐         ┌────────────────────┐   │
│  │   Frontend Layer     │         │  Backend API Layer │   │
│  │  (Next.js 15)        │◄────────► (FastAPI)          │   │
│  │  - React Flow Graph  │ REST/WS │ - Auth             │   │
│  │  - Real-time UI      │◄────────► - Meetings         │   │
│  │  - Zustand State     │         │ - Transcripts      │   │
│  │  - React Query       │         │ - Graphs           │   │
│  └──────────────────────┘         └────────────────────┘   │
│           ▲                                 ▲                │
│           │                                 │                │
│           │ WebSocket (realtime)            │ REST           │
│           │ (transcript, graph updates)     │                │
│           │                                 │                │
│  ┌────────▼─────────────────────────────────▼────────┐      │
│  │         Realtime Infrastructure (Redis)           │      │
│  │  - Pub/Sub: broadcast to users                    │      │
│  │  - Queue: async job distribution                  │      │
│  │  - Cache: session management                      │      │
│  └────────┬──────────────────────────────────────────┘      │
│           │                                                   │
│  ┌────────▼─────────────────────────────────────────┐       │
│  │         Data & Storage Layer                     │       │
│  │  ┌──────────────┐  ┌──────────────┐             │       │
│  │  │ PostgreSQL   │  │ Qdrant       │             │       │
│  │  │ - Structured │  │ - Vectors    │             │       │
│  │  │ - Relational │  │ - Embeddings │             │       │
│  │  │ - RLS        │  │ - Search     │             │       │
│  │  └──────────────┘  └──────────────┘             │       │
│  │  ┌──────────────┐  ┌──────────────┐             │       │
│  │  │ Supabase     │  │ File Storage │             │       │
│  │  │ Storage      │  │ - Uploads    │             │       │
│  │  │ - Transcripts│  │ - Recordings │             │       │
│  │  └──────────────┘  └──────────────┘             │       │
│  └─────────────────────────────────────────────────┘       │
│           ▲                                                   │
│           │ Async Processing                                │
│           │                                                  │
│  ┌────────▼─────────────────────────────────────────┐       │
│  │      AI Pipeline & Workers                      │       │
│  │  ┌─────────────────────────────────────────┐   │       │
│  │  │ Async Queue (Redis)                     │   │       │
│  │  │ - Priority queues (high/med/low)        │   │       │
│  │  │ - Job tracking                          │   │       │
│  │  │ - Result caching                        │   │       │
│  │  └─────────────────────────────────────────┘   │       │
│  │  ┌─────────────────────────────────────────┐   │       │
│  │  │ AI Workers (horizontal scaling)         │   │       │
│  │  │ - Batch processing                      │   │       │
│  │  │ - Gemini API calls                      │   │       │
│  │  │ - Decision extraction                   │   │       │
│  │  │ - Graph building                        │   │       │
│  │  └─────────────────────────────────────────┘   │       │
│  │  ┌─────────────────────────────────────────┐   │       │
│  │  │ Speech-to-Text Service                  │   │       │
│  │  │ - Deepgram/AssemblyAI API               │   │       │
│  │  │ - Audio transcription                   │   │       │
│  │  └─────────────────────────────────────────┘   │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │  External Services                              │        │
│  │  - Gemini API (intelligence extraction)         │        │
│  │  - Speech-to-Text (transcription)               │        │
│  │  - Supabase (file storage)                      │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend (Next.js 15)

**Responsibilities:**
- User interface and real-time updates
- Graph visualization (React Flow)
- State management (Zustand)
- API communication (Axios)
- WebSocket connections

**Key Features:**
- Responsive design with TailwindCSS
- Real-time transcript display
- Interactive graph explorer
- Live decision/action extraction feed
- Multi-user presence awareness

**Technology:**
- Next.js 15 (app router)
- TypeScript
- TailwindCSS
- React Flow
- Zustand
- React Query

### 2. Backend API (FastAPI)

**Responsibilities:**
- REST API endpoints
- Authentication & authorization
- Business logic
- Data validation
- WebSocket gateway

**Key Modules:**

```
app/
├── api/
│   ├── auth.py         # Authentication endpoints
│   ├── organizations.py # Organization management
│   └── meetings.py     # Meeting management
├── core/
│   ├── config.py       # Configuration
│   ├── database.py     # Database setup
│   └── security.py     # JWT, password hashing
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic validation schemas
├── services/           # Business logic
├── realtime/           # WebSocket infrastructure
│   └── websocket.py    # Connection manager
├── ai_pipeline/        # AI processing
│   ├── provider.py     # AI provider abstraction
│   ├── queue.py        # Async queue
│   └── batching.py     # Transcript batching
└── workers/            # Background jobs
    └── ai_worker.py    # AI job processor
```

### 3. Realtime Infrastructure (Redis)

**Responsibilities:**
- WebSocket message broadcasting
- Async job queuing
- Session caching
- Rate limiting

**Features:**
- Pub/Sub for real-time updates
- Priority queues for job processing
- TTL-based cache expiration
- High-performance messaging

### 4. Data Layer (PostgreSQL)

**Responsibilities:**
- Persistent data storage
- Multi-tenant isolation via RLS
- Referential integrity
- Transactional consistency

**Key Tables:**
- `users` - User accounts
- `organizations` - Workspaces
- `organization_members` - Role management
- `meetings` - Meeting sessions
- `transcripts` - Full transcripts
- `transcript_chunks` - Streamed segments
- `graph_nodes` - Intelligence nodes
- `graph_edges` - Node relationships
- `decisions` - Extracted decisions
- `action_items` - Extracted actions
- `ai_processing_jobs` - Job tracking

### 5. Vector Database (Qdrant)

**Responsibilities:**
- Semantic search
- Embedding storage
- Similarity matching

**Future Use:**
- Finding related decisions across meetings
- Topic clustering
- Context retrieval for AI

### 6. AI Pipeline

**Architecture:**

```
Realtime Input
     ↓
┌─────────────────────────────┐
│  Transcript Streaming       │
│  (WebSocket)                │
│  - No AI processing         │
│  - Real-time to frontend    │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  Batching Layer             │
│  - Time window (120s)       │
│  - Token limit (1000)       │
│  - Topic transition         │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  Redis Processing Queue     │
│  - Priority-based           │
│  - Job tracking             │
│  - Result caching           │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  AI Workers (Async)         │
│  - Parallel processing      │
│  - Horizontal scaling       │
│  - Error handling           │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  Gemini API Calls           │
│  - Summarization            │
│  - Decision extraction      │
│  - Action extraction        │
│  - Topic detection          │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│  Result Broadcasting        │
│  - WebSocket updates        │
│  - Database storage         │
│  - Graph building           │
└────────┬────────────────────┘
         ↓
Frontend Update (React Flow, Decisions List)
```

## Data Flow

### Meeting Creation Flow

```
User → Frontend → Backend API → Database
                      ↓
                Create Meeting
                Org isolation check
                      ↓
                Return meeting ID
                      ↓
Frontend stores in Zustand → Update UI
```

### Realtime Transcript Flow

```
Audio Input → STT Service → WebSocket message
                                  ↓
                           Backend receives
                                  ↓
                           Broadcast to org
                                  ↓
All Frontend clients get realtime update
```

### AI Processing Flow

```
Transcript chunks accumulate → Batching trigger
                                    ↓
                        Add to Redis queue
                                    ↓
                        AI Worker picks up
                                    ↓
                        Call Gemini API
                                    ↓
                    Extract: Decisions, Actions, Topics
                                    ↓
                        Save to database
                                    ↓
                    Broadcast via WebSocket
                                    ↓
Frontend receives → React Flow updates → User sees graph
```

## Security Architecture

### Authentication

- JWT tokens (HS256)
- Access tokens (30 min expiry)
- Refresh tokens (7 day expiry)
- Secure token storage

### Authorization

- Organization-level access control
- Role-based permissions (Owner, Admin, Member, Viewer)
- Resource ownership checks
- Row-level security in database

### Multi-Tenancy

- Complete org isolation at API level
- Database foreign key constraints
- WebSocket scoped connections
- No cross-org data leakage possible

### Data Protection

- Password hashing (bcrypt)
- Secure file uploads (Supabase)
- HTTPS/TLS in production
- Encrypted sensitive fields

## Scalability

### Horizontal Scaling

- **API Servers**: Multiple backend instances
- **Workers**: Multiple AI processing workers
- **Database**: Read replicas, connection pooling
- **Redis**: Cluster mode for HA
- **Frontend**: CDN deployment

### Performance Optimization

- Database indexes on org_id, meeting_id, user_id
- Connection pooling (SQLAlchemy)
- Redis caching for sessions
- Batch processing for AI calls
- Incremental graph updates

### Cost Optimization

- Transcript batching (reduce Gemini calls)
- Async processing (non-blocking)
- Result caching
- Smart queue prioritization
- Vector search for deduplication

## Deployment Architecture

```
┌─────────────────────────────────────┐
│      Production Environment         │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Load Balancer (nginx)      │   │
│  └──┬────────────────────────┬─┘   │
│     │                        │      │
│  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐  │     │
│  │ API │  │ API │  │ API │◄─┘     │
│  └──┬──┘  └──┬──┘  └──┬──┘        │
│     │       │        │            │
│  ┌──▼───────▼────────▼──┐         │
│  │  Kubernetes/ECS      │         │
│  │  - Container orch.   │         │
│  │  - Auto-scaling      │         │
│  │  - Health checks     │         │
│  └──────┬────────────────┘         │
│         │                          │
│  ┌──────▼─────────────────┐        │
│  │ AWS RDS PostgreSQL     │        │
│  │ - Multi-AZ             │        │
│  │ - Auto-backup          │        │
│  │ - Read replicas        │        │
│  └────────────────────────┘        │
│  ┌──────────────────────────┐      │
│  │ ElastiCache Redis        │      │
│  │ - Cluster mode           │      │
│  │ - Multi-AZ               │      │
│  │ - Auto-failover          │      │
│  └──────────────────────────┘      │
│  ┌──────────────────────────┐      │
│  │ S3 + CloudFront          │      │
│  │ - File storage           │      │
│  │ - CDN distribution       │      │
│  └──────────────────────────┘      │
│                                     │
└─────────────────────────────────────┘
```

## Future Architecture Enhancements

### Phase 2
- Neo4j for advanced graph queries
- Recurring blocker detection
- Decision evolution tracking

### Phase 3
- Vector search integration
- Advanced memory retrieval
- Multi-model AI support

### Phase 4
- Real-time analytics
- Predictive insights
- Integration marketplace

---

**Built for operational intelligence at scale.**
