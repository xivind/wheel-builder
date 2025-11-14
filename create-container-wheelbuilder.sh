#!/bin/bash

set -o xtrace

# Cleanup container and image
docker container stop wheel-builder
docker container rm wheel-builder
docker image rm wheel-builder

# Build image and tag it
docker build -t wheel-builder .

# Create data directory on host if it doesn't exist
mkdir -p ~/code/container_data

# Create and run container
docker run -d \
  --name=wheel-builder \
  -e TZ=Europe/Stockholm \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8004:8004 \
  wheel-builder