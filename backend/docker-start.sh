#!/bin/bash

# Docker Startup Script for BM-AI Backend
# This script provides easy commands to manage the Dockerized backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found!"
        if [ -f .env.docker ]; then
            print_status "Copying .env.docker to .env..."
            cp .env.docker .env
            print_warning "Please edit .env file and add your GOOGLE_API_KEY"
            return 1
        else
            print_error "No environment file found. Please create .env file with your configuration."
            return 1
        fi
    fi
    return 0
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Start services
start_services() {
    print_status "Starting BM-AI Backend services..."
    
    check_docker
    
    if ! check_env_file; then
        print_error "Environment setup required. Please configure .env file first."
        exit 1
    fi
    
    # Build and start services
    docker-compose up --build -d
    
    print_success "Services started successfully!"
    print_status "Backend API: http://localhost:8000"
    print_status "Qdrant Dashboard: http://localhost:6333/dashboard"
    
    # Show logs
    print_status "Showing logs (Ctrl+C to stop)..."
    docker-compose logs -f
}

# Stop services
stop_services() {
    print_status "Stopping BM-AI Backend services..."
    docker-compose down
    print_success "Services stopped successfully!"
}

# Restart services
restart_services() {
    print_status "Restarting BM-AI Backend services..."
    docker-compose restart
    print_success "Services restarted successfully!"
}

# Show status
show_status() {
    print_status "BM-AI Backend Services Status:"
    docker-compose ps
    
    echo ""
    print_status "Service Health:"
    
    # Check backend health
    if curl -s http://localhost:8000/ > /dev/null; then
        print_success "Backend API: ✅ Running (http://localhost:8000)"
    else
        print_error "Backend API: ❌ Not responding"
    fi
    
    # Check Qdrant health
    if curl -s http://localhost:6333/health > /dev/null; then
        print_success "Qdrant: ✅ Running (http://localhost:6333)"
    else
        print_error "Qdrant: ❌ Not responding"
    fi
}

# Show logs
show_logs() {
    if [ -n "$2" ]; then
        print_status "Showing logs for $2..."
        docker-compose logs -f "$2"
    else
        print_status "Showing all logs..."
        docker-compose logs -f
    fi
}

# Clean up (remove containers and volumes)
cleanup() {
    print_warning "This will remove all containers and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Setup environment
setup_env() {
    print_status "Setting up environment..."
    
    if [ -f .env ]; then
        print_warning ".env file already exists. Backup will be created."
        cp .env .env.backup
    fi
    
    cp .env.docker .env
    
    print_success "Environment file created!"
    print_warning "Please edit .env file and add your GOOGLE_API_KEY:"
    print_status "nano .env"
    print_status ""
    print_status "Required configuration:"
    print_status "  GOOGLE_API_KEY=your_actual_api_key_here"
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    cleanup)
        cleanup
        ;;
    setup)
        setup_env
        ;;
    *)
        echo "BM-AI Backend Docker Management"
        echo "================================"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|cleanup|setup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services (backend + Qdrant)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status and health"
        echo "  logs     - Show logs (optional: specify service name)"
        echo "  cleanup  - Remove all containers and volumes"
        echo "  setup    - Setup environment file"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs backend"
        echo "  $0 logs qdrant"
        echo ""
        echo "URLs after starting:"
        echo "  Backend API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  Qdrant Dashboard: http://localhost:6333/dashboard"
        exit 1
        ;;
esac
