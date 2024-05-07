#!/bin/bash

# NOTE REQUIRES AZ CLI 2.53.0 OR HIGHER and BICEP CLI 0.22 OR HIGHER
# Check options
while getopts s: flag
do
    case "${flag}" in
        s) subscriptionId=${OPTARG};;
    esac
done

if [ -z $subscriptionId ]; then
    echo "Error: A subscription id is needed. Set with -s"
    exit 1
fi

# Location of this bash script
AZURE_DIRECTORY="$INFRASTRUCTURE_DIRECTORY/azure"

# Deploy resources
print_header "Creating Resource Groups"
az group create --name "airflow-rg" --location "eastus"
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Azure resource group creation failed"
    exit $exit_code
fi

az group create --name "ai-infra-rg" --location "eastus"
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Azure resource group creation failed"
    exit $exit_code
fi

print_header "Building Azure Infrastructure"

az deployment group create --resource-group "ai-infra-rg" --parameters "$AZURE_DIRECTORY/aks-clusters.bicepparam" --no-wait
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Azure deployment failed"
    exit $exit_code
fi

# Wait for the resources to be created by polling the resource group
print_header "Waiting for resources to be created"
wait_for_resource_group "ai-infra-rg"
wait_for_resource_group "airflow-rg"
