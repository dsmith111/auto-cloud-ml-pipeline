#!/bin/bash

# Setup
SPARK_DIRECTORY="$INFRASTRUCTURE_DIRECTORY/spark"

# Deploy Identities
kubectl apply -f "$SPARK_DIRECTORY/"