#!/bin/bash

# Setup
while getopts t: flag
do
    case "${flag}" in
        t) clusterType=${OPTARG};;
    esac
done

if [ -z $clusterType ]; then
    echo "Error: A cluster type is needed. Set with -t (training, serving)"
    exit 1
elif [[ $clusterType != "serving" ]] && [[ $clusterType != "training" ]]; then
    echo "Error: $clusterType is not a valid cluster type. Please select either \"serving\" or \"training\""
    exit 1
fi

KUBEFLOW_DIRECTORY="$INFRASTRUCTURE_DIRECTORY/kubeflow"

# Deploy Kubeflow Components
# It fails on the first time, resources are created too fast, so we need to retry
while ! kubectl apply -k "$KUBEFLOW_DIRECTORY/$clusterType"; do
    sleep 5
done