# Docker Setup Guide for Synapse

This guide explains how to set up and run Synapse using Docker Compose for local development.

## Prerequisites

- **Docker Desktop** (version 20.10+)
- **Docker Compose** (version 1.29+)
- **4GB RAM** minimum for Docker (6GB+ recommended)
- **20GB disk space** for images and volumes

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/synapse.git
cd synapse
```

### 2. Configure Environment Variables

Copy the environment template and configure it:

```bash
cp .env.example .env
```

Edit `.env` and update the following (optional for local development):
- `GEMINI_API_KEY` - Get from https://makersuite.google.com/app/apikey
- `DEEPGRAM_API_KEY` - For speech-to-text (optional)
- `SUPABASE_URL` and `SUPABASE_KEY` - For file storage (optional)

For local development with Docker, the default values work fine.

### 3. Start All Services

```bash
# Start all services in the background
docker-compose up -d

# Or start with logs visible
docker-compose up

# To stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Backend ReDoc**: http://localhost:8000/redoc

## Service Details

### PostgreSQL Database
- **Port**: 5432 (exposed for development)
- **Credentials**: synapse / synapse
- **Database**: synapse
- **Health Check**: Enabled (checks every 10 seconds)

### Redis Cache & Queue
- **Port**: 6379
- **Purpose**: Realtime Pub/Sub, async job queue
- **Health Check**: Enabled

### Qdrant Vector Database
- **Port**: 6333 (REST API), 6334 (gRPC)
- **API Key**: synapse-key
- **Purpose**: Vector embeddings and semantic search

### FastAPI Backend
- **Port**: 8000
- **Features**: Hot-reload enabled (code changes auto-reload)
- **Health Check**: Enabled at /health endpoint
- **Logs**: `docker logs synapse-backend` or `docker-compose logs backend`

### Next.js Frontend
- **Port**: 3000
- **Features**: Hot-reload enabled (code changes auto-reload)
- **Health Check**: Enabled
- **Logs**: `docker logs synapse-frontend` or `docker-compose logs frontend`

### AI Worker (Optional)
- **Status**: Disabled by default (profiles: workers)
- **Purpose**: Background processing of AI jobs
- **Start**: `docker-compose up -d --profile workers ai_worker`

## Common Commands

### Docker Compose Commands

```bash
# View all running services
docker-compose ps

# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f backend

# Rebuild images (useful if requirements.txt changed)
docker-compose build --no-cache

# Start a specific service
docker-compose up -d postgres

# Stop all services
docker-compose down

# Remove all services, volumes, and data
docker-compose down -v

# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend bash
docker-compose exec postgres psql -U synapse -d synapse
```

### Make Commands (if Makefile is available)

```bash
# View available commands
make help

# Start all services (shortcut)
make up

# Stop all services
make down

# View logs
make logs

# Clean up everything
make clean

# Start AI worker
make worker

# Rebuild images
make build
```

## Development Workflow

### Backend Development

The backend container automatically reloads when you modify files in `backend/app/`:

```bash
# View backend logs in real-time
docker-compose logs -f backend

# Access the backend container
docker-compose exec backend bash

# Run commands inside the container
docker-compose exec backend python -m pytest
docker-compose exec backend pip install package-name
```

### Frontend Development

The frontend container automatically reloads when you modify files in `frontend/app/` or `frontend/src/`:

```bash
# View frontend logs in real-time
docker-compose logs -f frontend

# Access the frontend container
docker-compose exec frontend bash

# Install new packages
docker-compose exec frontend npm install package-name
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U synapse -d synapse

# List all tables
\dt

# Exit psql
\q

# Dump database (backup)
docker-compose exec postgres pg_dump -U synapse -d synapse > backup.sql

# Restore database
docker-compose exec -T postgres psql -U synapse -d synapse < backup.sql
```

### Redis Commands

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View all keys
KEYS *

# Get job queue length
LLEN queue:ai_jobs

# View realtime subscriptions
PUBSUB CHANNELS

# Exit redis-cli
exit
```

## Troubleshooting

### Services Won't Start

**Problem**: `docker-compose up` fails or services don't start

**Solutions**:
1. Check if ports are already in use:
   ```bash
   lsof -i :3000      # Check port 3000
   lsof -i :8000      # Check port 8000
   lsof -i :5432      # Check port 5432
   ```

2. Increase Docker resources:
   - Open Docker Desktop Settings
   - Go to Resources
   - Increase Memory to 6GB or higher
   - Increase CPUs to 4+

3. Check Docker logs:
   ```bash
   docker-compose logs --tail 50
   ```

### Database Connection Errors

**Problem**: Backend can't connect to PostgreSQL

**Solution**: Wait for database to be ready
```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready -U synapse

# Check health status
docker-compose ps
```

### Frontend Shows Blank Page

**Problem**: Frontend loads but shows blank page

**Solutions**:
1. Check frontend logs: `docker-compose logs -f frontend`
2. Verify backend is accessible: `curl http://localhost:8000/health`
3. Check browser console for errors (F12)
4. Rebuild frontend: `docker-compose up --build frontend`

### Port Already in Use

**Problem**: Port 3000, 8000, or 5432 already in use

**Solutions**:

Option 1 - Stop other applications using the port:
```bash
lsof -i :PORT_NUMBER
kill -9 PID
```

Option 2 - Change the port in docker-compose.yml:
```yaml
frontend:
  ports:
    - "3001:3000"  # Changed from 3000:3000

backend:
  ports:
    - "8001:8000"  # Changed from 8000:8000
```

### Out of Disk Space

**Problem**: Docker containers won't start, disk full

**Solution**: Clean up Docker resources
```bash
# Remove unused images, containers, volumes
docker system prune -a --volumes

# Or more aggressively
docker container prune -f
docker image prune -a -f
docker volume prune -f
```

### Connection Refused Errors

**Problem**: Backend can't reach Redis or PostgreSQL

**Solution**: Ensure services are running and healthy
```bash
# Check service health
docker-compose ps

# Restart all services
docker-compose down
docker-compose up -d
```

### Slow Performance

**Problem**: Services running slowly in Docker

**Solutions**:
1. Allocate more Docker resources (see Increase Docker resources above)
2. Check Docker disk usage: `docker system df`
3. Rebuild images: `docker-compose build --no-cache`
4. Clear Docker cache: `docker builder prune`

### AI Worker Issues

**Problem**: AI worker won't start or processes hang

**Solution**: Start the AI worker service
```bash
# Check if worker service exists
docker-compose ps

# Start the worker service
docker-compose up -d --profile workers ai_worker

# View worker logs
docker-compose logs -f ai_worker

# Stop worker
docker-compose stop ai_worker
```

## Production Considerations

### Security

For production deployment:
1. Change all default passwords and secrets
2. Use strong `SECRET_KEY` (generate with: `openssl rand -hex 32`)
3. Remove `DEBUG=True` environment variable
4. Configure proper CORS origins
5. Enable HTTPS/TLS

### Environment Configuration

Create a `.env.production` file:
```bash
DEBUG=False
SECRET_KEY=<generate-strong-random-key>
FRONTEND_URL=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/synapse
REDIS_URL=redis://prod-redis:6379/0
GEMINI_API_KEY=<your-production-api-key>
```

### Database

- Use managed database services (AWS RDS, Google Cloud SQL, etc.)
- Set up regular backups
- Configure connection pooling
- Enable monitoring and alerts

### Scaling

For production scaling:
1. Use Docker Swarm or Kubernetes
2. Run multiple backend instances behind a load balancer
3. Use managed Redis (ElastiCache, Memorystore)
4. Use managed PostgreSQL (RDS, Cloud SQL)
5. Set up monitoring with Prometheus/Grafana

## Advanced Topics

### Custom Docker Networks

The default network (`synapse-network`) allows all services to communicate. To customize:

```bash
# View networks
docker network ls

# Inspect network
docker network inspect synapse_synapse-network

# Create custom network
docker network create my-network
docker-compose --network my-network up
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect synapse_postgres_data

# Back up volume
docker run --rm -v synapse_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v synapse_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Building Custom Images

```bash
# Build specific service
docker-compose build backend

# Build without cache
docker-compose build --no-cache frontend

# Build and push to registry
docker-compose build
docker-compose push
```

## Getting Help

- Check logs: `docker-compose logs -f SERVICE_NAME`
- Enter container: `docker-compose exec SERVICE_NAME bash`
- View API docs: http://localhost:8000/docs
- Check database: `docker-compose exec postgres psql -U synapse -d synapse`

For more information, see:
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Synapse README](./README.md)
- [Getting Started Guide](./GETTING_STARTED.md)
