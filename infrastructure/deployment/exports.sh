#!/bin/bash

# Exported functions
print_header() {
    echo "======== $1 ========"
}

wait_for_resource_group() {
    local resourceGroup=$1
    local timeout=300
    local interval=5
    local start=$(date +%s)
    local end=$((start + timeout))

    echo "Waiting for resources to be created in $resourceGroup"
    while [ $(date +%s) -lt $end ]; do
        echo "Checking if resources are created"
        local resources=$(az resource list --resource-group $resourceGroup --query "[?provisioningState=='Succeeded'].id" -o tsv)
        if [ -n "$resources" ]; then
            echo "Resources created"
            return 0
        fi
        sleep $interval
    done
    echo "Error: Resources not created within $timeout seconds"
    exit 1
}

assign_identity_access() {
    local clusterName=$1
    local sourceRG=$2
    local targetRG=$3
    local role=$4
    local subscriptionId=$5
    local identity=$(az aks show --resource-group $sourceRG --name $clusterName --query identityProfile.kubeletidentity.clientId -o tsv)
    
    echo "Assigning $role role to $identity for /subscriptions/$subscriptionId/resourceGroups/$targetRG"
    az role assignment create --role $role --assignee $identity --scope /subscriptions/$subscriptionId/resourceGroups/$targetRG

    # Export the client id of the identity
    export IDENTITY_CLIENT_ID=$identity
}

# Exported variables
export REGION="eastus"

# exports
export -f print_header
export -f wait_for_resource_group
export -f assign_identity_access