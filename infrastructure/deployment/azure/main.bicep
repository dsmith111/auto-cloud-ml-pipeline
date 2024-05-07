param location string = resourceGroup().location
param standardAgentPoolProfile object
param standardComputePoolProfile object
param airflowResourceGroup string
param aksVersion string
param alias string

@secure()
param storagePassword string

module aksAppModule './aks-app-clusters.bicep' = {
  name: 'aksAppModule'
  params: {
    location: location
    standardAgentPoolProfile: standardAgentPoolProfile
    standardComputePoolProfile: standardComputePoolProfile
    aksVersion: aksVersion
  }
}

module aksPipelineModule './aks-pipeline-resources.bicep' = {
  name: 'aksPipelineModule'
  scope: resourceGroup(airflowResourceGroup)
  params: {
    location: location
    standardAgentPoolProfile: standardAgentPoolProfile
    standardComputePoolProfile: standardComputePoolProfile
    aksVersion: aksVersion
  }
}

module storageModule './storage-resources.bicep' = {
  name: 'storageModule'
  params: {
    location: location
    alias: alias
    storagePassword: storagePassword
  }
}
