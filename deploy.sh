#!/bin/bash
# Deployment script for Trading Bot Dashboard
# Universal script for VPS/Cloud deployment

set -e  # Exit on error

echo "======================================"
echo "🚀 Trading Bot Dashboard Deployment"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if Docker is installed
if command -v docker &> /dev/null; then
    print_status "Docker is installed"
else
    print_error "Docker is not installed. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_status "Docker installed successfully"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    print_status "Docker Compose is installed"
else
    print_info "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
fi

# Create necessary directories
print_info "Creating directories..."
mkdir -p logs ssl

# Build and start containers
print_info "Building Docker image..."
docker-compose build

print_info "Starting containers..."
docker-compose up -d

# Wait for service to be ready
print_info "Waiting for dashboard to be ready..."
sleep 10

# Check if service is running
if curl -f http://localhost:8080 &> /dev/null; then
    print_status "Dashboard is running successfully!"
    echo ""
    echo "======================================"
    echo "✨ Deployment Complete!"
    echo "======================================"
    echo "📊 Local access: http://localhost:8080"
    echo "🌐 External access: http://$(curl -s ifconfig.me):8080"
    echo ""
    echo "Useful commands:"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Stop: docker-compose down"
    echo "  - Restart: docker-compose restart"
    echo "  - Status: docker-compose ps"
    echo "======================================"
else
    print_error "Dashboard failed to start. Check logs:"
    docker-compose logs
fi
