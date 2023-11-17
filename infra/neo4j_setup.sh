#!/bin/bash

# Install & Auto start Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.3.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create Docker Compose file for Neo4j
sudo cat <<EOF > docker-compose.yml
version: '3.8'
services: 
  neo4j: 
    image: neo4j:5.11
    hostname: neo4j 
    restart: always 
    environment: 
      NEO4J_dbms_security_allow__csv__import__from__file__urls : true 
      NEO4J_dbms_memory_heap_initial__size : 4g 
      NEO4J_dbms_memory_heap.max__size : 4g 
      NEO4J_dbms_memory_pagecache_size : 4g 
      NEO4J_AUTH : neo4j/llmfaqdemo 
      NEO4J_PLUGINS: '["apoc"]'
    ports: 
       - 7687:7687 
       - 7474:7474 
       - 7473:7473 
 
  neodash: 
    image: neo4jlabs/neodash:2.2.3 
    container_name: neodash 
    restart: always 
    ports: 
      - 5005:5005
EOF

# Run Docker Compose with retry
for attempt in {1..5}; do
    sudo docker-compose up -d && break || sleep 10;
done
