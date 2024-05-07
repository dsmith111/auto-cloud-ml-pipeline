#!/bin/bash

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

# Get directory of this bash script
INFRASTRUCTURE_DIRECTORY=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export INFRASTRUCTURE_DIRECTORY

# Bring in exported functions from ./exports.sh
source "$INFRASTRUCTURE_DIRECTORY/exports.sh"
export SUBSCRIPTION_ID=$subscriptionId

# Setup Azure CLI
print_header "Setting up Azure CLI"
# If the subscription passed in is in the response from az account show, then we are already logged in
currentSubscription=$(az account show --query id -o tsv)
if [ "$currentSubscription" != "$subscriptionId" ]; then
    az login
    az account set --subscription $subscriptionId
else
    echo "Already logged in to the correct subscription"
fi

# Deploy azure resources
print_header "Deploying Azure resources"
bash $INFRASTRUCTURE_DIRECTORY/azure/deploy-azure-resources.sh -s $subscriptionId
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "Error: Azure deployment failed"
    exit $exit_code
fi

# Cluster names array
clusters=("spark" "training" "serving" "airflow")

# Get all AKS cluster credentials and deploy resources
for cluster in "${clusters[@]}"
do
    print_header "Assigning identity permissions for $cluster-aks-agentpool"

    if [ "$cluster" == "airflow" ]; then
        assign_identity_access "$cluster-aks" "airflow-rg" "ai-infra-rg" "Storage Blob Data Contributor" $subscriptionId
        assign_identity_access "$cluster-aks" "airflow-rg" "MC_airflow-rg_$cluster-aks_eastus" "Role Based Access Control Administrator" $subscriptionId
    else
        assign_identity_access "$cluster-aks" "ai-infra-rg" "ai-infra-rg" "Storage Blob Data Contributor" $subscriptionId
        assign_identity_access "$cluster-aks" "ai-infra-rg" "MC_ai-infra-rg_$cluster-aks_eastus" "Role Based Access Control Administrator" $subscriptionId
    fi

    print_header "Deploying $cluster-aks resources"
    # Get AKS cluster credentials
    if [ "$cluster" == "airflow" ]; then
        az aks get-credentials --resource-group airflow-rg --name "$cluster-aks"
    else
        az aks get-credentials --resource-group ai-infra-rg --name "$cluster-aks"
    fi

    # Switch context to the current cluster
    kubectl config use-context "$cluster-aks"

    # Deploy pod identities
    bash $INFRASTRUCTURE_DIRECTORY/pod-identity/deploy-pod-identities.sh -t $cluster

    # Deploy cluster-specific resources
    case $cluster in
        "spark")
            bash $INFRASTRUCTURE_DIRECTORY/spark/deploy-spark-resources.sh
            ;;
        "training")
            bash $INFRASTRUCTURE_DIRECTORY/kubeflow/deploy-kubeflow.sh -t $cluster
            ;;
        "serving")
            bash $INFRASTRUCTURE_DIRECTORY/kubeflow/deploy-kubeflow.sh -t $cluster
            ;;
        "airflow")
            bash $INFRASTRUCTURE_DIRECTORY/airflow/deploy-airflow.sh
            ;;
    esac
done

print_header "Infrastructure deployment complete"
echo ""
