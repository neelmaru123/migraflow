#!/usr/bin/env bash
# ==============================================================================
# Migraflow Production Deployment & Health Verification Script
# Target Environments: AWS EC2, Ubuntu 22.04/24.04, Debian 12, Amazon Linux 2023
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}       MIGRAFLOW AUTONOMOUS PLATFORM - PRODUCTION DEPLOYER       ${NC}"
echo -e "${CYAN}================================================================${NC}"

# 1. Dependency checks
echo -e "\n${YELLOW}[1/6] Checking system prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker Engine first.${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose plugin is not installed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker & Docker Compose plugin verified.${NC}"

# 2. Environment file check
echo -e "\n${YELLOW}[2/6] Verifying environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.production.example" ]; then
        echo -e "${YELLOW}Notice: '.env' not found. Creating from '.env.production.example'...${NC}"
        cp .env.production.example .env
        echo -e "${YELLOW}Please review '.env' and verify your API keys and HOST_IP.${NC}"
    else
        echo -e "${RED}Error: Neither '.env' nor '.env.production.example' found.${NC}"
        exit 1
    fi
fi

# Detect whether production Nginx compose or standard compose is preferred
COMPOSE_FILE="docker-compose.prod.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.yml"
fi
echo -e "${GREEN}✓ Using Compose configuration: ${COMPOSE_FILE}${NC}"

# 3. Pull & Build Docker Images
echo -e "\n${YELLOW}[3/6] Building and preparing application containers...${NC}"
docker compose -f "$COMPOSE_FILE" build --pull

# 4. Starting Production Services
echo -e "\n${YELLOW}[4/6] Booting production services in detached mode...${NC}"
docker compose -f "$COMPOSE_FILE" up -d

# 5. Health Check Verification Loop
echo -e "\n${YELLOW}[5/6] Awaiting service health readiness...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # Check API health
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "migration_platform_api.*healthy"; then
        HEALTHY=true
        break
    fi
    
    echo -e "Waiting for API database connectivity & migrations... (${RETRY_COUNT}/${MAX_RETRIES})"
    sleep 3
done

if [ "$HEALTHY" = true ]; then
    echo -e "${GREEN}✓ Backend API is healthy and database migrations are complete!${NC}"
else
    echo -e "${RED}Warning: API health check timed out. Checking container logs:${NC}"
    docker compose -f "$COMPOSE_FILE" logs --tail=30 api
    exit 1
fi

# 6. Deployment Summary
echo -e "\n${CYAN}================================================================${NC}"
echo -e "${GREEN}🎉 MIGRAFLOW PRODUCTION DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${CYAN}================================================================${NC}"

# Read HOST_IP if set
HOST_IP=$(grep -E '^HOST_IP=' .env | cut -d '=' -f2 | tr -d '"' || echo "localhost")
if [ -z "$HOST_IP" ]; then
    HOST_IP="localhost"
fi

if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
    echo -e "Web App & API:       ${CYAN}http://${HOST_IP}/${NC}"
    echo -e "API Documentation:   ${CYAN}http://${HOST_IP}/docs${NC}"
    echo -e "API Health Probe:    ${CYAN}http://${HOST_IP}/api/v1/health${NC}"
else
    echo -e "Web App:             ${CYAN}http://${HOST_IP}:3000${NC}"
    echo -e "API Control Plane:   ${CYAN}http://${HOST_IP}:8000${NC}"
    echo -e "API Health Probe:    ${CYAN}http://${HOST_IP}:8000/api/v1/health${NC}"
fi

echo -e "\nUseful Commands:"
echo -e "  View logs:          docker compose -f ${COMPOSE_FILE} logs -f"
echo -e "  Stop stack:         docker compose -f ${COMPOSE_FILE} down"
echo -e "  Restart stack:      docker compose -f ${COMPOSE_FILE} restart"
echo -e "${CYAN}================================================================${NC}\n"
