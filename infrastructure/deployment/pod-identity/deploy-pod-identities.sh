#!/bin/bash

# Setup
while getopts t: flag
do
    case "${flag}" in
        t) clusterType=${OPTARG};;
    esac
done

if [ -z $clusterType ]; then
    echo "Error: A cluster type is needed. Set with -t (spark, training, airflow, serving)"
    exit 1
elif [[ $clusterType != "serving" ]] && [[ $clusterType != "training" ]] && [[ $clusterType != "spark" ]] && [[ $clusterType != "airflow" ]]; then
    echo "Error: $clusterType is not a valid cluster type. Please select either \"serving\" or \"training\" or \"spark\" or \"airflow\""
    exit 1
fi

POD_IDENTITY_DIRECTORY="$INFRASTRUCTURE_DIRECTORY/pod-identity"
resourceGroup=""
if [ "$clusterType" == "airflow" ]; then
    resourceGroup="airflow-rg"
else
    resourceGroup="ai-infra-rg"
fi

clusterName="$clusterType-aks"

sed "s|{{SUBSCRIPTION_ID}}|$SUBSCRIPTION_ID|g;s|{{RESOURCE_GROUP}}|$resourceGroup|g;s|{{CLUSTER_NAME}}|$clusterType-aks|g;s|{{REGION}}|$REGION|g;s|{{CLIENT_ID}}|$IDENTITY_CLIENT_ID|g" "$POD_IDENTITY_DIRECTORY/azure-identity-pod-patch-template.yaml" > "$POD_IDENTITY_DIRECTORY/$clusterType/azure-identity-pod-patch.yaml"

# Deploy Pod NMIs
helm repo add aad-pod-identity https://raw.githubusercontent.com/Azure/aad-pod-identity/master/charts
helm install aad-pod-identity aad-pod-identity/aad-pod-identity

# Deploy Identities
kubectl apply -k "$POD_IDENTITY_DIRECTORY/$clusterType"