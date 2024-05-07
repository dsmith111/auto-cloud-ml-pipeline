param location string
param alias string

@secure()
param storagePassword string

// We want a gen2 data lake storage account
resource storageaccount 'Microsoft.Storage/storageAccounts@2021-02-01' = {
  name: 'maindatalake${alias}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    isHnsEnabled: true
  }
}

resource mainSQLServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: 'mainsqlserver${alias}'
  location: location
  properties: {
    administratorLogin: 'adminlogin'
    administratorLoginPassword: storagePassword
  }
}

resource mainSQLDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: mainSQLServer
  name: 'mainsqldatabase${alias}'
  location: location
  sku: {
    name: 'basic'
    tier: 'basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
  }
}
