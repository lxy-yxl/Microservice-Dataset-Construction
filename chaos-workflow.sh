#!/bin/bash

# Step 1: make deploy
make deploy DeployArgs="--with-tracing" Namespace=train-ticket

# Step 2: Sleep for 10 minutes
sleep 15m

# Step 3: Run kubectl create
kubectl apply -f ../train-ticket/chaosmesh/chaos1.yaml

sleep 5m

kubectl apply -f ../train-ticket/chaosmesh/chaos2.yaml

sleep 5m

kubectl apply -f ../train-ticket/chaosmesh/chaos3.yaml

sleep 5m

kubectl apply -f ../train-ticket/chaosmesh/chaos4.yaml

sleep 30m

# Step 5: make reset-deploy
make reset-deploy Namespace=train-ticket


# Save and exit the script
echo "Done!"