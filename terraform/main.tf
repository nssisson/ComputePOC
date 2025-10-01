locals {
  base_name = "ima-python-sbx"
  tags = {
    Owner       = "BI"
    Workload    = "python"
    Environment = "sbx"
    ManagedBy   = "Terraform"
  }

  registry   = "${module.acr.name}.azurecr.io"
  image_name = "computepoc/computepoc"
  image_tag  = "latest"

  storage_containers = {
    "jobs-logs-small" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    },
    "jobs-logs-medium" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    },
    "jobs-logs-large" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
    "raw" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
    "staging" = {
      role_assignments = {
        "ca_id-BlobContributor" = {
          role_definition_id_or_name = "Storage Blob Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
  }
  storage_shares = {
    "jobs-files-small" = {
      name = "jobs-files-small",
      access_tier = "TransactionOptimized,"
      quota = "1024",
      role_assignments = {
        "ca_id-FilesContributor" = {
          role_definition_id_or_name = "Storage File Data Privleged Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
    "jobs-files-medium" = {
      name = "jobs-files-medium",
      access_tier = "TransactionOptimized,"
      quota = "1024",
      role_assignments = {
        "ca_id-FilesContributor" = {
          role_definition_id_or_name = "Storage File Data Privleged Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
  }

  storage_queues = {
    "jobs-small" = {
      role_assignments = {
        "ca_id-QueueContributor" = {
          role_definition_id_or_name = "Storage Queue Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    },
    "jobs-medium" = {
      role_assignments = {
        "ca_id-QueueContributor" = {
          role_definition_id_or_name = "Storage Queue Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    },
    "jobs-large" = {
      role_assignments = {
        "ca_id-QueueContributor" = {
          role_definition_id_or_name = "Storage Queue Data Contributor"
          principal_id               = module.id.principal_id
        }
      }
    }
  }
  private_endpoints_enabled = [
    "blob",
    "dfs",
    "queue",
    "file"
  ]
}

resource "azurerm_resource_group" "this" {
  name     = "rg-${local.base_name}"
  location = "Central US"
}

module "dls" {
  source           = "Azure/avm-res-storage-storageaccount/azurerm"
  version          = "0.6.1"
  enable_telemetry = false

  name                = replace("st-${local.base_name}", "-", "")
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  shared_access_key_enabled= true

  containers = {
    for container_key, container in local.storage_containers :
    container_key => {
      name             = lookup(container, "name", container_key)
      role_assignments = lookup(container, "role_assignments", {})
      # future options
    }
  }
  queues = {
    for queue_key, queue in local.storage_queues :
    queue_key => {
      name             = lookup(queue, "name", queue_key)
      role_assignments = lookup(queue, "role_assignments", {})
      # future options
    }
  }

  shares = {
    for share_key, share in local.storage_shares :
    share_key => {
      name = lookup(share, "name", share_key)
      access_tier = lookup(share, "access_tier")
      quota = lookup(share, "quota")
    }
  }

  private_endpoints = {
    for endpoint in toset(local.private_endpoints_enabled) :
    endpoint => {
      name                          = "pep-${endpoint}-${local.base_name}"
      network_interface_name        = "nic-pep-${endpoint}-${local.base_name}"
      subnet_resource_id            = module.vnet.subnets["pep"].resource_id
      subresource_name              = endpoint
      private_dns_zone_resource_ids = [module.privatelink.private_dns_zone_resource_ids[endpoint]]
    } if contains(["blob", "dfs", "queue", "file"], endpoint)
  }

  role_assignments = {
    "tf-BlobOwner" = {
      role_definition_id_or_name = "Storage Blob Data Owner"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    "tf-QueueContributor" = {
      role_definition_id_or_name = "Storage Queue Data Contributor"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    "tf-FilesContributor" = {
      role_definition_id_or_name = "Storage File Data Privileged Contributor"
      principal_id               = data.azurerm_client_config.current.object_id
    }
  }

  public_network_access_enabled = true # Temporary
  network_rules = {
    ip_rules = [data.http.current_ip.response_body]
  }
}

module "log_analytics" {
  source           = "Azure/avm-res-operationalinsights-workspace/azurerm"
  version          = "0.4.2"
  enable_telemetry = false

  name                = "log-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  log_analytics_workspace_internet_ingestion_enabled = true
  log_analytics_workspace_internet_query_enabled     = true
}

module "id" {
  source           = "Azure/avm-res-managedidentity-userassignedidentity/azurerm"
  version          = "0.3.3"
  enable_telemetry = false

  name                = "id-${local.base_name}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags
}

module "acr" {
  source           = "Azure/avm-res-containerregistry-registry/azurerm"
  version          = "0.4.0"
  enable_telemetry = false

  name                = replace("acr-${local.base_name}", "-", "")
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  tags                = local.tags

  sku                        = "Basic"
  zone_redundancy_enabled    = false
  retention_policy_in_days   = null
  network_rule_bypass_option = "AzureServices"

  role_assignments = {
    "tf_AcrPush" = {
      role_definition_id_or_name = "AcrPush"
      principal_id               = data.azurerm_client_config.current.object_id
    }
    "id_AcrPull" = {
      role_definition_id_or_name = "AcrPull"
      principal_id               = module.id.principal_id
    }
  }
}


resource "azapi_resource" "cae" {
  type      = "Microsoft.App/managedEnvironments@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "cae-${local.base_name}"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  body = {
    properties = {
      appLogsConfiguration = {
        destination = "azure-monitor"
      }
      infrastructureResourceGroup = "rg-cae-${local.base_name}"
      publicNetworkAccess         = "Disabled"
      vnetConfiguration = {
        infrastructureSubnetId = module.vnet.subnets["aca"].resource_id
        internal               = true
      }

      workloadProfiles = [
        {
          name                = "Consumption",
          workloadProfileType = "Consumption"
        }
        #,
        #{
        #  enableFips          = false
        #  maximumCount        = 5
        #  minimumCount        = 0
        #  name                = "MemoryOptimized"
        #  workloadProfileType = "E8"
        #}
      ],
      zoneRedundant = false
    }
  }
}

resource "azurerm_monitor_diagnostic_setting" "env_diag" {
  name                       = "env-diagnostics-${local.base_name}"
  target_resource_id         = azapi_resource.cae.id
  log_analytics_workspace_id = module.log_analytics.resource_id

  # Logs you can collect
  enabled_log {
    category = "ContainerAppConsoleLogs"

  }
  enabled_log {
    category = "ContainerAppSystemLogs"
  }
  enabled_metric {
    category = "AllMetrics"

  }
}

data "azurerm_storage_account" "storage_key" {
  name                = module.dls.name
  resource_group_name = azurerm_resource_group.this.name
}

resource "azapi_resource" "cae_file_shares" {
  for_each = local.storage_shares
  type = "Microsoft.App/managedEnvironments/storages@2024-10-02-preview"
  name = each.value.name
  parent_id = azapi_resource.cae.id
  body = {
    properties = {
      azureFile = {
        accessMode = "ReadWrite"
        accountKey = data.azurerm_storage_account.storage_key.primary_access_key
        accountName = module.dls.name
        shareName = each.value.name
      }
    }
  }
}

resource "azapi_resource" "caj-small" {               # azurerm_container_app_job doesn't yet support identity in scale > rules
  type      = "Microsoft.App/jobs@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "caj-${local.base_name}-small"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  identity {
    type = "UserAssigned"
    identity_ids = [
      module.id.resource_id
    ]
  }

  body = {
    properties = {
      environmentId       = azapi_resource.cae.id
      workloadProfileName = "Consumption"

      configuration = {
        replicaTimeout    = 18600 # This becomes "replicaTimeoutInSeconds" when bumping to apiVersion @2025-01-01
        replicaRetryLimit = 0

        triggerType = "Event"
        eventTriggerConfig = {
          parallelism            = 1
          replicaCompletionCount = 1
          scale = {
            minExecutions   = 0
            maxExecutions   = 10
            pollingInterval = 30
            rules = [{
              name = "queue"
              type = "azure-queue"
              metadata = {
                accountName = module.dls.name
                queueName   = basename(module.dls.queues["jobs-small"].id)
                queueLength = "1"
              }
              identity = module.id.resource_id
            }]
          }
        }
        registries = [{
          server   = module.acr.resource.login_server
          identity = module.id.resource_id
        }]
        identitySettings = [{
          identity = replace(module.id.resource_id, "resourceGroups", "resourcegroups")
        }]
      }

      template = {
        containers = [{
          name      = "ima-python"
          image     = "${local.registry}/${local.image_name}:${local.image_tag}"
          imageType = "ContainerImage" # This is removed when bumping to apiVersion @2025-01-01
          resources = {
            cpu    = 1
            memory = "2Gi"
          }
          env = [
            {
              name  = "STORAGE_ACCOUNT_NAME"
              value = module.dls.name
            },
            {
              name  = "QUEUE_NAME"
              value = basename(module.dls.queues["jobs-small"].id)
            },
            {
              name  = "AZURE_TENANT_ID"
              value = data.azurerm_client_config.current.tenant_id
            },
            {
              name  = "AZURE_CLIENT_ID"
              value = module.id.client_id
            },
            {
              name  = "LOGGING_CONTAINER_NAME"
              value = basename(module.dls.containers["jobs-logs-small"].id)
            }
          ]
          volumeMounts = [
              {
                mountPath = "/mnt/azurefileshare"
                volumeName = local.storage_shares["jobs-files-small"].name
              }
            ]
        }]
        volumes = [
          {
            name = local.storage_shares["jobs-files-small"].name
            storageName = local.storage_shares["jobs-files-small"].name
            storageType = "AzureFile"
          }
        ]
      }
    }
  }
}


resource "azapi_resource" "caj-medium" {              # azurerm_container_app_job doesn't yet support identity in scale > rules
  type      = "Microsoft.App/jobs@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
  name      = "caj-${local.base_name}-medium"
  parent_id = azurerm_resource_group.this.id
  location  = azurerm_resource_group.this.location
  tags      = local.tags

  identity {
    type = "UserAssigned"
    identity_ids = [
      module.id.resource_id
    ]
  }

  body = {
    properties = {
      environmentId       = azapi_resource.cae.id
      workloadProfileName = "Consumption"

      configuration = {
        replicaTimeout    = 18600 # This becomes "replicaTimeoutInSeconds" when bumping to apiVersion @2025-01-01
        replicaRetryLimit = 0

        triggerType = "Event"
        eventTriggerConfig = {
          parallelism            = 1
          replicaCompletionCount = 1
          scale = {
            minExecutions   = 0
            maxExecutions   = 10
            pollingInterval = 30
            rules = [{
              name = "queue"
              type = "azure-queue"
              metadata = {
                accountName = module.dls.name
                queueName   = basename(module.dls.queues["jobs-medium"].id)
                queueLength = "1"
              }
              identity = module.id.resource_id
            }]
          }
        }
        registries = [{
          server   = module.acr.resource.login_server
          identity = module.id.resource_id
        }]
        identitySettings = [{
          identity = replace(module.id.resource_id, "resourceGroups", "resourcegroups")
        }]
      }

      template = {
        containers = [{
          name      = "ima-python"
          image     = "${local.registry}/${local.image_name}:${local.image_tag}"
          imageType = "ContainerImage" # This is removed when bumping to apiVersion @2025-01-01
          resources = {
            cpu    = 4
            memory = "8Gi"
          }
          env = [
            {
              name  = "STORAGE_ACCOUNT_NAME"
              value = module.dls.name
            },
            {
              name  = "QUEUE_NAME"
              value = basename(module.dls.queues["jobs-medium"].id)
            },
            {
              name  = "AZURE_TENANT_ID"
              value = data.azurerm_client_config.current.tenant_id
            },
            {
              name  = "AZURE_CLIENT_ID"
              value = module.id.client_id
            },
            {
              name  = "LOGGING_CONTAINER_NAME"
              value = basename(module.dls.containers["jobs-logs-medium"].id)
            }
          ]
        }]
      }
    }
  }
}

#resource "azapi_resource" "caj-large" {               # azurerm_container_app_job doesn't yet support identity in scale > rules
#  type      = "Microsoft.App/jobs@2024-10-02-preview" # Latest api version is 2025-01-01; not yet supported by azapi with validation
#  name      = "caj-${local.base_name}-large"
#  parent_id = azurerm_resource_group.this.id
#  location  = azurerm_resource_group.this.location
#  tags      = local.tags
#
#  identity {
#    type = "UserAssigned"
#    identity_ids = [
#      module.id.resource_id
#    ]
#  }
#
#  body = {
#    properties = {
#      environmentId       = azapi_resource.cae.id
#      workloadProfileName = "MemoryOptimized"
#
#      configuration = {
#        replicaTimeout    = 18600 # This becomes "replicaTimeoutInSeconds" when bumping to apiVersion @2025-01-01
#        replicaRetryLimit = 0
#
#        triggerType = "Event"
#        eventTriggerConfig = {
#          parallelism            = 1
#          replicaCompletionCount = 1
#          scale = {
#            minExecutions   = 0
#            maxExecutions   = 10
#            pollingInterval = 30
#            rules = [{
#              name = "queue"
#              type = "azure-queue"
#              metadata = {
#                accountName = module.dls.name
#                queueName   = basename(module.dls.queues["jobs-large"].id)
#                queueLength = "1"
#              }
#              identity = module.id.resource_id
#            }]
#          }
#        }
#        registries = [{
#          server   = module.acr.resource.login_server
#          identity = module.id.resource_id
#        }]
#        identitySettings = [{
#          identity = replace(module.id.resource_id, "resourceGroups", "resourcegroups")
#        }]
#      }
#
#      template = {
#        containers = [{
#          name      = "ima-python"
#          image     = "${local.registry}/${local.image_name}:${local.image_tag}"
#          imageType = "ContainerImage" # This is removed when bumping to apiVersion @2025-01-01
#          resources = {
#            cpu    = 4
#            memory = "32Gi"
#          }
#          env = [
#            {
#              name  = "STORAGE_ACCOUNT_NAME"
#              value = module.dls.name
#            },
#            {
#              name  = "QUEUE_NAME"
#              value = basename(module.dls.queues["jobs-large"].id)
#            },
#            {
#              name  = "AZURE_TENANT_ID"
#              value = data.azurerm_client_config.current.tenant_id
#            },
#            {
#              name  = "AZURE_CLIENT_ID"
#              value = module.id.client_id
#            },
#            {
#              name  = "LOGGING_CONTAINER_NAME"
#              value = basename(module.dls.containers["jobs-logs-large"].id)
#            }
#          ]
#        }]
#      }
#    }
#  }
#}

