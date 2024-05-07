param location string
param standardAgentPoolProfile object
param standardComputePoolProfile object
param aksVersion string

var defaultNP = {
  networkPlugin: 'azure'
  serviceCidr: '10.0.0.0/16'
  dnsServiceIP: '10.0.0.10'
  ipFamilies: [
    'IPv4'
  ]
}

resource sparkCluster 'Microsoft.ContainerService/managedClusters@2023-11-01' = {
  name: 'spark-aks'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: aksVersion
    dnsPrefix: 'dnsprefix'
    enableRBAC: true
    networkProfile: defaultNP
    agentPoolProfiles: [
      standardAgentPoolProfile
      standardComputePoolProfile
    ]
  }
}

resource aksTrainingCluster 'Microsoft.ContainerService/managedClusters@2023-11-01' = {
  name: 'training-aks'
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: aksVersion
    dnsPrefix: 'dnsprefix'
    enableRBAC: true
    networkProfile: defaultNP
    agentPoolProfiles: [
      standardAgentPoolProfile
      standardComputePoolProfile
    ]
  }
}

resource aksServingCluster 'Microsoft.ContainerService/managedClusters@2023-11-01' = {
  name: 'serving-aks'
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
