#!/bin/bash

# Ejecutar desde la raiz del proyecto
set -e

IMAGE_NAME="dftp_node"
NETWORK_NAME="dftp_net"

echo ">>> Construyendo imagen Docker..."
docker build -f comm/tests/Dockerfile -t $IMAGE_NAME .

echo ">>> Creando red overlay bridge..."
docker network create $NETWORK_NAME || true

echo ">>> Iniciando contenedor node1..."
docker run -d --rm \
    --name node1 \
    --network $NETWORK_NAME \
    $IMAGE_NAME \
    python3 comm/tests/run_node.py --id node1 --port 9100

sleep 1

echo ">>> Ejecutando test_ping desde node2 contra node1..."
docker run --rm \
    --name node2 \
    --network $NETWORK_NAME \
    $IMAGE_NAME \
    python3 comm/tests/test_ping.py --id node2 --target node1 --port 9100

echo ">>> Deteniendo contenedores..."
docker stop node1 || true
docker stop node2 || true

echo ">>> Eliminando red..."
docker network rm $NETWORK_NAME || true

echo ">>> Prueba completada."
