param location string
param standardAgentPoolProfile object
param standardComputePoolProfile object
param aksVersion string

resource aksAirflowCluster 'Microsoft.ContainerService/managedClusters@2023-11-01' = {
  name: 'airflow-aks'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: aksVersion
    dnsPrefix: 'dnsprefix'
    enableRBAC: true
    agentPoolProfiles: [
      standardAgentPoolProfile
      standardComputePoolProfile
    ]
  }
}
