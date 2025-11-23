#!/bin/bash

# Script to launch multiple client instances
# Usage: ./launch_clients.sh [number_of_clients]

NUM_CLIENTS=${1:-100}

echo "Launching $NUM_CLIENTS clients..."

for i in $(seq 1 $NUM_CLIENTS); do
    python3 client.py $i &
done

echo "All clients launched!"
echo "Waiting for all clients to complete..."
wait
echo "All clients completed!"
