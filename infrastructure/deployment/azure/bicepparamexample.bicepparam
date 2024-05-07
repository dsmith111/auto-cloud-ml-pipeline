using './main.bicep'

var vmSize = 'Standard_B2s'

param standardAgentPoolProfile = {
  name: 'systempool'
  enableAutoScaling: true
  count: 1
  minCount: 1
  maxCount: 4
  vmSize: vmSize
  osType: 'Linux'
  mode: 'System'
}
param standardComputePoolProfile = {
  name: 'computepool'
  enableAutoScaling: true
  count: 0
  minCount: 0
  maxCount: 5
  vmSize: vmSize
  osType: 'Linux'
  mode: 'User'
}
param airflowResourceGroup = 'airflow-rg'
param aksVersion = '1.28.3'
param alias = 'username'
param storagePassword = 'dummypassword1234!'
