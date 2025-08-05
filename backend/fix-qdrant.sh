#!/bin/bash

# Qdrant Troubleshooting Script
# This script helps diagnose and fix Qdrant startup issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Clean up any existing containers
cleanup_containers() {
    print_status "Cleaning up existing containers..."
    
    # Stop and remove containers
    docker-compose down -v --remove-orphans 2>/dev/null || true
    
    # Remove any dangling containers
    docker container prune -f 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Test Qdrant standalone
test_qdrant_standalone() {
    print_status "Testing Qdrant standalone..."
    
    # Start just Qdrant
    docker run -d --name test-qdrant -p 6333:6333 qdrant/qdrant:latest
    
    # Wait for startup
    print_status "Waiting for Qdrant to start..."
    sleep 10
    
    # Test connection
    for i in {1..30}; do
        if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
            print_success "Qdrant is responding!"
            docker stop test-qdrant && docker rm test-qdrant
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    print_error "Qdrant failed to start properly"
    docker logs test-qdrant
    docker stop test-qdrant && docker rm test-qdrant
    return 1
}

# Start with simplified compose
start_simplified() {
    print_status "Starting with simplified Docker Compose..."
    
    # Use simplified compose file
    docker-compose -f docker-compose.simple.yml up --build -d
    
    print_status "Waiting for services to start..."
    sleep 15
    
    # Check Qdrant
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        print_success "Qdrant is running!"
    else
        print_error "Qdrant is not responding"
        docker-compose -f docker-compose.simple.yml logs qdrant
        return 1
    fi
    
    # Check Backend
    sleep 10
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend is running!"
        print_success "Backend API: http://localhost:8000"
        print_success "API Docs: http://localhost:8000/docs"
        print_success "Qdrant: http://localhost:6333/dashboard"
    else
        print_warning "Backend may still be starting..."
        print_status "Check logs with: docker-compose -f docker-compose.simple.yml logs backend"
    fi
}

# Show detailed logs
show_logs() {
    print_status "Showing container logs..."
    
    echo ""
    print_status "=== Qdrant Logs ==="
    docker-compose logs qdrant 2>/dev/null || docker logs bm-ai-qdrant 2>/dev/null || echo "No Qdrant logs found"
    
    echo ""
    print_status "=== Backend Logs ==="
    docker-compose logs backend 2>/dev/null || docker logs bm-ai-backend 2>/dev/null || echo "No Backend logs found"
}

# Main troubleshooting function
main() {
    echo "🔧 Qdrant Troubleshooting Tool"
    echo "=============================="
    echo ""
    
    case "${1:-auto}" in
        "cleanup")
            cleanup_containers
            ;;
        "test")
            test_qdrant_standalone
            ;;
        "simple")
            cleanup_containers
            start_simplified
            ;;
        "logs")
            show_logs
            ;;
        "auto"|*)
            print_status "Running automatic troubleshooting..."
            
            # Step 1: Cleanup
            cleanup_containers
            
            # Step 2: Test Qdrant standalone
            if test_qdrant_standalone; then
                print_success "Qdrant works standalone"
            else
                print_error "Qdrant has issues even standalone"
                exit 1
            fi
            
            # Step 3: Start with simplified compose
            start_simplified
            
            print_success "Troubleshooting completed!"
            print_status "If issues persist, check logs with: $0 logs"
            ;;
    esac
}

# Show usage if no valid command
if [[ "$1" == "help" ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  auto     - Run automatic troubleshooting (default)"
    echo "  cleanup  - Clean up containers and volumes"
    echo "  test     - Test Qdrant standalone"
    echo "  simple   - Start with simplified compose"
    echo "  logs     - Show container logs"
    echo "  help     - Show this help"
    exit 0
fi

main "$1"
