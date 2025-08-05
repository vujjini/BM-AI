# BM-AI Backend Docker Setup

This guide explains how to run the BM-AI Backend with all required services using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Google API Key for Gemini and Embeddings

### 1. Setup Environment
```bash
# Copy environment template
cp .env.docker .env

# Edit .env file and add your Google API Key
nano .env  # or use your preferred editor
```

### 2. Start Services
```bash
# Make startup script executable (Linux/Mac)
chmod +x docker-start.sh

# Start all services
./docker-start.sh start

# Or use docker-compose directly
docker-compose up --build -d
```

### 3. Access Services
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 📋 Available Commands

### Using the Startup Script
```bash
./docker-start.sh start     # Start all services
./docker-start.sh stop      # Stop all services
./docker-start.sh restart   # Restart all services
./docker-start.sh status    # Show service status
./docker-start.sh logs      # Show all logs
./docker-start.sh logs backend  # Show backend logs only
./docker-start.sh cleanup   # Remove containers and volumes
./docker-start.sh setup     # Setup environment file
```

### Using Docker Compose Directly
```bash
# Development (with hot reload)
docker-compose up --build -d

# Production
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean up everything
docker-compose down -v --remove-orphans
```

## 🏗️ Architecture

### Services
1. **Backend (FastAPI)**: Main application server
   - Port: 8000
   - Features: PDF processing, Excel conversion, file uploads
   - Auto-reloads in development mode

2. **Qdrant**: Vector database for document embeddings
   - HTTP Port: 6333
   - gRPC Port: 6334
   - Persistent storage with Docker volumes

### Network
- All services run on a custom bridge network (`bm-ai-network`)
- Services communicate using container names as hostnames
- Only necessary ports are exposed to the host

## 📁 File Structure

```
backend/
├── Dockerfile                 # Backend container definition
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── docker-start.sh           # Management script
├── .env.docker              # Environment template
├── .dockerignore            # Docker ignore rules
└── uploads/                 # Volume for file uploads
```

## 🔧 Configuration

### Environment Variables
```env
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Qdrant (automatically configured)
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_URL=
QDRANT_API_KEY=
```

### Volumes
- `qdrant_storage`: Persistent storage for Qdrant data
- `./uploads`: Host directory for uploaded files

## 🔍 Monitoring and Health Checks

### Health Endpoints
- Backend: `GET http://localhost:8000/`
- Qdrant: `GET http://localhost:6333/health`

### Service Status
```bash
# Check container status
docker-compose ps

# Check health status
./docker-start.sh status

# View real-time logs
docker-compose logs -f
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :6333
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

2. **Qdrant Connection Issues**
   ```bash
   # Check Qdrant logs
   docker-compose logs qdrant
   
   # Restart Qdrant service
   docker-compose restart qdrant
   ```

3. **Backend Not Starting**
   ```bash
   # Check backend logs
   docker-compose logs backend
   
   # Verify environment variables
   docker-compose exec backend env | grep GOOGLE_API_KEY
   ```

4. **Permission Issues (Linux/Mac)**
   ```bash
   # Make script executable
   chmod +x docker-start.sh
   
   # Fix upload directory permissions
   sudo chown -R $USER:$USER uploads/
   ```

### Reset Everything
```bash
# Complete cleanup and restart
./docker-start.sh cleanup
./docker-start.sh start
```

## 🚀 Production Deployment

### Using Production Compose File
```bash
# Start in production mode
docker-compose -f docker-compose.prod.yml up --build -d

# Production differences:
# - No source code mounting (no hot reload)
# - Resource limits applied
# - Optimized for stability
```

### Production Checklist
- [ ] Set strong environment variables
- [ ] Configure proper logging
- [ ] Set up monitoring
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure backup for Qdrant data

## 📊 API Usage Examples

### Upload Single File
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.xlsx"
```

### Upload Multiple Files
```bash
curl -X POST "http://localhost:8000/api/upload-folder" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.xlsx"
```

### Chat with Documents
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main issues mentioned in the logs?"}'
```

## 🔄 Development Workflow

1. **Start Development Environment**
   ```bash
   ./docker-start.sh start
   ```

2. **Make Code Changes**
   - Backend auto-reloads on file changes
   - No need to rebuild container for code changes

3. **View Logs**
   ```bash
   ./docker-start.sh logs backend
   ```

4. **Test API**
   - Visit http://localhost:8000/docs for interactive API docs
   - Use curl or Postman for API testing

5. **Stop When Done**
   ```bash
   ./docker-start.sh stop
   ```

## 📝 Notes

- The development setup mounts source code for hot reloading
- Qdrant data persists between container restarts
- Upload files are stored in `./uploads/` directory
- All services start automatically with health checks
- Logs are available through Docker Compose or the startup script
